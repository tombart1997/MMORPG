"""Native TRELLIS single/multi-image inference, one mesh, stage CPU offload.

Pinned MIT weights/code. No paid requests and no independent-mesh averaging.
The upstream run_multi_image sampler combines view-conditioned predictions for
one shared sparse structure and one shared structured latent.
"""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT / '.backends/TRELLIS'
MODEL = 'microsoft/TRELLIS-image-large'
REVISION = '25e0d31ffbebe4b5a97464dd851910efc3002d96'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', nargs='+')
    parser.add_argument('--output')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--steps', type=int, default=25)
    parser.add_argument('--guidance', type=float, default=5.0)
    parser.add_argument('--mode', choices=['stochastic', 'multidiffusion'], default='multidiffusion')
    parser.add_argument('--angles', nargs='+')
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--download', action='store_true')
    args = parser.parse_args()
    if not args.check and not args.download and (not args.images or not args.output):
        parser.error('--images and --output required')
    if args.images and not 1 <= len(args.images) <= 6:
        parser.error('One to six separate views supported')
    if args.angles and (len(args.angles)!=len(args.images or []) or any(a not in ['front','left','back','right','top','three_quarter'] for a in args.angles)):
        parser.error('Angles must label every input image exactly once')
    if not 6 <= args.steps <= 50 or not 1 <= args.guidance <= 12:
        parser.error('Steps 6..50 and guidance 1..12 required')
    os.environ.update(ATTN_BACKEND='sdpa', SPARSE_ATTN_BACKEND='sdpa', SPCONV_ALGO='native')
    sys.path[:0] = [str(Path(__file__).parent), str(REPO)]
    from patch_upstream import patch, COMMIT
    patch(REPO)
    import torch
    from huggingface_hub import snapshot_download
    if args.download:
        print(snapshot_download(MODEL, revision=REVISION, allow_patterns=[
            'pipeline.json', 'LICENSE', 'ckpts/ss_dec*', 'ckpts/ss_flow*',
            'ckpts/slat_flow*', 'ckpts/slat_dec_mesh*']), flush=True)
        return
    from trellis import models
    from trellis.pipelines import TrellisImageTo3DPipeline, samplers
    from trellis.modules import sparse as sp
    torch.set_num_threads(6)
    torch.backends.cuda.enable_flash_sdp(False)
    torch.backends.cuda.enable_mem_efficient_sdp(False)
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required for the TRELLIS local backend')
    if args.check:
        import spconv.pytorch as conv
        coords = torch.tensor([[0,0,0,0], [0,1,0,0]], dtype=torch.int32, device='cuda')
        data = conv.SparseConvTensor(torch.randn(2,8,device='cuda'), coords, [4,4,4], 1)
        out = conv.SubMConv3d(8,8,3,algo=conv.ConvAlgo.Native).cuda()(data)
        torch.cuda.synchronize()
        print(json.dumps({'cuda':torch.cuda.get_device_name(), 'sparse_convolution_passed':bool(torch.isfinite(out.features).all()),
                          'generation_passed':False, 'code_commit':COMMIT, 'model_revision':REVISION}), flush=True)
        return
    import numpy as np
    from PIL import Image
    import trimesh
    from safetensors.torch import load_file
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    torch.cuda.reset_peak_memory_stats()
    weights = Path(snapshot_download(MODEL, revision=REVISION, allow_patterns=[
        'pipeline.json', 'LICENSE', 'ckpts/ss_dec*', 'ckpts/ss_flow*',
        'ckpts/slat_flow*', 'ckpts/slat_dec_mesh*']))
    cfg = json.loads((weights/'pipeline.json').read_text())['args']

    # Load just one model per stage, release it after use. No simultaneous 5-model
    # GPU/RAM residency, no dependency on unused Gaussian/radiance rasterizers.
    class OffloadedPipeline(TrellisImageTo3DPipeline):
        @property
        def device(self):
            return torch.device('cuda')

        def load_stage(self, name):
            for previous in list(self.models):
                self.models.pop(previous).cpu()
            gc.collect()
            torch.cuda.empty_cache()
            stem = weights / cfg['models'][name]
            spec = json.loads(stem.with_suffix('.json').read_text())
            module = getattr(models, spec['name'])(**spec['args'])
            module.load_state_dict(load_file(str(stem.with_suffix('.safetensors'))))
            self.models[name] = module.eval().cuda()
            print('Stage ' + name, flush=True)
            return module

        def encode_image(self, images):
            self._init_image_cond_model(cfg['image_cond_model'])
            self.models['image_cond_model'].cuda()
            # DINO float32, sequential views to bound attention memory.
            result = torch.cat([super(OffloadedPipeline, self).encode_image([im]) for im in images])
            self.models.pop('image_cond_model').cpu()
            gc.collect()
            torch.cuda.empty_cache()
            return result

        def sample_sparse_structure(self, cond, num_samples=1, sampler_params=None):
            flow = self.load_stage('sparse_structure_flow_model')
            noise = torch.randn(num_samples, flow.in_channels, flow.resolution, flow.resolution, flow.resolution, device='cuda')
            params = {**self.sparse_structure_sampler_params, **(sampler_params or {})}
            z = self.sparse_structure_sampler.sample(flow, noise, **cond, **params, verbose=True).samples
            del flow, noise
            decoder = self.load_stage('sparse_structure_decoder')
            coords = torch.argwhere(decoder(z)>0)[:, [0,2,3,4]].int()
            del z, decoder
            if not len(coords):
                raise RuntimeError('No occupied voxels; inspect masked input views')
            print('Occupied voxels: ' + str(len(coords)), flush=True)
            return coords

        def sample_slat(self, cond, coords, sampler_params=None):
            self.load_stage('slat_flow_model')
            return super().sample_slat(cond, coords, sampler_params or {})

        def decode_slat(self, slat, formats=None):
            torch.save({'feats':slat.feats.cpu(), 'coords':slat.coords.cpu()}, outdir/'structured_latent.pt')
            self.load_stage('slat_decoder_mesh')
            return super().decode_slat(slat, ['mesh'])

    pipe = OffloadedPipeline()
    pipe.models = {}
    for stage in ('sparse_structure', 'slat'):
        spec = cfg[stage+'_sampler']
        setattr(pipe, stage+'_sampler', getattr(samplers,spec['name'])(**spec['args']))
        setattr(pipe, stage+'_sampler_params', spec['params'])
    pipe.slat_normalization = cfg['slat_normalization']
    pipe.rembg_session = None
    images = [Image.open(path).convert('RGBA') for path in args.images]
    prepared = []
    preprocessing = []
    from foreground import studio_foreground
    for index, im in enumerate(images):
        masked,mask_method=studio_foreground(im)
        if masked is not None:
            im=masked
        else:
            import rembg
            if pipe.rembg_session is None:
                pipe.rembg_session=rembg.new_session('u2net')
            im=rembg.remove(im,session=pipe.rembg_session)
        im.save(outdir/f'foreground_{index:02d}.png')
        preprocessing.append({'angle':(args.angles or ['unknown']*len(images))[index],
            'mask_method':mask_method,'foreground_sha256':sha(outdir/f'foreground_{index:02d}.png')})
        im = pipe.preprocess_image(im)
        im.save(outdir/f'conditioning_{index:02d}.png')
        prepared.append(im)
    pipe.rembg_session = None
    gc.collect()
    params = {'steps':args.steps, 'cfg_strength':args.guidance}
    if len(prepared) > 1:
        result = pipe.run_multi_image(prepared, seed=args.seed,
            sparse_structure_sampler_params=params, slat_sampler_params=params,
            formats=['mesh'], preprocess_image=False, mode=args.mode)
    else:
        result = pipe.run(prepared[0], seed=args.seed,
            sparse_structure_sampler_params=params, slat_sampler_params=params,
            formats=['mesh'], preprocess_image=False)
    mesh = result['mesh'][0]
    vertices = mesh.vertices.detach().cpu().numpy()
    faces = mesh.faces.detach().cpu().numpy()
    colors = (mesh.vertex_attrs[:, :3].detach().cpu().numpy().clip(0,1)*255).astype(np.uint8) if mesh.vertex_attrs is not None else None
    shape = trimesh.Trimesh(vertices, faces, vertex_colors=colors, process=False)
    # TRELLIS Z-up => glTF/Godot Y-up. Keep geometry under the same transform.
    shape.apply_transform(trimesh.transformations.rotation_matrix(-np.pi/2,[1,0,0]))
    shape.apply_transform(trimesh.transformations.rotation_matrix(np.pi,[0,1,0]))
    from export_glb import export_mesh
    export_mesh(shape,outdir/'source.glb')
    np.savez_compressed(outdir/'geometry.npz',vertices=vertices,faces=faces,colors=colors)
    elapsed = round(time.monotonic()-started,2)
    metadata = {'model':MODEL,'model_revision':REVISION,'code_commit':COMMIT,'backend':'trellis',
        'multi_image':len(prepared)>1,'conditioning_method':'native_'+args.mode if len(prepared)>1 else 'single_image',
        'image_count':len(prepared),'inputs':[{'path':str(Path(p).resolve()),'sha256':sha(p)} for p in args.images],
        'view_angles':args.angles or [],'preprocessing':preprocessing,
        'seed':args.seed,'steps':args.steps,'cfg_strength':args.guidance,'triangles':len(faces),
        'color_source':'native vertex colors','materials':'base color only; PBR surfaces need authoring',
        'elapsed_seconds':elapsed,'peak_cuda_mb':round(torch.cuda.max_memory_allocated()/2**20,1),
        'cost_credits':0,'license':'MIT code and weights','cpu_offload':'one stage at a time',
        'upstream_port':'exact chunked SDPA, native spconv, unchanged native multi-image sampler',
        'review_status':'pending','unseen_surfaces':'Generated reference views are inferred; inspect geometry and silhouette.'}
    (outdir/'generation.json').write_text(json.dumps(metadata,indent=2),encoding='utf-8')
    print(json.dumps(metadata),flush=True)


if __name__ == '__main__':
    main()
