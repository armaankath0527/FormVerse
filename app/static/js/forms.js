let allFormsCache = [];

function statusBadge(status){ return '<span class="badge '+status+'">'+status+'</span>'; }

async function loadForms(){
  try {
    const data = await api('/forms');
    allFormsCache = data.forms;
    renderFormsGrid(allFormsCache);
  } catch (err) {
    document.getElementById('forms-grid').innerHTML = '<p style="color:var(--ink-soft);grid-column:1/-1;">Couldn\'t load forms. '+err.message+'</p>';
  }
}

function renderFormsGrid(list){
  const grid = document.getElementById('forms-grid');
  if(list.length===0){
    grid.innerHTML = '<div class="empty-state" style="grid-column:1/-1;"><h3>No forms yet</h3><p>Start from scratch — it only takes a minute.</p><a class="btn btn-primary" href="/app/builder" style="margin-top:14px;display:inline-flex;">+ New form</a></div>';
    return;
  }
  grid.innerHTML = list.map(f=>
    '<div class="form-card">'+
      '<div class="fc-top"><div><h4>'+f.title+'</h4><div class="fc-meta">Edited '+ (f.updatedAt||'').slice(0,16) +'</div></div>'+statusBadge(f.status)+'</div>'+
      '<div class="fc-stats"><span>👁 '+f.viewCount+' views</span><span>📥 '+f.responseCount+' responses</span></div>'+
      '<div class="fc-actions">'+
        '<a class="btn btn-outline btn-sm" href="/app/builder/'+f.id+'">Edit</a>'+
        (f.status==='published' ? '<button class="btn btn-outline btn-sm" onclick="openShareModal(\''+f.shareSlug+'\', \''+f.title.replace(/'/g,"\\'")+'\')">Share</button>' : '')+
        '<a class="btn btn-ghost btn-sm" href="/app/responses?form='+f.id+'">Responses</a>'+
        '<button class="btn btn-ghost btn-sm" onclick="duplicateFormAction('+f.id+')">Duplicate</button>'+
        '<button class="btn btn-ghost btn-sm" onclick="deleteFormAction('+f.id+', this)" style="color:var(--red);">Delete</button>'+
      '</div>'+
    '</div>'
  ).join('');
}

function filterForms(q){
  q = q.toLowerCase();
  renderFormsGrid(allFormsCache.filter(f=>f.title.toLowerCase().includes(q)));
}

function sortForms(key){
  let list = [...allFormsCache];
  if(key==='name') list.sort((a,b)=>a.title.localeCompare(b.title));
  if(key==='responses') list.sort((a,b)=>b.responseCount-a.responseCount);
  renderFormsGrid(list);
}

async function duplicateFormAction(id){
  try { await api('/forms/'+id+'/duplicate', {method:'POST'}); toast('Form duplicated.', 'success'); loadForms(); }
  catch(err){ /* toast already shown by api() */ }
}

async function deleteFormAction(id, btn){
  if (!confirm('Delete this form and all its responses? This can\'t be undone.')) return;
  btn.closest('.form-card').style.opacity = '0.4';
  try { await api('/forms/'+id, {method:'DELETE'}); toast('Form deleted.', 'success'); loadForms(); }
  catch(err){ loadForms(); }
}

document.addEventListener('DOMContentLoaded', () => {
  loadForms();
  // Respect ?q= for deep-linkable searches
  const params = new URLSearchParams(window.location.search);
  if (params.get('q')) document.getElementById('forms-search').value = params.get('q');
});
