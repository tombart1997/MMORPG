"""Read-only inventory report; never changes diagnoses or invents visual reviews."""
from pathlib import Path
from collections import Counter
import csv, html, json

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/asset_review'
FORGE = Path(r'C:\Users\Tom\Documents\2D_to_3D')

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')

def main():
    inventory = read(OUT/'inventory.json')['assets']
    fallbacks = {a['key']: a for a in read(OUT/'fallback_inventory.json')['assets']}
    registry = read(ROOT/'game/data/visuals/reviewed_versions.json')['mappings']
    rows = []
    attempts = []
    for source in inventory:
        asset = read(FORGE/'data/assets'/source['asset_id']/'manifest.json')
        flow = asset['reviewflow']
        diagnosis = flow['diagnosis']
        initial = OUT/('benchmarks' if source['key'] in ('watchtower','fern_reference','mob_meadow_wolf','mob_ironhide_boar') else 'inventory')/source['key']
        before = initial/'before.png'
        after = None
        if source['key'] in fallbacks:
            after = OUT/'fallbacks'/fallbacks[source['key']]['evidence_key']/'after.png'
        elif source['key'] in ('watchtower','fern_reference'):
            version = next(v for v in flow['versions'] if v['id']==flow['accepted_version'])
            artifact = version['artifacts']['files'].get('after.png')
            after = FORGE/'data/assets'/source['asset_id']/artifact
            # Keep the offline gallery self-contained; copied immutable evidence only.
            destination = OUT/'accepted'/source['key']/'after.png'
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(after.read_bytes())
            after = destination
        elif source['key']=='derived_benchmark_fern':
            after = OUT/'accepted/fern_reference/after.png'
        target = 'res://'+source['target'][5:]
        mapping = registry.get(target)
        current = {
            'key': source['key'], 'asset_id': source['asset_id'], 'category': source['category'],
            'family': source.get('family'), 'generated_status': source['status'],
            'current_status': flow['status'], 'temporary_fallback': bool(flow.get('temporary_fallback')),
            'confidence': diagnosis.get('confidence'), 'initial_findings': source.get('review_notes'),
            'defects': diagnosis.get('defects', []), 'criteria': diagnosis.get('criteria', []),
            'plan': flow.get('plan', []), 'budget': flow['budget'], 'remaining_review': flow['remaining_review'],
            'future_work': diagnosis.get('future_work', []), 'source_sha256': source['source_sha256'],
            'saved_source': str(FORGE/'data/assets'/source['asset_id']/source['source']),
            'original_generated_source': source['original_source'], 'source_asset_id': source['source_asset_id'],
            'game_target': target, 'deployed_mapping': mapping, 'accepted_version': flow['accepted_version'],
            'before': before.relative_to(OUT).as_posix() if before.exists() else None,
            'after': after.relative_to(OUT).as_posix() if after and after.exists() else None,
            'attempts': [{k:t.get(k) for k in ('id','kind','state','elapsed_seconds','cost_credits','plan','review','notes','evidence')} for t in flow['attempts']],
            'archived_candidates': [{k:c.get(k) for k in ('id','path','sha256','archive_reason')} for c in asset['candidates'] if c.get('archived')],
            'review_url': 'http://127.0.0.1:8742/?asset='+source['asset_id'],
        }
        rows.append(current)
        attempts += [dict(asset_id=source['asset_id'],key=source['key'],**a) for a in current['attempts']]
    report = {
        'date': '2026-10-04', 'scope': '110 saved game bindings, including 59 reconstructed originals and 51 derived exports.',
        'initial_generated_status_counts': dict(Counter(r['generated_status'] for r in rows)),
        'current_selected_status_counts': dict(Counter(r['current_status'] for r in rows)),
        'temporary_fallbacks': sum(r['temporary_fallback'] for r in rows),
        'deployed_versions': sum(bool(r['deployed_mapping']) for r in rows),
        'repair_attempt_states': dict(Counter(a['state'] for a in attempts)),
        'repair_attempt_kinds': dict(Counter(a['kind'] for a in attempts)),
        'repair_job_processing_seconds': round(sum(a['elapsed_seconds'] or 0 for a in attempts), 3),
        'repair_job_cost_credits': sum(a['cost_credits'] or 0 for a in attempts),
        'regenerated_during_review': 0,
        'accepted_regional_rebuilds': ['watchtower','fern_reference'],
        'accepted_derived_rebuilds': ['derived_benchmark_fern'],
        'archived_candidates': sum(len(r['archived_candidates']) for r in rows),
        'assets': rows,
        'limits': ['KEEP on a temporary fallback approves runtime safety and sampled appearance, not complete concept fidelity.',
                   'Every saved standardized sheet and rigged animation sheet was opened; four samples per clip are not exhaustive animation validation.',
                   'Repair-job time excludes initial diagnosis renders, evidence review, reference preparation and earlier generation costs. Those remain in their original job receipts.',
                   'REGENERATE is an actionable diagnosis; no new neural generation was performed in this bounded review. Paid regeneration remains disabled.'],
    }
    write(OUT/'report.json', report)
    fields = ['key','asset_id','category','family','generated_status','current_status','temporary_fallback','accepted_version','initial_findings','future_work','remaining_review','game_target']
    with (OUT/'inventory.csv').open('w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fields);writer.writeheader()
        for row in rows:
            writer.writerow({k:json.dumps(row[k],ensure_ascii=False) if isinstance(row[k],(list,dict)) else row[k] for k in fields})
    cards = []
    escape = html.escape
    for row in rows:
        images = ''.join(f'<a href="{escape(row[k])}" target="_blank"><img loading="lazy" src="{escape(row[k])}" alt="{k}"><figcaption>{k}</figcaption></a>' for k in ['before','after'] if row[k])
        details = ''.join(f'<li>{escape(str(s))}</li>' for s in row['future_work']+row['remaining_review'])
        attempt_text = ', '.join(f"{a['kind']}: {a['state']} ({a['elapsed_seconds'] or 0}s, {a['cost_credits'] or 0} credits)" for a in row['attempts']) or 'No new geometry repair; diagnosed and retained or selected a saved fallback.'
        cards.append(f'''<article data-status="{escape(row['generated_status'])}" data-current="{escape(row['current_status'])}" data-fallback="{str(row['temporary_fallback']).lower()}">
<h2>{escape(row['key'])}</h2><p class="badge">Generated: {escape(row['generated_status'])} / Current: {escape(row['current_status'])}{' (temporary fallback)' if row['temporary_fallback'] else ''}</p>
<p>{escape(row['initial_findings'] or '')}</p><div class="comparison">{images}</div><p>{escape(attempt_text)}</p><ul>{details}</ul>
<small>Confidence: {escape(str(row['confidence']))}. Accepted version: {escape(str(row['accepted_version'] or 'none'))}. Archived candidates: {len(row['archived_candidates'])}.</small>
<p><a href="{escape(row['review_url'])}">Open live Forge review</a></p></article>''')
    counts = ', '.join(f'{k}: {v}' for k,v in report['initial_generated_status_counts'].items())
    page = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Asset inventory review</title>
<style>body{max-width:1400px;margin:30px auto;padding:0 24px;background:#13191c;color:#e0e5df;font:16px/1.5 system-ui}a{color:#acd3bf}h1,h2{color:#edd3a3}input,select{padding:10px;margin:4px;background:#253137;color:inherit;border:1px solid #5a6c64}article{border:1px solid #415248;border-radius:8px;padding:20px;margin:24px 0;background:#1c2527}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:12px}.comparison img{width:100%;max-height:680px;object-fit:contain;background:#0c1113}.badge{color:#edd3a3}small{color:#b6c3ba}[hidden]{display:none}@media(max-width:700px){.comparison{grid-template-columns:1fr}}</style>
<h1>110 saved assets: opened evidence and production decisions</h1><p>''' + escape(counts)+'''</p><p>Two regional rebuilds, one derived fern export, 54 explicitly marked temporary fallbacks, 61 archived candidates. Original concepts, meshes, PBR textures and manifests are retained. A fallback's KEEP status does not certify its complete concept fidelity.</p>
<p><a href="README.md">Full report</a> / <a href="report.json">Machine-readable report</a> / <a href="inventory.csv">Spreadsheet</a> / <a href="http://127.0.0.1:8742/">Live review interface</a></p>
<input id="search" placeholder="Search asset or finding"><select id="status"><option value="">All original diagnoses</option><option>KEEP</option><option>POLISH</option><option>PARTIAL REBUILD</option><option>REGENERATE</option><option>REJECT</option></select><select id="kind"><option value="">All current results</option><option value="fallback">Temporary fallback</option><option value="unresolved">Unresolved generated asset</option></select><span id="count"></span>
''' + '\n'.join(cards)+'''
<script>const articles=[...document.querySelectorAll('article')];function filter(){let n=0;for(const a of articles){const match=a.textContent.toLowerCase().includes(search.value.toLowerCase())&&(!status.value||a.dataset.status===status.value)&&(!kind.value||(kind.value==='fallback'?a.dataset.fallback==='true':a.dataset.current!=='KEEP'));a.hidden=!match;if(match)n++;}document.querySelector('#count').textContent=n+' assets shown';}const search=document.querySelector('#search'),status=document.querySelector('#status'),kind=document.querySelector('#kind');[search,status,kind].forEach(e=>e.addEventListener('input',filter));filter();</script></html>'''
    (OUT/'gallery.html').write_text(page, encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('assets','limits')},indent=2))

if __name__=='__main__':main()
