import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {initRepairUI,renderRepairUI} from './reviewflow.js';
import {mountMultiview} from './multiview.js';

const $=id=>document.getElementById(id);
const esc=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const human=s=>s.replaceAll('_',' ').replace(/^./,c=>c.toUpperCase());
let system,assets=[],selected=null,jobs=[],tab='workspace',reference=null,cropImage=null,cropRect=null,defects=[],checkNames=[],viewer=null,comparison=null,polling=false;
const fileUrl=(a,path)=>`/api/assets/${a.id}/files/${path.split('/').map(encodeURIComponent).join('/')}`;
async function api(path,body,method){
  const options={method:method||(body?'POST':'GET'),headers:{'x-forge-request':'1'}};
  if(body instanceof FormData) options.body=body;
  else if(body!==undefined){options.headers['Content-Type']='application/json';options.body=JSON.stringify(body);}
  const response=await fetch('/api'+path,options);
  if(!response.ok){const err=await response.json().catch(()=>({detail:response.statusText}));throw new Error(typeof err.detail==='string'?err.detail:JSON.stringify(err.detail));}
  return response.json();
}
function toast(message,error=false){$('toast').textContent=message;$('toast').classList.remove('hidden');$('toast').classList.toggle('error',error);clearTimeout(toast.timer);toast.timer=setTimeout(()=>$('toast').classList.add('hidden'),error?9000:4500);}
const act=fn=>async event=>{try{await fn(event);}catch(error){toast(error.message,true);}};
function switchTab(value){tab=value;document.querySelectorAll('.tab-content').forEach(el=>el.classList.toggle('hidden',el.id!==value||!selected));document.querySelectorAll('.tabs button').forEach(el=>el.classList.toggle('active',el.dataset.tab===value));if(value==='reference')drawCrop();if(value==='results')loadResults();viewer?.resize();comparison?.resize();}

