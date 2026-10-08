"""Audit and publish the final catalogue without granting visual approval."""
import hashlib
import html
import json
import struct
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DOC=ROOT/'docs/full_asset_rebuild'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def gltf(path):
    data=path.read_bytes()
    if data[:4]!=b'glTF' or struct.unpack_from('<I',data,4)[0]!=2:
        raise ValueError('Expected glTF 2 GLB: '+str(path))
    length=struct.unpack_from('<I',data,12)[0]
    return json.loads(data[20:20+length])

def main():
    sources=read(ROOT/'blender/multiview_rebuild/export_manifest.json')['models']
    lineage={r['path']:r for r in read(DOC/'variant_lineage.json')}
    references={r['key']:r for r in read(ROOT/'concepts_docs/art/asset_turnarounds_v2/catalog.json')['assets']}
    review_path=DOC/'visual_review.json'
    reviews={r['path']:r for r in read(review_path)['models']} if review_path.exists() else {}
    records=[];cards=[]
    for export in sources:
        key=export['key'];target=ROOT/export['target'];source=ROOT/export['source']
        group=target.parent.name if target.parent.name!='generated' else 'hero_mount'
        info=lineage.get(export['target'],{})
        base=info.get('base','jade' if group=='weapons' else 'warrior' if key in ['traveler_guard','jade_ironback_mantle','warden_insignia'] else key)
        ref=references.get(base)
        reference=Path(ref['sheet'].replace('\\','/')) if ref else Path('concepts_docs/art/world_briarwood.png')
        image=DOC/'evidence'/f'{key}_runtime.png'
        animation=DOC/'evidence'/f'{key}_runtime_animation.png'
        for required in [target,source,ROOT/reference,image]:
            if not required.is_file():raise ValueError('Missing catalogue evidence/source: '+str(required))
        scene=gltf(target)
        triangles=sum(scene['accessors'][p.get('indices',p['attributes']['POSITION'])]['count']//3
            for mesh in scene.get('meshes',[]) for p in mesh['primitives'] if p.get('mode',4)==4)
        digest=sha(target);review=reviews.get(export['target'],{})
        animation_digest=sha(animation) if animation.exists() else None
        valid_review=(review.get('sha256')==digest and review.get('render_sha256')==sha(image)
            and review.get('animation_render_sha256')==animation_digest)
        record={**export,'group':group,'base':base,'sha256':digest,'source_sha256':sha(source),'triangles':triangles,
            'bytes':target.stat().st_size,'materials':len(scene.get('materials',[])),
            'bones':[len(skin['joints']) for skin in scene.get('skins',[])],
            'clips':[clip.get('name','') for clip in scene.get('animations',[])],
            'reference':reference.as_posix(),'input_angles':[v['angle'] for v in ref['views'] if v['used']] if ref else [],
            'method':info.get('method','New reconstructed body with fitted skin/tack, or clean concept-derived equipment; see repair report.'),
            'old_geometry_reused':False,'visual_status':review.get('status','requires_opened_review') if valid_review else 'requires_opened_review',
            'render':image.relative_to(ROOT).as_posix(),'render_sha256':sha(image),
            'animation_render':animation.relative_to(ROOT).as_posix() if animation.exists() else None,
            'animation_render_sha256':animation_digest}
        records.append(record)
        links=[('Full Godot sheet',f'evidence/{key}_runtime.png'),('Editable source','../../'+export['source']),
               ('Runtime GLB','../../'+export['target']),('Reference','../../'+reference.as_posix())]
        if animation.exists():links.insert(1,('All clip samples',f'evidence/{key}_runtime_animation.png'))
        link_html=' · '.join(f'<a href="{html.escape(url)}">{html.escape(label)}</a>' for label,url in links)
        cards.append(f'<article data-group="{group}" data-name="{key}"><h2>{html.escape(key.replace("_"," ").title())}</h2>'
            f'<p class="meta">{group} · {triangles:,} triangles · {record["materials"]} materials · {record["visual_status"]}</p>'
            f'<a class="angles" href="evidence/{key}_runtime.png"><img src="evidence/{key}_runtime.png" alt="{key}: Godot front, side, back and three-quarter views" loading="lazy"></a>'
            f'<p>{html.escape(record["method"])}</p><p>{link_html}</p><details><summary>Source and hash</summary><p>Shared base: {base}. '
            f'Inputs: {", ".join(record["input_angles"]) or "broader concept authority"}. Rig joints: {record["bones"]}. '
            f'Clips: {html.escape(", ".join(record["clips"])) or "static"}.</p><code>{digest}</code></details></article>')
    actual={p.relative_to(ROOT).as_posix() for p in (ROOT/'game/assets/generated').rglob('*.glb')}
    if actual!={r['target'] for r in records}:raise ValueError('Runtime and editable catalogues differ')
    (DOC/'catalogue.json').write_text(json.dumps({'schema':1,'models':records},indent=2),encoding='utf-8')
    groups=sorted({r['group'] for r in records})
    options='<option value="">Every group</option>'+''.join(f'<option>{g}</option>' for g in groups)
    page='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ironfield · Complete asset rebuild</title>
