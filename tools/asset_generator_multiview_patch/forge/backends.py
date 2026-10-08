import base64
import json
from pathlib import Path
from typing import Protocol

import httpx

from .config import ROOT


class GenerationBackend(Protocol):
    id: str
    def capabilities(self) -> dict: ...
    def generate(self, reference: Path, output: Path, settings: dict, context) -> Path: ...


class TripoSRBackend:
    id = "triposr"
    python = ROOT / ".backends" / "venv" / "Scripts" / "python.exe"
    runner = ROOT / "backends" / "triposr" / "runner.py"

    def capabilities(self):
        probe = ROOT / "data" / "local_probe.json"
        details = json.loads(probe.read_text(encoding="utf-8")) if probe.exists() else {}
        return {"id":self.id,"label":"TripoSR · local", "primary":True,"installed":self.python.exists(),
                "available":self.python.exists() and bool(details.get("kernel_probe")), "probe":details,
                "single_image":True,"multi_view":False,"textures":True,"pbr":False,"parts":False,"rigging":False,
                "retexture":True,"retexture_scope":"Rebake the base-color field from this model's cached geometry; no new texture prompt", "pose_control":False,"seeds":False,"cost_credits":0,"license":"MIT (code and weights)",
                "limitations":"512 px conditioning; inferred rear surfaces; base color only; no semantic parts or rig",
                "setup":"powershell -ExecutionPolicy Bypass -File scripts/setup_local.ps1"}

    def generate(self, reference, output, settings, context):
        if not self.python.exists():
            raise RuntimeError("Local model is not installed. Run scripts/setup_local.ps1.")
        context.run_process([str(self.python),str(self.runner),"--image",str(reference),"--output",str(output),
                             "--resolution",str(settings.get("mc_resolution",256)),"--texture",str(settings.get("texture_resolution",2048)),
                             "--chunk","4096"], timeout=2400, stage="local_generation")
        result = output/"source.glb"
        if not result.exists():
            raise RuntimeError("Local model produced no GLB. Inspect the job log.")
        return result


class MeshyBackend:
    """Optional contract adapter. Paid requests are disabled in this application."""
    id = "meshy"
    base_url = "https://api.meshy.ai/openapi/v1"

    def capabilities(self):
        return {"id":self.id,"label":"Meshy 7.1 · paid generation disabled", "primary":False, "available":False,
                "single_image":True,"multi_view":False,"textures":True,"pbr":True,"parts":False,"rigging":False,
                "pose_control":True,"retexture":False,"seeds":False,"cost_credits":30,
                "disabled_reason":"Paid generation disabled by your project preference", "license":"Provider terms; output rights depend on plan",
                "docs":"https://docs.meshy.ai/en/api/image-to-3d", "pricing":"https://docs.meshy.ai/en/api/pricing"}

    @staticmethod
    def payload(reference, settings):
        suffix = "jpeg" if reference.suffix.lower() in (".jpg",".jpeg") else "png"
        return {"image_url":f"data:image/{suffix};base64,"+base64.b64encode(reference.read_bytes()).decode(),
                "ai_model":"meshy-7.1","should_texture":True,"enable_pbr":True,"should_remesh":False,
                "image_enhancement":False,"remove_lighting":True,"geometry_resolution":"standard",
                "texture_resolution":f"{settings.get('texture_resolution',4096)//1024}k","target_formats":["glb"]}

    def generate(self, reference, output, settings, context):
        # Keep the disabled boundary inside the adapter as well as in the API.
        # User-supplied keys never enable paid generation implicitly.
        raise RuntimeError("Paid generation is disabled. No Meshy API request was sent.")


class TripoSGBackend:
    id = "triposg"
    python = ROOT / ".backends" / "triposg-venv" / "Scripts" / "python.exe"
    runner = ROOT / "backends" / "triposg" / "runner.py"

    def capabilities(self):
        probe = ROOT / "data" / "triposg_probe.json"
        details = json.loads(probe.read_text(encoding="utf-8")) if probe.exists() else {}
        return {"id":self.id,"label":"TripoSG · local geometry", "primary":False,
                "installed":self.python.exists(),
                "available":self.python.exists() and bool(details.get("generation_passed")),"probe":details,
                "single_image":True,"multi_view":False,"textures":False,"pbr":False,"parts":False,"rigging":False,
                "retexture":False,"pose_control":False,"seeds":True,"cost_credits":0,"license":"MIT (code and weights)",
                "limitations":"Geometry only; materials must be authored separately; single-view inferred hidden surfaces",
                "disabled_reason":"Full local generation compatibility test pending" if not details.get("generation_passed") else "",
                "setup":"powershell -ExecutionPolicy Bypass -File scripts/setup_triposg.ps1"}

    def generate(self, reference, output, settings, context):
        if not self.python.exists():
            raise RuntimeError("Run scripts/setup_triposg.ps1 before using this backend")
        context.run_process([str(self.python),str(self.runner),"--image",str(reference),"--output",str(output),
                             "--seed",str(settings.get("generation_seed",42)),
                             "--steps",str(settings.get("diffusion_steps",50)),
                             "--guidance",str(settings.get("guidance_scale",7.0)),
                             "--depth",str(settings.get("shape_octree_depth",9))],timeout=3600,stage="local_shape_generation")
        result=output/"source.glb"
        if not result.is_file():
            raise RuntimeError("TripoSG produced no mesh; see the retained log and shape checkpoint")
        return result