class Viewer{
  constructor(element,compact=false){
    this.element=element;this.compact=compact;this.scene=new THREE.Scene();this.scene.background=new THREE.Color('#141c23');
    this.camera=new THREE.PerspectiveCamera(35,1,0.005,10000);
    this.renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});this.renderer.setPixelRatio(Math.min(devicePixelRatio,1.7));this.renderer.outputColorSpace=THREE.SRGBColorSpace;this.renderer.toneMapping=THREE.ACESFilmicToneMapping;this.renderer.toneMappingExposure=1.15;
    element.prepend(this.renderer.domElement);this.controls=new OrbitControls(this.camera,this.renderer.domElement);this.controls.enableDamping=true;
    this.pmrem=new THREE.PMREMGenerator(this.renderer);this.environment=this.pmrem.fromScene(new RoomEnvironment(),0.04);this.scene.environment=this.environment.texture;
    this.ambient=new THREE.HemisphereLight(0xc7d5e8,0x414939,1.6);this.scene.add(this.ambient);
    this.key=new THREE.DirectionalLight(0xfff0d8,3);this.key.position.set(4,6,5);this.scene.add(this.key);
    this.fill=new THREE.DirectionalLight(0xb4d2e5,1.5);this.fill.position.set(-4,2,-4);this.scene.add(this.fill);
    this.clock=new THREE.Clock();this.original=new Map();this.helpers=[];this.mode='textured';this.paused=false;this.token=0;this.generatedMaterials=[];
    new ResizeObserver(()=>this.resize()).observe(element);
    this.renderer.setAnimationLoop(()=>{const dt=Math.min(this.clock.getDelta(),.1);this.controls.update();if(!this.paused)this.mixer?.update(dt);this.renderer.render(this.scene,this.camera);});
  }
  resize(){const w=this.element.clientWidth,h=this.element.clientHeight;if(!w||!h)return;this.camera.aspect=w/h;this.camera.updateProjectionMatrix();this.renderer.setSize(w,h,false);}
  clear(){if(this.root){this.scene.remove(this.root);this.root.traverse(node=>{if(node.geometry)node.geometry.dispose();});for(const mats of this.original.values())for(const mat of [].concat(mats)){for(const value of Object.values(mat))if(value?.isTexture)value.dispose();mat.dispose();}}this.original.clear();for(const helper of this.helpers){this.scene.remove(helper);helper.dispose();}this.helpers=[];this.root=null;this.mixer=null;this.size=1;this.gltf=null;for(const mat of this.generatedMaterials)mat.dispose();this.generatedMaterials=[];}
  async load(url,previewRotation=[]){
    const token=++this.token;const gltf=await new GLTFLoader().loadAsync(url);if(token!==this.token)return;this.clear();this.gltf=gltf;this.root=gltf.scene;this.scene.add(this.root);
    if(previewRotation.length===3)this.root.rotation.set(...previewRotation.map(THREE.MathUtils.degToRad),'YXZ');
    this.root.updateMatrixWorld(true);const box=new THREE.Box3().setFromObject(this.root);const center=box.getCenter(new THREE.Vector3());this.root.position.sub(center);this.root.updateMatrixWorld(true);this.size=Math.max(box.getSize(new THREE.Vector3()).length(),.1);
    let triangles=0;const mats=new Set(),textures=new Set();
    const skeletons=new Set();this.root.traverse(node=>{if(node.isMesh){this.original.set(node,node.material);triangles+=(node.geometry.index?.count||node.geometry.attributes.position.count)/3;for(const mat of [].concat(node.material)){mats.add(mat);for(const value of Object.values(mat))if(value?.isTexture)textures.add(value);}}if(node.isSkinnedMesh)skeletons.add(node.skeleton);});
    for(const skeleton of skeletons){let rootBone=skeleton.bones[0];while(rootBone.parent?.isBone)rootBone=rootBone.parent;const helper=new THREE.SkeletonHelper(rootBone);helper.material.depthTest=false;helper.material.transparent=true;helper.renderOrder=999;helper.visible=$('skeleton-toggle').checked;this.helpers.push(helper);this.scene.add(helper);}
    this.triangles=Math.round(triangles);this.materials=mats.size;this.textures=textures.size;this.mixer=new THREE.AnimationMixer(this.root);this.action=null;this.clips=gltf.animations;
    this.setMode(this.mode);this.frame('inspect');this.resize();
    const boneCount=[...skeletons].reduce((n,s)=>n+s.bones.length,0);this.element.dataset.skeletonSegments=this.helpers.reduce((n,h)=>n+h.geometry.attributes.position.count/2,0);
    if(!this.compact){$('viewer-stats').textContent=`${this.triangles.toLocaleString()} triangles · ${mats.size} materials · ${textures.size} textures${boneCount?' · '+boneCount+' bones · '+this.clips.length+' clips':''}`;$('viewer-message').classList.add('hidden');$('animation-select').innerHTML='<option value="">Rest pose</option>'+this.clips.map((clip,i)=>`<option value="${i}">${esc(clip.name)} · ${clip.duration.toFixed(2)}s</option>`).join('');}
  }
  setMode(mode){this.mode=mode;for(const mat of this.generatedMaterials)mat.dispose();this.generatedMaterials=[];this.original.forEach((original,node)=>{if(mode==='textured'){node.material=original;return;}let material;if(mode==='normal')material=new THREE.MeshNormalMaterial({side:THREE.DoubleSide});else material=new THREE.MeshStandardMaterial({color:mode==='clay'?0x8d9698:0xb6c3aa,roughness:.86,metalness:0,wireframe:mode==='wireframe',side:THREE.DoubleSide});this.generatedMaterials.push(material);node.material=material;});}
  setLight(preset){const warm=preset==='warm',game=preset==='game';this.key.color.set(warm?0xffd3a0:0xfff0e4);this.fill.color.set(warm?0xccb6a6:0xb4d2e5);this.key.intensity=game?1.6:3;this.ambient.intensity=game?.7:1.6;this.renderer.toneMappingExposure=game?.95:1.15;}
  frame(distance){const d=this.size*(distance==='close'?.65:distance==='gameplay'?3.5:1.8);const sign=selected?.settings.front_axis==='+Z'?1:-1;this.controls.target.set(0,0,0);this.camera.position.set(d*.13,d*.06,d*sign);this.camera.near=Math.max(.001,this.size/1000);this.camera.far=Math.max(100,this.size*100);this.camera.updateProjectionMatrix();this.controls.update();}
  play(index){this.mixer?.stopAllAction();if(index!==''){this.action=this.mixer.clipAction(this.clips[Number(index)]);this.action.reset().play();this.paused=false;}else this.action=null;}
  capture(){this.renderer.render(this.scene,this.camera);const link=document.createElement('a');link.href=this.renderer.domElement.toDataURL('image/png');link.download=`${selected?.name||'asset'}_${this.mode}.png`;link.click();}
}

