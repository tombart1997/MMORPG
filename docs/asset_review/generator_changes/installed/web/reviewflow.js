// Diagnosis and repair evidence remain distinct from technical validation.
let api,act,refresh,url,esc;
const $=id=>document.getElementById(id);
export function initRepairUI(context){
  ({api,act,refresh,url,esc}=context);
  const tab=document.createElement('button');tab.dataset.tab='repairs';tab.textContent='Diagnosis & repairs';
  document.querySelector('.tabs').insertBefore(tab,document.querySelector('[data-tab="results"]'));
  const section=document.createElement('section');section.id='repairs';section.className='tab-content hidden';
  section.innerHTML=`<div class="page-grid"><div><div class="section-title">DIAGNOSIS & TARGETED REPAIR</div>
    <p id="repair-status" class="notice"></p><p class="small">Mesh findings and visual judgments are recorded separately. Rejected candidates are retained and excluded from export.</p>
    <div id="repair-evidence" class="preview-grid"></div><label>Diagnosis, defects, repair plan & budget<textarea id="diagnosis-editor" class="code" rows="24"></textarea></label>
    <div class="review-actions"><button id="diagnose-mesh">Inspect mesh & render views</button><button id="save-diagnosis">Save diagnosis</button><button id="run-repair" class="primary">Run bounded repair</button></div>
    <div class="section-title">BEFORE / AFTER COMPARISON</div><div id="repair-comparisons" class="preview-grid"></div>
    <label>Comparison record<textarea id="repair-comparison" class="code" rows="14"></textarea></label><div id="attempt-actions" class="review-actions"></div>
    <div class="section-title">ATTEMPTS, TIME & COST</div><div id="repair-attempts"></div></div>
    <aside><div class="section-title">SUPPORTED OPERATIONS</div><pre id="repair-capabilities"></pre><p class="small">Unsupported backend settings are refused. Anatomy edits need a saved Blender pass; an unavailable assistant stays pending. Quad remeshing and texture upscaling do not repair missing features.</p>
    <div class="section-title">ACCEPTED VERSIONS & ROLLBACK</div><div id="repair-versions"></div><button id="promote-version">Preserve accepted version</button><button id="rollback-game">Restore previous game visual</button><div class="section-title">REMAINING REVIEW</div><ul id="repair-remaining"></ul></aside></div>`;
  document.querySelector('main').insertBefore(section,$('job-panel'));
}
export async function renderRepairUI(asset,system){
  const aid=asset.id,flow=await api(`/assets/${aid}/diagnosis`);
  const evidence=flow.diagnosis?.evidence||[];
  const record=flow.diagnosis||{status:flow.status,source_sha256:flow.inspection?.source_sha256||asset.artifacts.runtime_sha256||asset.candidates.find(c=>c.id===asset.selected_candidate)?.sha256,
    criteria:['Record criteria specific to this asset'],confidence:'requires_review',evidence:flow.inspection?[{kind:'mesh',path:flow.inspection.mesh},...Object.values(flow.inspection.renders).filter(p=>p.endsWith('.png')).map(path=>({kind:'render',path}))]:[],defects:[],plan:[],budget:flow.budget,remaining_review:flow.remaining_review};
  $('repair-status').textContent=`${flow.status}${flow.temporary_fallback?' (temporary fallback; original '+flow.generated_status+')':''} | ${flow.attempts.length} attempts | ${flow.attempts.reduce((n,a)=>n+(a.elapsed_seconds||0),0).toFixed(1)}s | ${flow.attempts.reduce((n,a)=>n+(a.cost_credits||0),0)} credits`;
  $('diagnosis-editor').value=JSON.stringify(record,null,2);
  $('repair-capabilities').textContent=JSON.stringify(system.repair_capabilities,null,2);
  $('repair-remaining').innerHTML=(flow.remaining_review.map(s=>`<li>${esc(s)}</li>`).join('')||'<li>No outstanding acceptance checks.</li>')+(flow.diagnosis?.future_work||[]).map(s=>`<li>Future art work: ${esc(s)}</li>`).join('');
  const picture=(path,label)=>`<a href="${url(asset,path)}" target="_blank"><img src="${url(asset,path)}" alt="${esc(label)}"><span>${esc(label)}</span></a>`;
  $('repair-evidence').innerHTML=evidence.filter(e=>e.path?.endsWith('.png')).map(e=>picture(e.path,e.notes||e.kind)).join('');
  const attempt=flow.attempts.at(-1),comparison={decision:'accepted',notes:'',evidence:Object.values(attempt?.evidence||{}).filter(p=>p.endsWith('.png')),improved_defects:[],regressions:[],checks:{silhouette:false,materials:false,animation:false,integration:false,reference_fidelity:false,no_regressions:false,gameplay_distance:false}};
  comparison.fallback=false;comparison.fallback_reason='';
  const accepted=flow.versions.find(v=>v.id===flow.accepted_version);
  $('repair-comparison').value=JSON.stringify(attempt?.state==='requires_review'?(attempt.review||comparison):(accepted?.review||attempt?.review||comparison),null,2);
  const compared=accepted&&attempt?.state!=='requires_review'?accepted.artifacts.files:(attempt?.evidence||{});
  $('repair-comparisons').innerHTML=['before.png','after.png'].filter(name=>compared?.[name]).map(name=>picture(compared[name],name)).join('');
  $('repair-attempts').innerHTML=flow.attempts.map(a=>`<div class="candidate-card"><div>${esc(a.kind)} · ${esc(a.state)}<small>${a.elapsed_seconds||0}s · ${a.cost_credits||0} credits · ${esc(a.id)}</small><small>${esc(a.review?.notes||a.notes||'Requires evidence review')}</small></div></div>`).join('')||'<p class="small">No repair attempts. Good assets can remain KEEP.</p>';
  $('attempt-actions').innerHTML=attempt?.state==='requires_review'?['accepted','rejected','plateau'].map(d=>`<button data-attempt-decision="${d}">${d==='accepted'?'Keep improved candidate':d==='rejected'?'Archive & restore previous':'Stop: improvement plateau'}</button>`).join(''):'';
  document.querySelectorAll('[data-attempt-decision]').forEach(b=>b.onclick=act(async()=>{const review=JSON.parse($('repair-comparison').value);review.decision=b.dataset.attemptDecision;await api(`/assets/${aid}/attempts/${attempt.id}/review`,review,'PUT');await refresh(aid);}));
  $('save-diagnosis').onclick=act(async()=>{await api(`/assets/${aid}/diagnosis`,JSON.parse($('diagnosis-editor').value),'PUT');await refresh(aid);});
  $('diagnose-mesh').onclick=act(async()=>{await api(`/assets/${aid}/jobs`,{operation:'diagnose'});await refresh(aid);});
  $('run-repair').disabled=flow.status==='KEEP'||flow.status==='REJECT';
  $('run-repair').onclick=act(async()=>{await api(`/assets/${aid}/repair`,{assisted:flow.plan.some(p=>p.operation==='assisted_blender')});await refresh(aid);});
  $('repair-versions').innerHTML=flow.versions.map(v=>`<div class="candidate-card"><div>${esc(v.id)}${v.id===flow.accepted_version?' · accepted':''}${v.review.fallback?' (temporary fallback)':''}<small>${esc(v.review.notes)}</small><small>${esc(v.review.fallback_reason||'')}</small><a href="${url(asset,v.runtime)}">Versioned GLB</a></div><button data-rollback="${v.id}">Rollback</button>${flow.game_binding?`<button data-deploy="${v.id}">Use in game</button>`:''}</div>`).join('')||'<p class="small">Working game files remain in use until promotion and integration pass.</p>';
  document.querySelectorAll('[data-rollback]').forEach(b=>b.onclick=act(async()=>{await api(`/assets/${aid}/versions/rollback`,{version_id:b.dataset.rollback});await refresh(aid);}));
  document.querySelectorAll('[data-deploy]').forEach(b=>b.onclick=act(async()=>{await api(`/assets/${aid}/game/apply`,{version_id:b.dataset.deploy});await refresh(aid);}));
  $('rollback-game').disabled=!flow.game_binding||!flow.game_version;
  $('rollback-game').onclick=act(async()=>{await api(`/assets/${aid}/game/rollback`,{});await refresh(aid);});
  $('promote-version').onclick=act(async()=>{const r=JSON.parse($('repair-comparison').value);await api(`/assets/${aid}/versions/promote`,{notes:r.notes,evidence:r.evidence,checks:r.checks,fallback:r.fallback||false,fallback_reason:r.fallback_reason||''});await refresh(aid);});
}
