"""Build an offline reference browser from the imported, inspected input catalog."""
import html
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'concepts_docs/art/asset_turnarounds_v2'
catalog=json.loads((ART/'catalog.json').read_text(encoding='utf-8'))
cards=[]
for asset in catalog['assets']:
    key=asset['key'];views=[]
    for view in asset['views']:
        angle=view['angle'];used=view['used']
        views.append(f'<a class="view {"used" if used else "omitted"}" href="{key}/{angle}.png"><img src="{key}/{angle}.png" alt="{angle} view" loading="lazy"><span>{angle.replace("_"," ")} · {"INPUT" if used else "SUPPLEMENTARY"}</span></a>')
    exclusions=''.join(f'<li><b>{html.escape(angle)}:</b> {html.escape(reason)}</li>' for angle,reason in asset.get('excluded_views',{}).items())
    cards.append(f'''<article id="{key}"><div class="card-heading"><h2>{html.escape(asset['name'])}</h2><a href="http://127.0.0.1:8743/?asset={asset['forge_asset_id']}">Open in Forge ↗</a></div>
      <a href="{key}/turnaround.png"><img class="sheet" src="{key}/turnaround.png" alt="{html.escape(asset['name'])} production turnaround" loading="lazy"></a>
      <div class="views">{''.join(views)}</div><p>{html.escape(asset['review_notes'])}</p>{'<ul>'+exclusions+'</ul>' if exclusions else ''}
      <details><summary>Provenance and input contract</summary><p>Concept asset {asset['source_asset_id']}; reviewed set {asset['reference_set_id']}. Generated hidden surfaces are inferred. Input review does not accept a generated mesh.</p><a href="{key}/prompt.txt">Exact generation prompt</a><p>Sheet SHA-256: <code>{asset['sheet_sha256']}</code></p></details></article>''')
page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ironfield · Production reference views</title>
<style>body{margin:0;background:#11181b;color:#e3e8e7;font:16px/1.6 system-ui}main{max-width:1200px;margin:auto;padding:32px}a{color:#c2dca7}h1,h2{line-height:1.2}.intro{max-width:850px;color:#b6c2c2}nav{display:flex;flex-wrap:wrap;gap:16px;margin:24px 0}article{padding:24px;margin:32px 0;border:1px solid #3c4b4c;border-radius:10px;background:#182225}.sheet{width:100%;max-height:650px;object-fit:contain;background:#fff}.card-heading{display:flex;justify-content:space-between;align-items:center;gap:20px}.views{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin-top:16px}.view img{width:100%;height:170px;object-fit:contain;background:#eee}.view span{display:block;font-size:12px}.omitted{opacity:.65}code{overflow-wrap:anywhere}details{font-size:14px;color:#b6c2c2}footer{margin:40px 0;color:#b6c2c2}</style>
<main><h1>Production reference views</h1><p class="intro">'''+str(len(catalog['assets']))+''' practical interpretations of the game concept art, opened and inspected during the full asset rebuild. These images isolate each asset in a neutral pose, describe its main angles and separate horse, rider, tools and equipment. Click a sheet or individual angle to inspect it at full resolution. Only panels marked INPUT condition the shared 3D reconstruction.</p>
<p class="intro">Horse markings and blacksmith angle labels were corrected after inspection. Redundant fern angles and an inconsistent tower rear were excluded. Opposite surfaces are design interpretations, not photographs or measured geometry.</p>
<nav>'''+''.join(f'<a href="#{a["key"]}">{html.escape(a["name"])}</a>' for a in catalog['assets'])+'''</nav>'''+''.join(cards)+'''<footer><a href="catalog.json">Exact input hashes and review notes</a> · <a href="../../../docs/full_asset_rebuild/README.md">Generator changes and actual Godot results</a><p>Forge must be running for its links. The gallery and images also work offline. Backend: native TRELLIS combined-image conditioning; inference and visual acceptance remain separate steps.</p></footer></main></html>'''
(ART/'index.html').write_text(page,encoding='utf-8')
print('Built',len(cards),'reference sheets')