function renderLibrary(){
  $('asset-list').innerHTML=assets.filter(a=>(!$('library-search').value||a.name.toLowerCase().includes($('library-search').value.toLowerCase()))&&(!$('library-status').value||a.reviewflow?.status===$('library-status').value)).map(a=>{const thumb=a.artifacts?.files?.['turntable_00.png'];return `<button class="asset-card ${selected?.id===a.id?'active':''}" data-id="${a.id}">${thumb?`<img src="${fileUrl(a,thumb)}" alt="">`:'<span class="asset-icon">◇</span>'}<div><strong>${esc(a.name)}</strong><small>${esc(human(a.preset))} · ${esc(a.reviewflow?.status||a.review.status)}${a.reviewflow?.temporary_fallback?' (temporary fallback)':''}</small></div></button>`;}).join('');
  document.querySelectorAll('.asset-card').forEach(el=>el.onclick=act(()=>selectAsset(el.dataset.id)));
}
async function refreshAssets(){assets=await api('/assets');if(selected)selected=assets.find(a=>a.id===selected.id)||selected;renderLibrary();}
async function selectAsset(id){$('compare-area').classList.add('hidden');$('workspace').classList.remove('comparing');comparison?.clear();selected=await api('/assets/'+id);reference=null;cropImage=null;cropRect=null;renderLibrary();await renderAsset();}
async function renderAsset(){
  if(!selected)return;
  $('empty-state').classList.add('hidden');$('job-panel').classList.remove('hidden');$('asset-title').textContent=selected.name;
  const candidate=selected.candidates.find(c=>c.id===selected.selected_candidate);$('origin-badge').textContent=candidate?human(candidate.origin):'REFERENCE ONLY';
  $('compare-button').disabled=selected.candidates.filter(c=>c.path.endsWith('.glb')&&!c.archived).length<2;
  $('review-badge').textContent=human(selected.review.status)+(selected.review.status==='pending'?' · visual review':'');$('review-badge').classList.toggle('failed',selected.review.status==='rejected');
  $('export-button').disabled=selected.review.status!=='accepted'||selected.artifacts.stale===true;
  const primary=[...selected.references].reverse().find(r=>r.role==='primary');
  if(primary){$('reference-image').src=fileUrl(selected,primary.path);$('reference-empty').classList.add('hidden');$('reference-info').textContent=`${primary.resolution.join(' × ')} px · ${primary.original?'original':'prepared crop'}`;}
  else{$('reference-image').removeAttribute('src');$('reference-empty').classList.remove('hidden');}
  $('candidates').innerHTML=selected.candidates.length?selected.candidates.map((c,i)=>`<div class="candidate-card ${c.id===selected.selected_candidate?'active':''}"><div>Candidate ${String(i+1).padStart(2,'0')} · ${esc(human(c.origin))}<small>${esc(c.model||c.original_filename||'Imported source')} · ${c.triangles?c.triangles.toLocaleString()+' triangles · ':''}${c.cost_credits||0} credits${c.elapsed_seconds?' · '+c.elapsed_seconds+'s':''}</small>${c.archived?`<small>Archived: ${esc(c.archive_reason||'Excluded from selection and export')}</small>`:''}</div><button data-candidate="${c.id}" ${c.id===selected.selected_candidate||c.archived?'disabled':''}>Select</button></div>`).join(''):'<p class="small">Import an existing mesh or reconstruct your prepared reference.</p>';
  document.querySelectorAll('[data-candidate]').forEach(el=>el.onclick=act(async()=>{await api(`/assets/${selected.id}/select`,{candidate_id:el.dataset.candidate});await selectAsset(selected.id);}));
  const files=selected.artifacts.files||{};const choices=[];
  if(files['runtime.glb'])choices.push(['Runtime',files['runtime.glb']]);
  if(files['source.glb'])choices.push(['Preserved source',files['source.glb']]);
  for(const key of Object.keys(files))if(/^lod\d\.glb$/.test(key))choices.push([key+' · review pending',files[key]]);
  if(candidate?.path.endsWith('.glb'))choices.push(['Original candidate',candidate.path]);
  $('view-file').innerHTML=choices.map(([name,path])=>`<option value="${esc(path)}">${esc(name)}</option>`).join('');
  if(!viewer){try{viewer=new Viewer($('viewer'));}catch(error){$('viewer-message').textContent='WebGL unavailable: '+error.message;}}
  if(choices.length){await loadViewer(choices[0][1]);}
  else{viewer?.clear();$('viewer-message').classList.remove('hidden');$('viewer-message').textContent=candidate?'Run Blender to normalize this file for review':'Import or generate a mesh to inspect it';$('viewer-stats').textContent='';}
  $('design-requirements').value=selected.design_requirements;$('unseen-surfaces').value=selected.unseen_surfaces;$('license-note').value=selected.provenance.license;
  $('config-editor').value=JSON.stringify(selected.settings,null,2);
  $('optimization-mode').value=selected.settings.optimization_mode||'preserve';
  $('triangle-target').value=selected.settings.triangle_budget;
  $('optimization-summary').textContent='No optimization report yet. Save settings and process to compare the result.';
  if(files['optimization.json']){
    const response=await fetch(fileUrl(selected,files['optimization.json']));
    if(response.ok){
      const report=await response.json();
      const retained=(report.objects||[]).filter(o=>o.status==='quality_guard_kept_source').length;
      const rejected=(report.objects||[]).reduce((n,o)=>n+(o.rejected_attempts||[]).length,0);
      $('optimization-summary').textContent=report.mode==='preserve'?'Source geometry preserved.':`Target ${report.target_triangles.toLocaleString()} / achieved ${report.achieved_triangles.toLocaleString()} triangles. ${retained} meshes kept their source after quality checks; ${rejected} attempts rejected. Full details are in optimization.json under Files & validation.`;
    }
  }

  $('stage-list').innerHTML=(selected.settings.stages||system.presets[selected.preset].stages).map((stage,i)=>`<span>${i+1} / ${esc(human(stage))}</span>`).join('');
  renderGenerationControls(primary);
  $('process').disabled=!candidate;$('turntable').disabled=!candidate;$('godot').disabled=!files['runtime.glb'];
  $('retexture').disabled=candidate?.origin!=='generated_local'||candidate?.model!=='stabilityai/TripoSR';
  $('review-notes').value=selected.review.notes||'';$('override-reason').value=selected.review.override_reason||'';defects=structuredClone(selected.review.defects||[]);
  checkNames=await api(`/assets/${selected.id}/review-checks`);$('review-checklist').innerHTML=checkNames.map(name=>`<label><input type="checkbox" data-check="${name}" ${selected.review.checklist?.[name]?'checked':''}>${esc(human(name))}</label>`).join('');
  const validation=selected.artifacts.validation;$('technical-summary').classList.toggle('failed',validation?.technical_status==='failed'||selected.artifacts.stale===true);$('technical-summary').textContent=selected.artifacts.stale?'Settings changed. Reprocess before accepting this version.':validation?`Technical checks ${validation.technical_status} · ${validation.triangles.toLocaleString()} triangles · ${validation.errors.length} errors · ${validation.warnings.length} warnings. Visual acceptance requires your checklist.`:'No processed version. Import/generate and process before acceptance.';
  renderDefects();renderReferences();renderJobs();await renderRepairUI(selected,system);switchTab(tab);
}
async function loadViewer(path){if(!viewer)return;const url=fileUrl(selected,path);if(viewer.currentUrl===url)return;viewer.currentUrl=url;$('viewer-message').classList.remove('hidden');$('viewer-message').textContent='Loading geometry…';try{await viewer.load(url,selected.candidates.find(c=>c.path===path)?.preview_rotation_degrees||[]);}catch(error){viewer.currentUrl=null;$('viewer-message').textContent='Review load failed: '+error.message;throw error;}}
function renderReferences(){
  $('reference-list').innerHTML=selected.references.map((r,i)=>`<button data-ref="${r.id}" class="${reference?.id===r.id?'active':''}">${i+1} · ${r.resolution.join('×')} · ${esc(r.role)}${r.original?' · original':''}</button>`).join('');
  document.querySelectorAll('[data-ref]').forEach(el=>el.onclick=act(()=>chooseReference(el.dataset.ref)));
  if(!reference&&selected.references.length)chooseReference(selected.references.at(-1).id);
}
async function chooseReference(id){reference=selected.references.find(r=>r.id===id);if(!reference)return;$('consistency-panel').classList.toggle('hidden',reference.consistency_review!=='pending');cropImage=new Image();cropImage.src=fileUrl(selected,reference.path);await cropImage.decode();cropRect={x:0,y:0,w:cropImage.naturalWidth,h:cropImage.naturalHeight};setCropFields();drawCrop();document.querySelectorAll('[data-ref]').forEach(el=>el.classList.toggle('active',el.dataset.ref===id));}
function setCropFields(){for(const [id,key]of [['crop-x','x'],['crop-y','y'],['crop-w','w'],['crop-h','h']])$(id).value=cropRect[key];}
function drawCrop(){if(!cropImage||!cropRect)return;const c=$('crop-canvas');const scale=Math.min(1,350/cropImage.naturalHeight,(c.parentElement.clientWidth||650)/cropImage.naturalWidth);c.width=Math.round(cropImage.naturalWidth*scale);c.height=Math.round(cropImage.naturalHeight*scale);const ctx=c.getContext('2d');ctx.drawImage(cropImage,0,0,c.width,c.height);ctx.fillStyle='#06100955';ctx.fillRect(0,0,c.width,c.height);ctx.save();ctx.beginPath();ctx.rect(cropRect.x*scale,cropRect.y*scale,cropRect.w*scale,cropRect.h*scale);ctx.clip();ctx.drawImage(cropImage,0,0,c.width,c.height);ctx.restore();ctx.strokeStyle='#cbdfb3';ctx.lineWidth=2;ctx.strokeRect(cropRect.x*scale,cropRect.y*scale,cropRect.w*scale,cropRect.h*scale);}
let cropStart=null;
function cropPoint(event){const rect=$('crop-canvas').getBoundingClientRect();return {x:Math.max(0,Math.min(cropImage.naturalWidth,Math.round((event.clientX-rect.left)/rect.width*cropImage.naturalWidth))),y:Math.max(0,Math.min(cropImage.naturalHeight,Math.round((event.clientY-rect.top)/rect.height*cropImage.naturalHeight)))};}
$('crop-canvas').onpointerdown=e=>{if(!cropImage)return;cropStart=cropPoint(e);$('crop-canvas').setPointerCapture(e.pointerId);};
$('crop-canvas').onpointermove=e=>{if(!cropStart)return;const p=cropPoint(e);cropRect={x:Math.min(p.x,cropStart.x),y:Math.min(p.y,cropStart.y),w:Math.max(1,Math.abs(p.x-cropStart.x)),h:Math.max(1,Math.abs(p.y-cropStart.y))};setCropFields();drawCrop();};
$('crop-canvas').onpointerup=()=>{cropStart=null;};
for(const id of ['crop-x','crop-y','crop-w','crop-h'])$(id).onchange=()=>{cropRect={x:+$('crop-x').value,y:+$('crop-y').value,w:+$('crop-w').value,h:+$('crop-h').value};drawCrop();};
function renderDefects(){$('defect-list').innerHTML=defects.map((d,i)=>`<div class="defect"><input type="checkbox" aria-label="Resolve defect" data-defect="${i}" ${d.resolved?'checked':''}><span>${esc(d.description)}</span><button data-remove-defect="${i}" aria-label="Remove defect">×</button></div>`).join('');document.querySelectorAll('[data-defect]').forEach(el=>el.onchange=()=>defects[+el.dataset.defect].resolved=el.checked);document.querySelectorAll('[data-remove-defect]').forEach(el=>el.onclick=()=>{defects.splice(+el.dataset.removeDefect,1);renderDefects();});}
async function saveReview(status){const checklist={};document.querySelectorAll('[data-check]').forEach(el=>checklist[el.dataset.check]=el.checked);await api(`/assets/${selected.id}/review`,{status,notes:$('review-notes').value,defects,checklist,override_reason:$('override-reason').value},'PUT');await refreshAssets();$('review-badge').textContent=human(status);$('export-button').disabled=status!=='accepted';toast(status==='accepted'?'Reviewed version accepted. Export bundle is available.':'Review saved.');}
async function loadResults(){if(!selected)return;const files=selected.artifacts.files||{},previews=selected.artifacts.previews||{};$('file-list').innerHTML=Object.entries(files).map(([name,path])=>`<a class="file-link" href="${fileUrl(selected,path)}" download>${esc(name)} ↓</a>`).join('')||'<p class="small">Run Blender processing to create exports and inspection reports.</p>';
  $('validation-report').textContent=JSON.stringify(selected.artifacts.validation||{status:'No processed version'},null,2);$('processing-report').textContent=files['processing.json']?JSON.stringify(await fetch(fileUrl(selected,files['processing.json'])).then(r=>r.json()),null,2):'No processing report';
  const pictures=[files['turntable_00.png'],files['clay.png'],previews['turntable.gif']].filter(Boolean);$('previews').innerHTML=pictures.map(path=>`<a href="${fileUrl(selected,path)}" target="_blank"><img src="${fileUrl(selected,path)}" alt="Actual rendered asset preview"></a>`).join('');
  const godot=selected.artifacts.godot;$('godot-report').textContent=JSON.stringify(godot||{status:'Not run'},null,2);$('godot-summary').innerHTML=godot?`<p class="small">Import ${esc(godot.technical.status)} · ${godot.technical.triangles.toLocaleString()} triangles · ${godot.technical.bones} bones</p>${godot.performance.average_fps?`<div class="notice">${godot.performance.average_fps.toFixed(1)} measured FPS<br>${godot.performance.instances} instances · ${godot.performance.average_frame_ms.toFixed(2)} ms average</div>`:''}${[['gameplay.png','Godot gameplay screenshot'],['closeup.png','Godot close-up screenshot'],['multi_instance.png','Measured instance grid'],...(godot.performance.animation_previews||[]).map(clip=>['preview_'+clip+'.gif',human(clip)+' animation preview'])].map(([path,label])=>`<a class="file-link" href="${fileUrl(selected,godot.project+'/results/'+path)}" target="_blank">${esc(label)} ↗</a>`).join('')}`:'<p class="small">Run the Godot stage to inspect import, animations and measured rendering.</p>';
  $('manifest-link').href=fileUrl(selected,'manifest.json');$('manifest-link').setAttribute('download','manifest.json');$('provenance-summary').textContent=selected.provenance.license;
}
function renderJobs(){const active=jobs.filter(j=>['running','queued'].includes(j.state));$('job-indicator').textContent=active.length?`${active.length} active · ${active[0].stage.replaceAll('_',' ')}`:'No active jobs';if(!selected)return;const own=jobs.filter(j=>j.asset_id===selected.id).slice(0,8);$('jobs').innerHTML=own.map(j=>`<div class="job-row"><span class="badge ${j.state==='failed'?'failed':'muted'}">${esc(j.state)}</span><div class="job-description"><strong>${esc(human(j.operation))} · ${esc(j.stage)}${j.duration_seconds?' · '+j.duration_seconds+'s':''}</strong><small>${esc(j.message)}</small>${j.reason?`<small>Reason: ${esc(j.reason)}</small>`:''}</div>${['running','queued'].includes(j.state)?`<button data-cancel="${j.id}">Cancel</button>`:''}${['failed','cancelled','interrupted'].includes(j.state)?`<button data-resume="${j.id}">Resume stage</button>`:''}<a href="${fileUrl(selected,'logs/'+j.id+'.log')}" target="_blank">Log ↗</a></div>`).join('')||'<p class="small">No jobs for this asset.</p>';document.querySelectorAll('[data-cancel]').forEach(el=>el.onclick=act(async()=>{await api('/jobs/'+el.dataset.cancel+'/cancel',{});toast('Cancellation requested.');}));document.querySelectorAll('[data-resume]').forEach(el=>el.onclick=act(async()=>{await api('/jobs/'+el.dataset.resume+'/resume',{});await poll();}));}
async function submit(operation){
  const backend=$('generation-backend').value;
  const opts=operation==='generate'?{backend,...(backend==='trellis'?multiview.options():{})}:operation==='godot'?{instances:25,rendered_benchmark:true}:{};
  if(operation==='generate'&&backend==='trellis')await api(`/assets/${selected.id}/settings`,{...selected.settings,...multiview.settings()},'PUT');
  await api(`/assets/${selected.id}/jobs`,{operation,options:opts,reason:$('retry-reason').value});toast(human(operation)+' queued.');await poll();
}
function renderGenerationControls(primary){
  const candidate=selected.candidates.find(c=>c.id===selected.selected_candidate),select=$('generation-backend');
  const inherited=candidate?.backend||(candidate?.model==='VAST-AI/TripoSG'?'triposg':candidate?.model==='stabilityai/TripoSR'?'triposr':selected.reference_sets?.length&&system.backends.find(b=>b.id==='trellis'&&b.available)?'trellis':system.backends.find(b=>b.id==='triposg'&&b.available)?.id||'triposr');
  const previous=select.dataset.assetId===selected.id?(select.value||inherited):inherited;
  select.dataset.assetId=selected.id;
  select.innerHTML=system.backends.filter(b=>b.id!=='meshy').map(b=>`<option value="${b.id}" ${b.available?'':'disabled'}>${esc(b.label)}${b.vertex_colors?' · vertex color':b.textures?' · base color':' · shape only'}${b.available?'':' · setup required'}</option>`).join('');
  select.value=previous;
  const backend=system.backends.find(b=>b.id===select.value);
  const update=()=>{$('generate').disabled=!backend?.available||!(backend.multi_view&&multiview.selectedSet()||primary);};
  multiview.render(selected,backend,update); update();
  $('generate').querySelector('small').textContent=(backend?.label||'Local generator')+' · 0 service credits';
  $('backend-state').textContent=backend?.available?(backend.multi_view?'Combine separate reviewed views into one mesh. Native colors, inferred geometry; inspect the output before replacement.':backend.textures?'Local reconstruction uses one image; hidden surfaces remain uncertain.':'Local geometry reconstruction. No generated textures or PBR maps; review the clay mesh and author materials separately.'):'Complete backend setup and the compatibility test. Imported meshes remain available.';
}
async function poll(){if(polling)return;polling=true;try{const next=await api('/jobs');const changed=next.some(j=>['succeeded','failed','cancelled'].includes(j.state)&&jobs.find(old=>old.id===j.id)?.state!==j.state);jobs=next;renderJobs();if(changed){await refreshAssets();if(selected)await renderAsset();system=await api('/system');}}catch(error){console.warn('Job polling:',error.message);}finally{polling=false;}}
function renderCapabilities(){$('capabilities').innerHTML=system.backends.map(b=>`<div class="cap-card"><strong>${esc(b.label)}</strong><p class="small">${esc(b.disabled_reason||b.limitations)}</p><div class="cap-grid">${['single_image','multi_view','textures','pbr','parts','rigging','pose_control','seeds'].map(key=>`<label><input type="checkbox" disabled ${b[key]?'checked':''}> ${esc(human(key))}</label>`).join('')}</div><p class="small">${esc(b.license)}</p></div>`).join('');}

