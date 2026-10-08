"""Small, audited Windows/Pascal port. Does not change the multi-image sampler.

Patch only the pinned checkout; keep an unmodified .forge-original copy of every
file. Native sparse windows/coordinates and all trained weights are preserved.
"""
from pathlib import Path
import shutil
import subprocess

COMMIT = '442aa1e1afb9014e80681d3bf604e8d728a86ee7'
DINO_COMMIT = '7764ea0f912e53c92e82eb78a2a1631e92725fc8'


def patch(root):
    root = Path(root)
    actual = subprocess.check_output(['git', '-C', str(root), 'rev-parse', 'HEAD'], text=True).strip()
    if actual != COMMIT:
        raise RuntimeError('TRELLIS checkout differs from audited revision: ' + actual)

    def edit(relative, pairs):
        path = root / relative
        original = path.with_name(path.name + '.forge-original')
        if not original.exists():
            shutil.copy2(path, original)
        text = original.read_text(encoding='utf-8')
        for before, after in pairs:
            if before not in text:
                raise RuntimeError('Upstream patch anchor missing: ' + relative)
            text = text.replace(before, after)
        path.write_text(text, encoding='utf-8')

    edit('trellis/modules/sparse/__init__.py', [
        ("env_sparse_attn in ['xformers', 'flash_attn']", "env_sparse_attn in ['xformers', 'flash_attn', 'sdpa']")])
    for name in ('full_attn', 'windowed_attn', 'serialized_attn'):
        pairs = [("elif ATTN == 'flash_attn':\n    import flash_attn",
                  "elif ATTN == 'flash_attn':\n    import flash_attn\nelif ATTN == 'sdpa':\n    from sdpa import dense_attention, packed_attention")]
        if name == 'full_attn':
            pairs.append(("    if ATTN == 'xformers':\n        if num_all_args == 1:",
                          "    if ATTN == 'sdpa':\n        if num_all_args == 1:\n            q, k, v = qkv.unbind(dim=1)\n        elif num_all_args == 2:\n            k, v = kv.unbind(dim=1)\n        out = packed_attention(q, k, v, q_seqlen, kv_seqlen)\n    elif ATTN == 'xformers':\n        if num_all_args == 1:"))
        else:
            if name in ('serialized_attn', 'windowed_attn'):
                pairs.append(("        if ATTN == 'xformers':\n            q, k, v = qkv_feats.unbind(dim=2)",
                              "        if ATTN == 'sdpa':\n            q, k, v = qkv_feats.unbind(dim=2)\n            out = dense_attention(q, k, v)\n        elif ATTN == 'xformers':\n            q, k, v = qkv_feats.unbind(dim=2)"))
                needle = "        if ATTN == 'xformers':\n            q, k, v = qkv_feats.unbind(dim=1)"
            indent = '        '
            pairs.append((needle, indent + "if ATTN == 'sdpa':\n" + indent + "    q, k, v = qkv_feats.unbind(dim=1)\n" + indent + "    out = packed_attention(q, k, v, seq_lens, seq_lens)\n" + indent + "elif ATTN == 'xformers':\n" + indent + "    q, k, v = qkv_feats.unbind(dim=1)"))
        edit('trellis/modules/sparse/attention/' + name + '.py', pairs)
    # Dense flow attention needs the same bounded-memory exact SDPA implementation.
    edit('trellis/modules/attention/full_attn.py', [
        ('from torch.nn.functional import scaled_dot_product_attention as sdpa', 'from sdpa import dense_attention'),
        ("        out = sdpa(q, k, v)         # [N, H, L, C]", "        out = dense_attention(q.transpose(1, 2), k.transpose(1, 2), v.transpose(1, 2)).transpose(1, 2)")])
    edit('trellis/pipelines/__init__.py', [
        ('from .trellis_text_to_3d import TrellisTextTo3DPipeline', '# Text pipeline dependencies are loaded only when requested.'),
        ("    return globals()[config['name']].from_pretrained(path)",
         "    if config['name'] == 'TrellisTextTo3DPipeline':\n        from .trellis_text_to_3d import TrellisTextTo3DPipeline\n        return TrellisTextTo3DPipeline.from_pretrained(path)\n    return globals()[config['name']].from_pretrained(path)")])
    edit('trellis/pipelines/trellis_image_to_3d.py', [
        ("torch.hub.load('facebookresearch/dinov2', name, pretrained=True)",
         "torch.hub.load('facebookresearch/dinov2:" + DINO_COMMIT + "', name, pretrained=True, skip_validation=True, trust_repo=True)")])
    edit('trellis/representations/mesh/flexicubes/flexicubes.py', [
        ('from kaolin.utils.testing import check_tensor','from tensor_checks import check_tensor')])


if __name__ == '__main__':
    import sys
    patch(sys.argv[1])
