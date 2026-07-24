let formFields = [];
let fieldCounter = 0;
let selectedFieldId = null;
let currentFormId = typeof EXISTING_FORM_ID !== 'undefined' ? EXISTING_FORM_ID : null;
const formMeta = {title:'Untitled form', desc:''};

const FIELD_LABELS = {
  short:'Short text', long:'Long text', email:'Email address', number:'Number', phone:'Phone number',
  url:'Website URL', dropdown:'Choose an option', checkbox:'Select all that apply', radio:'Choose one',
  multiple:'Multiple choice', yesno:'Yes or no?', date:'Select a date', time:'Select a time',
  file:'Upload a file', rating:'Rate your experience', heading:'Section heading', paragraph:'Add supporting text here.', divider:'Section'
};
const LAYOUT_TYPES = ['heading','paragraph','divider'];
const OPTION_TYPES = ['dropdown','checkbox','radio','multiple'];

async function initBuilder(){
  if (currentFormId) {
    try {
      const data = await api('/forms/' + currentFormId);
      formMeta.title = data.form.title;
      formMeta.desc = data.form.description || '';
      formFields = data.form.fields.map(f => {
        fieldCounter++;
        return {
          id: 'fld_' + fieldCounter, serverId: f.id, type: f.type, label: f.label,
          required: f.required, placeholder: f.placeholder || '', help: f.helpText || '',
          charLimit: f.charLimit || '', options: f.options && f.options.length ? f.options : ['Option A','Option B','Option C']
        };
      });
    } catch (err) { /* toast already shown */ }
  }
  document.getElementById('form-title-input').value = formMeta.title;
  document.getElementById('form-desc-input').value = formMeta.desc;
  renderCanvas();
  renderInspector();
}

/* ---------- drag & drop ---------- */
function dragStart(e){ e.dataTransfer.setData('text/type', e.target.closest('.pal-item').dataset.type); }
function dragOver(e){ e.preventDefault(); document.getElementById('dropzone').classList.add('dragover'); }
function dragLeave(e){ document.getElementById('dropzone').classList.remove('dragover'); }
function dropField(e){
  e.preventDefault();
  document.getElementById('dropzone').classList.remove('dragover');
  const type = e.dataTransfer.getData('text/type');
  if(!type) return;
  addField(type);
}

function addField(type){
  fieldCounter++;
  formFields.push({
    id:'fld_'+fieldCounter, type:type, label: FIELD_LABELS[type] || 'Untitled field',
    required:false, placeholder:'', help:'', charLimit:'',
    options: OPTION_TYPES.includes(type) ? ['Option A','Option B','Option C'] : []
  });
  selectedFieldId = formFields[formFields.length-1].id;
  renderCanvas();
  renderInspector();
}

function duplicateField(id){
  const f = formFields.find(x=>x.id===id);
  if(!f) return;
  fieldCounter++;
  const copy = {...f, id:'fld_'+fieldCounter, serverId:undefined, label:f.label+' (copy)', options:[...(f.options||[])]};
  const idx = formFields.findIndex(x=>x.id===id);
  formFields.splice(idx+1,0,copy);
  selectedFieldId = copy.id;
  renderCanvas(); renderInspector();
}

function deleteField(id){
  formFields = formFields.filter(f=>f.id!==id);
  if(selectedFieldId===id) selectedFieldId=null;
  renderCanvas(); renderInspector();
}

function moveField(id, dir){
  const idx = formFields.findIndex(f=>f.id===id);
  const newIdx = idx+dir;
  if(newIdx<0 || newIdx>=formFields.length) return;
  [formFields[idx], formFields[newIdx]] = [formFields[newIdx], formFields[idx]];
  renderCanvas();
}

function selectField(id){ selectedFieldId = id; renderCanvas(); renderInspector(); }