initRepairUI({api,act,refresh:selectAsset,url:fileUrl,esc});
document.querySelectorAll('.tabs button').forEach(el=>el.onclick=()=>switchTab(el.dataset.tab));
for(const id of ['new-asset','empty-create'])$(id).onclick=()=>$('create-dialog').showModal();
$('cancel-create').onclick=()=>$('create-dialog').close();
$('create-form').onsubmit=act(async event=>{event.preventDefault();const form=new FormData(event.target);const a=await api('/assets',Object.fromEntries(form));$('create-dialog').close();event.target.reset();await refreshAssets();tab='reference';await selectAsset(a.id);});
$('reference-upload').onchange=act(async e=>{if(!selected)throw Error('Create an asset first');const form=new FormData();form.set('file',e.target.files[0]);form.set('role',$('reference-role').value);await api(`/assets/${selected.id}/references`,form);e.target.value='';await selectAsset(selected.id);toast('Original reference saved.');});
$('mesh-upload').onchange=act(async e=>{if(!selected)throw Error('Create an asset first');const form=new FormData();form.set('file',e.target.files[0]);form.set('license_note',$('license-note').value);await api(`/assets/${selected.id}/import`,form);e.target.value='';await selectAsset(selected.id);toast('Imported candidate saved. Run Blender to inspect and export.');});
$('save-crop').onclick=act(async()=>{if(!reference)throw Error('Choose a reference first');await api(`/assets/${selected.id}/prepare`,{reference_id:reference.id,crop:[cropRect.x,cropRect.y,cropRect.w,cropRect.h],rotation_degrees:Number($('reference-rotation').value),remove_background:$('remove-bg').checked,background_color:$('background-color').value,tolerance:+$('bg-tolerance').value,role:$('reference-role').value});await selectAsset(selected.id);toast('Prepared crop saved at original pixel resolution.');});
$('save-design').onclick=act(async()=>{await api(`/assets/${selected.id}/design`,{design_requirements:$('design-requirements').value,unseen_surfaces:$('unseen-surfaces').value,license:$('license-note').value},'PUT');await refreshAssets();toast('Design contract saved.');});
$('save-config').onclick=act(async()=>{await api(`/assets/${selected.id}/settings`,JSON.parse($('config-editor').value),'PUT');await selectAsset(selected.id);toast('Settings saved. Reprocess to validate this configuration.');});
for(const id of ['optimization-mode','triangle-target'])$(id).onchange=act(async()=>{const settings=JSON.parse($('config-editor').value);settings.optimization_mode=$('optimization-mode').value;settings.triangle_budget=Number($('triangle-target').value);$('config-editor').value=JSON.stringify(settings,null,2);});
const backendLabel=document.createElement('label');backendLabel.textContent='Generation backend';const backendSelect=document.createElement('select');backendSelect.id='generation-backend';backendSelect.setAttribute('aria-label','Generation backend');backendLabel.appendChild(backendSelect);$('generate').before(backendLabel);backendSelect.onchange=()=>renderGenerationControls([...selected.references].reverse().find(r=>r.role==='primary'));
const multiview=mountMultiview({api,esc,fileUrl,current:()=>selected,reload:selectAsset,notify:toast});
const rotationLabel=document.createElement('label');rotationLabel.textContent='Rotate prepared view';const rotationSelect=document.createElement('select');rotationSelect.id='reference-rotation';rotationSelect.innerHTML=[0,90,180,270].map(d=>`<option value="${d}">${d}°</option>`).join('');rotationLabel.appendChild(rotationSelect);$('save-crop').before(rotationLabel);
for(const operation of ['generate','retexture','process','turntable','godot'])$(operation).onclick=act(()=>submit(operation));
$('edit-reference').onclick=()=>switchTab('reference');
$('view-file').onchange=act(e=>loadViewer(e.target.value));
document.querySelectorAll('[data-mode]').forEach(el=>el.onclick=()=>{document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b===el));viewer?.setMode(el.dataset.mode);comparison?.setMode(el.dataset.mode);});
$('lighting').onchange=e=>{viewer?.setLight(e.target.value);comparison?.setLight(e.target.value);};
$('skeleton-toggle').onchange=e=>{for(const helper of viewer?.helpers||[])helper.visible=e.target.checked;};
$('animation-select').onchange=e=>viewer?.play(e.target.value);
$('play-animation').onclick=()=>{if(viewer){viewer.paused=!viewer.paused;$('play-animation').textContent=viewer.paused?'Play':'Pause';}};
$('distance').onchange=e=>viewer?.frame(e.target.value);
$('capture').onclick=()=>viewer?.capture();
$('add-defect').onclick=()=>{const text=$('defect-text').value.trim();if(text){defects.push({description:text,resolved:false,evidence:'Human visual review'});$('defect-text').value='';renderDefects();}};
$('save-review').onclick=act(()=>saveReview('pending'));$('reject-review').onclick=act(()=>saveReview('rejected'));$('accept-review').onclick=act(()=>saveReview('accepted'));
$('export-button').onclick=()=>{window.location.href=`/api/assets/${selected.id}/export`;};
$('system-button').onclick=async()=>{system=await api('/system');$('system-info').textContent=JSON.stringify(system,null,2);$('system-dialog').showModal();};$('close-system').onclick=()=>$('system-dialog').close();
$('compare-button').onclick=act(async()=>{const candidates=selected.candidates.filter(c=>c.path.endsWith('.glb')&&!c.archived);if(candidates.length<2)throw Error('Import or generate a second GLB candidate to compare');$('compare-area').classList.remove('hidden');$('workspace').classList.add('comparing');document.querySelector('.workbench-grid').appendChild($('compare-area'));$('compare-select').innerHTML=candidates.map((c,i)=>`<option value="${esc(c.path)}">Candidate ${i+1} · ${esc(human(c.origin))}</option>`).join('');if(!comparison)comparison=new Viewer($('compare-viewer'),true);const other=candidates.find(c=>c.id!==selected.selected_candidate);await comparison.load(fileUrl(selected,other.path),other.preview_rotation_degrees||[]);comparison.setMode(viewer?.mode||'textured');$('compare-select').value=other.path;viewer?.resize();});
$('compare-select').onchange=act(async e=>{const c=selected.candidates.find(c=>c.path===e.target.value);await comparison.load(fileUrl(selected,e.target.value),c?.preview_rotation_degrees||[]);comparison.setMode(viewer?.mode||'textured');});$('close-compare').onclick=()=>{$('compare-area').classList.add('hidden');$('workspace').classList.remove('comparing');viewer?.resize();};
$('approve-reference').onclick=act(async()=>{await api(`/assets/${selected.id}/references/${reference.id}/review`,{consistency_approved:true,notes:$('consistency-notes').value},'PUT');await selectAsset(selected.id);toast('Consistency review recorded. You can now prepare this view as primary authority.');});

