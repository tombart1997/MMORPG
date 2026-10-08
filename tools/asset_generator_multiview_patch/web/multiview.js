// Practical turnarounds are split into individual prepared references first.
// A reviewed set then freezes the exact pixels/angle/pose contract at enqueue.
export function mountMultiview({api, esc, fileUrl, current, reload, notify}) {
  const container = document.createElement('section');
  container.className = 'multiview-panel';
  container.innerHTML = `<h2>Combined reference views</h2>
    <p class="small">Upload separate views or crop them from a turnaround sheet above. Assign each angle once. Use the same asset, pose, proportions and materials in every view. Hidden details in generated views are interpretations of the original concept.</p>
    <label>Set name<input id="mv-name" value="Neutral production views"></label>
    <label>Original concept authority<select id="mv-authority"></select></label>
    <label>Pose<input id="mv-pose" value="Neutral standing pose; all views show the same pose."></label>
    <label>Proportions and scale notes<input id="mv-scale" value="Same proportions across views; orthographic primary angles, mild perspective three-quarter."></label>
    <div id="mv-members"></div><button id="mv-create">Save a new view set</button>
    <div id="mv-sets"></div>`;
  document.getElementById('reference-list').before(container);
  const generation = document.createElement('div');
  generation.className = 'multiview-generation';
  generation.innerHTML = `<label>Generation inputs<select id="mv-generation-set"><option value="">Single primary image</option></select></label>
    <label>Combined conditioning<select id="mv-mode"><option value="multidiffusion">Combine every view at each step</option><option value="stochastic">Cycle views across steps (faster)</option></select></label>
    <label>TRELLIS steps per stage<input id="mv-steps" type="number" min="6" max="50" value="25"></label>
    <label>TRELLIS guidance<input id="mv-guidance" type="number" min="1" max="12" step="0.5" value="5"></label>
    <label><span><input id="mv-project-colors" type="checkbox"> Project reviewed orthographic color details (check mesh orientation first)</span></label>
    <p class="small" id="mv-generation-note"></p>`;
  document.getElementById('generate').before(generation);
  const $ = id => document.getElementById(id);
  let assetId;
  let generationAssetId;
  let onChange = () => {};
  function render(asset, backend, change) {
    onChange = change;
    const refs = asset.references;
    if (assetId !== asset.id) {
      assetId = asset.id;
      $('mv-mode').value = asset.settings.multiview_mode || 'multidiffusion';
      $('mv-steps').value = asset.settings.trellis_steps || 25;
      $('mv-guidance').value = asset.settings.trellis_guidance || 5;
      $('mv-project-colors').checked = asset.settings.project_reference_colors === true && asset.candidates.length > 0;
    }
    $('mv-authority').innerHTML = refs.map(r => `<option value="${r.id}">${esc(r.original_filename || r.path)} · ${esc(r.role)}</option>`).join('');
    const defaultSet = (asset.reference_sets || []).find(s => s.id === asset.selected_reference_set);
    $('mv-members').innerHTML = ['front','left','back','right','three_quarter','top'].map(angle => {
      const selected = defaultSet?.views.find(v => v.angle === angle)?.reference_id;
      return `<label>${esc(angle.replace('_',' '))}<select data-mv-angle="${angle}"><option value="">Omit this angle</option>${refs.map(r => `<option value="${r.id}" ${selected === r.id ? 'selected' : ''}>${esc(r.original_filename || r.path)} · ${r.resolution.join('×')}</option>`).join('')}</select></label>`;
    }).join('');
    const sets = asset.reference_sets || [];
    const previous = generationAssetId === asset.id ? $('mv-generation-set').value : asset.selected_reference_set || '';
    generationAssetId = asset.id;
    $('mv-generation-set').innerHTML = '<option value="">Single primary image</option>' + sets.map(s => `<option value="${s.id}" ${s.review.status === 'approved' ? '' : 'disabled'}>${esc(s.name)} · ${s.views.length} views · ${s.review.status}</option>`).join('');
    $('mv-generation-set').value = sets.some(s => s.id === previous && s.review.status === 'approved') ? previous : '';
    $('mv-sets').innerHTML = sets.map(s => `<article class="mv-set"><strong>${esc(s.name)}</strong><span>${s.review.status}</span><p class="small">${esc(s.pose)} ${esc(s.scale_notes)}</p><div class="mv-thumbs">${s.views.map(v => `<a href="${fileUrl(asset,v.path)}" target="_blank"><img src="${fileUrl(asset,v.path)}" alt="${esc(v.angle)} view"><span>${esc(v.angle.replace('_',' '))}</span></a>`).join('')}</div><textarea data-mv-notes="${s.id}" rows="2" placeholder="Record inspection: identity, pose, limb spacing, proportions, materials, inferred details">${esc(s.review.notes || '')}</textarea><button data-mv-approve="${s.id}">Approve consistency</button><button data-mv-reject="${s.id}">Reject set</button></article>`).join('');
    for (const decision of ['approve','reject']) for (const button of container.querySelectorAll(`[data-mv-${decision}]`)) {
      button.onclick = async () => {
        try {
          const id = button.dataset[decision === 'approve' ? 'mvApprove' : 'mvReject'];
          const notes = container.querySelector(`[data-mv-notes="${id}"]`).value;
          await api(`/assets/${asset.id}/reference-sets/${id}/review`,{approved:decision === 'approve',notes},'PUT');
          await reload(asset.id); notify('View set review saved.');
        } catch (e) { notify(e.message,true); }
      };
    }
    generation.querySelectorAll('input,select').forEach(el => { el.disabled = !backend?.multi_view; });
    $('mv-generation-note').textContent = backend?.multi_view ? 'One shared mesh uses all selected views. Inspect its forward axis before projecting colors. More views increase inference time; compare geometry before game replacement.' : 'This backend supports one image. Choose TRELLIS to combine separate views.';
  }
  $('mv-create').onclick = async () => {
    try {
      const asset = current();
      const views = [...container.querySelectorAll('[data-mv-angle]')].filter(el => el.value).map(el => ({angle:el.dataset.mvAngle,reference_id:el.value}));
      await api(`/assets/${asset.id}/reference-sets`,{name:$('mv-name').value,source_reference_id:$('mv-authority').value,pose:$('mv-pose').value,scale_notes:$('mv-scale').value,views});
      await reload(asset.id); notify('View set saved. Open each view and record consistency before approval.');
    } catch (e) { notify(e.message,true); }
  };
  // Do not redraw the form on input changes; keep the user's selected set.
  $('mv-generation-set').onchange = () => onChange();
  return {render, options:() => ({reference_set_id:$('mv-generation-set').value || undefined}),
    settings:() => ({multiview_mode:$('mv-mode').value,trellis_steps:Number($('mv-steps').value),trellis_guidance:Number($('mv-guidance').value),project_reference_colors:$('mv-project-colors').checked}),
    selectedSet:() => $('mv-generation-set').value};
}