function fieldPreviewHTML(f){
  switch(f.type){
    case 'long': return '<div class="fake-input" style="height:44px;">'+ (f.placeholder||'Long answer text') +'</div>';
    case 'dropdown': return '<div class="fake-input">▾ '+(f.options[0]||'Select...')+'</div>';
    case 'checkbox': return '<div style="margin-top:4px;">'+ f.options.map(o=>'☐ '+escapeHtml(o)).join(' &nbsp; ') +'</div>';
    case 'radio': case 'multiple': return '<div style="margin-top:4px;">'+ f.options.map(o=>'○ '+escapeHtml(o)).join(' &nbsp; ') +'</div>';
    case 'yesno': return '<div style="margin-top:4px;">○ Yes &nbsp; ○ No</div>';
    case 'date': return '<div class="fake-input">📅 mm/dd/yyyy</div>';
    case 'time': return '<div class="fake-input">🕐 --:-- --</div>';
    case 'file': return '<div class="fake-input">⬆ Click or drag to upload</div>';
    case 'rating': return '<div style="margin-top:4px;font-size:16px;">☆ ☆ ☆ ☆ ☆</div>';
    case 'heading': case 'paragraph': return '';
    case 'divider': return '<div style="border-top:1.5px dashed var(--paper-line);margin-top:6px;"></div>';
    default: return '<div class="fake-input">'+(f.placeholder||'Your answer')+'</div>';
  }
}