class TrellisBackend:
    id = 'trellis'
    python = ROOT / '.backends/trellis-venv/Scripts/python.exe'
    runner = ROOT / 'backends/trellis/runner.py'

    def capabilities(self):
        probe = ROOT / 'data/trellis_probe.json'
        details = json.loads(probe.read_text(encoding='utf-8')) if probe.exists() else {}
        available = self.python.exists() and bool(details.get('generation_passed'))
        return {'id':self.id,'label':'TRELLIS · combined views','primary':False,
            'installed':self.python.exists(),'available':available,'probe':details,
            'single_image':True,'multi_view':True,'min_views':2,'max_views':6,
            'textures':False,'vertex_colors':True,'pbr':False,'rigging':False,'parts':False,
            'pose_control':False,'retexture':False,'seeds':True,'cost_credits':0,
            'license':'MIT (code and weights)',
            'conditioning_modes':['multidiffusion','stochastic'],
            'limitations':'Native shared-latent view conditioning; inferred turnarounds need consistency review. Vertex colors only; rigging and PBR authoring remain separate.',
            'disabled_reason':'' if available else 'Full multi-image generation compatibility test pending',
            'setup':'powershell -ExecutionPolicy Bypass -File scripts/setup_trellis.ps1'}

    def _run(self, references, output, settings, context):
        if not self.python.exists():
            raise RuntimeError('Run scripts/setup_trellis.ps1 before using TRELLIS')
        angles=settings.get('reference_view_angles',[])
        angle_args=['--angles',*angles] if angles else []
        from backends.trellis import checkpoint
        identity=checkpoint.signature(references,settings)
        if checkpoint.matches(output,identity):
            context.update(stage='native_mesh_checkpoint',message='Retained native mesh and exact inputs verified; resume color projection')
        else:
            context.run_process([str(self.python),str(self.runner),'--images',*[str(p) for p in references],*angle_args,
                '--output',str(output),'--seed',str(settings.get('generation_seed',42)),
                '--steps',str(settings.get('trellis_steps',25)),
                '--guidance',str(settings.get('trellis_guidance',5.0)),
                '--mode',settings.get('multiview_mode','multidiffusion')],
                timeout=5400,stage='combined_view_generation' if len(references)>1 else 'single_view_generation',cwd=str(ROOT))
            checkpoint.save(output,identity)
        source = output/'source.glb'
        if not source.is_file():
            raise RuntimeError('TRELLIS produced no mesh; inspect the retained inference log')
        if settings.get('project_reference_colors',False) and len([a for a in angles if a!='three_quarter'])>=2:
            from . import config
            request={'source':str(source),'output':str(output/'projected.glb'),
                'report':str(output/'reference_projection.json'),
                'views':[{'angle':a,'mask':str(output/f'foreground_{i:02d}.png')} for i,a in enumerate(angles)]}
            (output/'projection_request.json').write_text(json.dumps(request,indent=2),encoding='utf-8')
            context.run_process([config.BLENDER,'--background','--threads','6','--python-exit-code','1',
                '--python',str(ROOT/'blender/project_reference_colors.py'),'--',str(output/'projection_request.json')],
                timeout=420,stage='reference_color_projection',cwd=str(ROOT))
            source=output/'projected.glb'
            meta=json.loads((output/'generation.json').read_text(encoding='utf-8'))
            meta.update(color_source='Reviewed orthographic references; native colors in uncovered regions',
                projection_report='reference_projection.json',
                projection_seconds=json.loads((output/'reference_projection.json').read_text())['elapsed_seconds'])
            (output/'generation.json').write_text(json.dumps(meta,indent=2),encoding='utf-8')
        return source

    def generate(self, reference, output, settings, context):
        return self._run([reference],output,settings,context)

    def generate_multiview(self, references, output, settings, context):
        if not 2 <= len(references) <= 6:
            raise ValueError('Combined-image generation requires two to six separate views')
        return self._run(references,output,settings,context)


BACKENDS = {b.id:b for b in (TripoSRBackend(),TripoSGBackend(),TrellisBackend(),MeshyBackend())}