<style>body{margin:0;background:#152025;color:#e2e9e8;font:16px/1.6 system-ui}main{max-width:1440px;margin:auto;padding:28px}a{color:#bce0ad}h1,h2{line-height:1.2}.intro{max-width:940px}.controls{display:flex;flex-wrap:wrap;gap:18px;margin:28px 0}select,input{font:inherit;padding:10px;background:#24363c;color:white;border:1px solid #5a7075;border-radius:5px}.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:22px}article{padding:18px;background:#1c2b31;border:1px solid #4a6068;border-radius:7px}.meta{font-size:13px;color:#b8c8ce}.angles{display:block;aspect-ratio:4;overflow:hidden;background:#515d66}.angles img{display:block;width:100%;height:auto}code{overflow-wrap:anywhere;font-size:12px}details{font-size:14px}[hidden]{display:none!important}@media(max-width:850px){.grid{grid-template-columns:1fr}main{padding:16px}input,select{max-width:100%}}</style></head><body><main>
<h1>All 111 replacement models</h1><p class="intro">Actual Godot imports, opened at front, side, back and three-quarter angles. Open a full sheet for clay, wireframe, details, reference comparison and gameplay-distance views. Rigged models include every exported clip sampled at four points. Thin weapons, coins and ground litter are rotated only on the inspection stage so their surfaces can be seen.</p>
<p class="intro">Shared bases and clean remodeling are recorded for every export. Numerical import checks and image generation do not grant visual approval. The review record is tied to both the model and rendered-image hashes.</p>
<p><a href="README.md">Pipeline, repairs and performance</a> · <a href="catalogue.json">Full catalogue</a> · <a href="gameplay_checks.json">Gameplay checks</a> · <a href="../../concepts_docs/art/asset_turnarounds_v2/index.html">30 practical reference sheets</a> · <a href="../screenshots/horse-reference/godot/final_multiview/final_contact.png">Horse, rider and mounted fit</a></p>
<div class="controls"><label>Group <select id="group">'''+options+'''</select></label><label>Find a model <input id="search" type="search" placeholder="Name"></label><span id="count" aria-live="polite"></span></div><section class="grid">'''+''.join(cards)+'''</section>
<script>const cards=[...document.querySelectorAll('article')],group=document.querySelector('#group'),search=document.querySelector('#search');function filter(){let n=0;for(const c of cards){c.hidden=(group.value&&c.dataset.group!==group.value)||!c.dataset.name.includes(search.value.toLowerCase().replaceAll(' ','_'));if(!c.hidden)n++}document.querySelector('#count').textContent=n+' models'}group.addEventListener('change',filter);search.addEventListener('input',filter);filter();</script></main></body></html>'''
    (DOC/'gallery.html').write_text(page,encoding='utf-8')
    print('CATALOGUE',len(records),'models;',sum(r['visual_status']!='requires_opened_review' for r in records),'hash-matched opened reviews')

if __name__=='__main__':main()