function escapeHtml(s){ return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function renderCanvas(){
  const dz = document.getElementById('dropzone');
  if(formFields.length===0){
    dz.innerHTML = '<div class="empty-hint" id="empty-hint">Drag a field here to start building →</div>';
    return;
  }
  dz.innerHTML = formFields.map((f)=>{
    const isLayout = LAYOUT_TYPES.includes(f.type);
    const labelHTML = f.type==='heading'
      ? '<div class="flabel" style="font-family:var(--font-display);font-size:18px;">'+escapeHtml(f.label)+'</div>'
      : f.type==='paragraph'
        ? '<div class="fpreview">'+escapeHtml(f.label)+'</div>'
        : f.type==='divider'
          ? '<div class="flabel" style="color:var(--ink-soft);font-size:12px;font-family:var(--font-mono);text-transform:uppercase;">'+escapeHtml(f.label)+'</div>'
          : '<div class="flabel"><span class="ftype">'+f.type+'</span>'+escapeHtml(f.label)+(f.required?' <span class="req">*</span>':'')+'</div>';
    return '<div class="f-item'+(selectedFieldId===f.id?' selected':'')+'" onclick="selectField(\''+f.id+'\')">'+
      '<div class="f-item-actions">'+
        '<button onclick="event.stopPropagation();moveField(\''+f.id+'\',-1)" title="Move up">↑</button>'+
        '<button onclick="event.stopPropagation();moveField(\''+f.id+'\',1)" title="Move down">↓</button>'+
        '<button onclick="event.stopPropagation();duplicateField(\''+f.id+'\')" title="Duplicate">⧉</button>'+
        '<button onclick="event.stopPropagation();deleteField(\''+f.id+'\')" title="Delete">✕</button>'+
      '</div>'+
      '<div class="f-item-head">'+labelHTML+'</div>'+
      (isLayout ? '' : '<div class="fpreview">'+fieldPreviewHTML(f)+'</div>')+
    '</div>';
  }).join('');
}

function renderInspector(){
  const f = formFields.find(x=>x.id===selectedFieldId);
  const empty = document.getElementById('inspector-empty');
  const body = document.getElementById('inspector-body');
  if(!f){ empty.style.display='block'; body.style.display='none'; return; }
  empty.style.display='none'; body.style.display='block';
  const isLayout = LAYOUT_TYPES.includes(f.type);
  const hasOptions = OPTION_TYPES.includes(f.type);

  let html =
    '<div class="field"><label>Field label</label><input type="text" value="'+escapeHtml(f.label)+'" oninput="updateField(\''+f.id+'\',\'label\',this.value)"></div>';

  if (hasOptions) {
    html += '<div class="field"><label>Options</label><div id="opt-editor">' +
      f.options.map((o,i) => optRowHTML(f.id, i, o)).join('') +
      '</div><button type="button" class="add-opt-btn" onclick="addOption(\''+f.id+'\')">+ Add option</button></div>';
  }

  if (!isLayout) {
    html +=
      '<div class="field"><label>Placeholder text</label><input type="text" value="'+escapeHtml(f.placeholder)+'" oninput="updateField(\''+f.id+'\',\'placeholder\',this.value)"></div>'+
      '<div class="field"><label>Help text</label><input type="text" value="'+escapeHtml(f.help)+'" oninput="updateField(\''+f.id+'\',\'help\',this.value)"></div>'+
      '<div class="field"><label>Character limit <span class="hint">(optional)</span></label><input type="number" value="'+(f.charLimit||'')+'" oninput="updateField(\''+f.id+'\',\'charLimit\',this.value)"></div>'+
      '<div class="toggle-row">Required field<div class="switch'+(f.required?' on':'')+'" onclick="toggleRequired(\''+f.id+'\')"></div></div>';
  }
  body.innerHTML = html;
}

function optRowHTML(fieldId, idx, value){
  return '<div class="opt-row">'+
    '<input type="text" value="'+escapeHtml(value)+'" oninput="updateOption(\''+fieldId+'\','+idx+',this.value)">'+
    '<button type="button" onclick="removeOption(\''+fieldId+'\','+idx+')" title="Remove">✕</button>'+
  '</div>';
}

function addOption(fieldId){
  const f = formFields.find(x=>x.id===fieldId);
  f.options.push('Option ' + (f.options.length + 1));
  renderInspector(); renderCanvas();
}
function updateOption(fieldId, idx, val){
  const f = formFields.find(x=>x.id===fieldId);
  f.options[idx] = val;
  renderCanvas();
}
function removeOption(fieldId, idx){
  const f = formFields.find(x=>x.id===fieldId);
  if (f.options.length <= 1) { toast('A choice field needs at least one option.', 'error'); return; }
  f.options.splice(idx,1);
  renderInspector(); renderCanvas();
}

function updateField(id, key, val){
  const f = formFields.find(x=>x.id===id);
  if(!f) return;
  f[key]=val;
  renderCanvas();
}

function toggleRequired(id){
  const f = formFields.find(x=>x.id===id);
  f.required = !f.required;
  renderCanvas(); renderInspector();
}

function setBuilderTab(tab){
  document.getElementById('btab-build').classList.toggle('active', tab==='build');
  document.getElementById('btab-preview').classList.toggle('active', tab==='preview');
  document.querySelector('.palette').style.display = tab==='build' ? 'block':'none';
  document.getElementById('inspector').style.display = tab==='build' ? 'block':'none';
}

function serializeFields(){
  return formFields.map(f => ({
    type: f.type, label: f.label, required: !!f.required,
    placeholder: f.placeholder || '', helpText: f.help || '',
    charLimit: f.charLimit ? parseInt(f.charLimit) : null,
    options: OPTION_TYPES.includes(f.type) ? f.options : []
  }));
}

async function saveDraft(){
  const btn = document.getElementById('save-draft-btn');
  btn.disabled = true; const original = btn.textContent; btn.textContent = 'Saving…';
  const payload = { title: formMeta.title, description: formMeta.desc, fields: serializeFields() };
  try {
    if (currentFormId) {
      await api('/forms/'+currentFormId, { method:'PUT', body: JSON.stringify(payload) });
    } else {
      const data = await api('/forms', { method:'POST', body: JSON.stringify(payload) });
      currentFormId = data.form.id;
      window.history.replaceState({}, '', '/app/builder/'+currentFormId);
    }
    toast('Draft saved.', 'success');
  } catch (err) { /* toast shown */ }
  finally { btn.disabled = false; btn.textContent = original; }
}

async function publishForm(){
  const btn = document.getElementById('publish-btn');
  if (formFields.length === 0) { toast('Add at least one field before publishing.', 'error'); return; }
  btn.disabled = true; const original = btn.textContent; btn.textContent = 'Publishing…';
  const payload = { title: formMeta.title, description: formMeta.desc, fields: serializeFields() };
  try {
    if (currentFormId) {
      await api('/forms/'+currentFormId, { method:'PUT', body: JSON.stringify(payload) });
    } else {
      const data = await api('/forms', { method:'POST', body: JSON.stringify(payload) });
      currentFormId = data.form.id;
    }
    const pub = await api('/forms/'+currentFormId+'/publish', { method:'POST' });
    toast('Published!', 'success');
    openShareModal(pub.form.shareSlug, formMeta.title);
  } catch (err) { /* toast shown */ }
  finally { btn.disabled = false; btn.textContent = original; }
}

document.addEventListener('DOMContentLoaded', initBuilder);
