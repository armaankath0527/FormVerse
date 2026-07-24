let currentResponses = [];

function statusBadge(status){ return '<span class="badge '+status+'">'+status+'</span>'; }

async function loadResponsesPage(){
  document.getElementById('responses-body').innerHTML = skeletonRows(4,6);
  try {
    const data = await api('/forms');
    const sel = document.getElementById('resp-form-select');
    const publishable = data.forms.filter(f=>f.status!=='draft');
    if (publishable.length === 0) {
      sel.innerHTML = '<option>No published forms</option>';
      document.getElementById('resp-count-label').textContent = '0 responses';
      document.getElementById('responses-body').innerHTML =
        '<tr><td colspan="6"><div class="empty-state"><h3>No published forms yet</h3><p>Publish a form to start collecting responses.</p></div></td></tr>';
      return;
    }
    sel.innerHTML = publishable.map(f=>'<option value="'+f.id+'">'+f.title+'</option>').join('');

    const params = new URLSearchParams(window.location.search);
    const preselect = params.get('form');
    if (preselect && publishable.some(f=>String(f.id)===preselect)) sel.value = preselect;

    await renderResponses();
  } catch (err) {
    document.getElementById('responses-body').innerHTML = '<tr><td colspan="6" style="color:var(--ink-soft);">'+err.message+'</td></tr>';
  }
}

function onFormChange(){ renderResponses(); }

async function renderResponses(){
  const formId = document.getElementById('resp-form-select').value;
  if (!formId) return;
  document.getElementById('responses-body').innerHTML = skeletonRows(4,6);
  try {
    const data = await api('/forms/'+formId+'/responses');
    currentResponses = data.responses;
    document.getElementById('resp-count-label').textContent = data.count + ' response' + (data.count===1?'':'s');
    renderFilteredResponses();
  } catch (err) {
    document.getElementById('responses-body').innerHTML = '<tr><td colspan="6" style="color:var(--ink-soft);">'+err.message+'</td></tr>';
  }
}

function renderFilteredResponses(){
  const q = (document.getElementById('resp-search').value || '').toLowerCase();
  let list = currentResponses;
  if (q) {
    list = list.filter(r => JSON.stringify(r.answers).toLowerCase().includes(q) || String(r.id).includes(q));
  }
  if (list.length === 0) {
    document.getElementById('responses-body').innerHTML =
      '<tr><td colspan="6"><div class="empty-state"><h3>No responses'+(q?' match your search':' yet')+'</h3></div></td></tr>';
    return;
  }
  document.getElementById('responses-body').innerHTML = list.map(r=>
    '<tr><td><input type="checkbox" class="resp-check" data-id="'+r.id+'"></td><td>Response #'+r.id+'</td><td>'+ (r.submittedAt||'').slice(0,16) +'</td>'+
    '<td>'+statusBadge(r.status==='flagged'?'draft':'published')+'</td>'+
    '<td>'+r.device+'</td>'+
    '<td><button class="btn btn-ghost btn-sm" onclick="viewResponseAction('+r.id+')">View</button>'+
    ' <button class="btn btn-ghost btn-sm" onclick="deleteResponseAction('+r.id+')" style="color:var(--red);">Delete</button></td></tr>'
  ).join('');
  document.querySelectorAll('.resp-check').forEach(cb => cb.addEventListener('change', updateBulkBar));
  updateBulkBar();
}

function toggleSelectAll(master){
  document.querySelectorAll('.resp-check').forEach(cb => cb.checked = master.checked);
  updateBulkBar();
}

function updateBulkBar(){
  const checked = document.querySelectorAll('.resp-check:checked').length;
  document.getElementById('bulk-bar').style.display = checked > 0 ? 'block' : 'none';
}

async function bulkDelete(){
  const ids = Array.from(document.querySelectorAll('.resp-check:checked')).map(cb => parseInt(cb.dataset.id));
  if (ids.length === 0) return;
  if (!confirm('Delete ' + ids.length + ' response(s)? This can\'t be undone.')) return;
  const formId = document.getElementById('resp-form-select').value;
  try {
    await api('/forms/'+formId+'/responses/bulk-delete', { method:'POST', body: JSON.stringify({ids}) });
    toast('Deleted ' + ids.length + ' response(s).', 'success');
    renderResponses();
  } catch (err) { /* toast shown */ }
}

async function viewResponseAction(id){
  try {
    const data = await api('/responses/'+id);
    const entries = Object.entries(data.response.answers);
    const lines = entries.length ? entries.map(([k,v])=>'• '+k+': '+v).join('\n') : '(no answers recorded)';
    alert('Response #'+id+' — submitted '+data.response.submittedAt+'\n\n'+lines);
  } catch (err) { /* toast shown */ }
}

async function deleteResponseAction(id){
  if (!confirm('Delete this response?')) return;
  try { await api('/responses/'+id, {method:'DELETE'}); toast('Response deleted.', 'success'); renderResponses(); }
  catch(err){ /* toast shown */ }
}

function exportResponses(fmt){
  const formId = document.getElementById('resp-form-select').value;
  if (!formId) return;
  if (fmt === 'xlsx') {
    toast('True .xlsx export needs an Excel-writing library not yet installed on the backend — exporting CSV instead (opens fine in Excel/Sheets).', 'error');
  }
  const url = '/api/forms/' + formId + '/responses/export?format=csv';
  fetch(url, { credentials: 'same-origin' })
    .then(res => { if(!res.ok) throw new Error('Export failed.'); return res.blob(); })
    .then(blob => {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'responses.csv';
      a.click();
      toast('Export downloaded.', 'success');
    })
    .catch(err => toast(err.message, 'error'));
}

document.addEventListener('DOMContentLoaded', loadResponsesPage);