async function init(){system=await api('/system');assets=await api('/assets');jobs=await api('/jobs');$('preset-select').innerHTML=Object.entries(system.presets).map(([id,p])=>`<option value="${id}" ${id==='equipment'?'selected':''}>${esc(p.label)}</option>`).join('');renderCapabilities();renderLibrary();const gallery=await api('/gallery');$('gallery').innerHTML=gallery.map(g=>`<button data-gallery="${esc(g.path)}"><img src="${g.url}" alt="${esc(g.name)}" loading="lazy"><span>${esc(g.name)}</span></button>`).join('')||'<p class="small">Configured concept gallery is unavailable.</p>';document.querySelectorAll('[data-gallery]').forEach(el=>el.onclick=act(async()=>{if(!selected)throw Error('Create an asset first');await api(`/assets/${selected.id}/gallery-reference`,{path:el.dataset.gallery});await selectAsset(selected.id);toast('Gallery original copied into this asset.');}));const requested=new URLSearchParams(location.search).get('asset');if(assets.length){await selectAsset(assets.some(a=>a.id===requested)?requested:assets[0].id);if(requested)switchTab('repairs');}setInterval(poll,2500);}
$('library-search').oninput=renderLibrary;$('library-status').onchange=renderLibrary;
init().catch(error=>toast('Application startup: '+error.message,true));
