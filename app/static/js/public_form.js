let PF_FIELDS = [];

function pfEscape(s){ return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); }

function pfFieldHTML(f){
  const reqStar = f.required ? ' <span class="req">*</span>' : '';
  const help = f.helpText ? '<div class="pf-help">'+pfEscape(f.helpText)+'</div>' : '';
  const name = 'field_' + f.id;

  switch(f.type){
    case 'heading':
      return '<div class="pf-heading">'+pfEscape(f.label)+'</div>';
    case 'paragraph':
      return '<div class="pf-paragraph">'+pfEscape(f.label)+'</div>';
    case 'divider':
      return '<div class="pf-divider"></div>';
    case 'long':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><textarea name="'+name+'" rows="4" placeholder="'+pfEscape(f.placeholder)+'"'+(f.charLimit?' maxlength="'+f.charLimit+'"':'')+'></textarea>'+help+'</div>';
    case 'email':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="email" name="'+name+'" placeholder="'+pfEscape(f.placeholder||'you@example.com')+'">'+help+'</div>';
    case 'number':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="number" name="'+name+'" placeholder="'+pfEscape(f.placeholder)+'">'+help+'</div>';
    case 'phone':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="tel" name="'+name+'" placeholder="'+pfEscape(f.placeholder||'(555) 555-5555')+'">'+help+'</div>';
    case 'url':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="url" name="'+name+'" placeholder="'+pfEscape(f.placeholder||'https://')+'">'+help+'</div>';
    case 'date':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="date" name="'+name+'">'+help+'</div>';
    case 'time':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="time" name="'+name+'">'+help+'</div>';
    case 'file':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="file" name="'+name+'">'+help+'</div>';
    case 'dropdown':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><select name="'+name+'"><option value="">Select...</option>'+
        (f.options||[]).map(o=>'<option value="'+pfEscape(o)+'">'+pfEscape(o)+'</option>').join('')+'</select>'+help+'</div>';
    case 'checkbox':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label>'+
        (f.options||[]).map((o,i)=>'<div class="pf-choice-row"><input type="checkbox" name="'+name+'" value="'+pfEscape(o)+'" id="'+name+'_'+i+'"><label for="'+name+'_'+i+'" style="font-weight:400;margin:0;">'+pfEscape(o)+'</label></div>').join('')+help+'</div>';
    case 'radio': case 'multiple':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label>'+
        (f.options||[]).map((o,i)=>'<div class="pf-choice-row"><input type="radio" name="'+name+'" value="'+pfEscape(o)+'" id="'+name+'_'+i+'"><label for="'+name+'_'+i+'" style="font-weight:400;margin:0;">'+pfEscape(o)+'</label></div>').join('')+help+'</div>';
    case 'yesno':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label>'+
        '<div class="pf-choice-row"><input type="radio" name="'+name+'" value="Yes" id="'+name+'_y"><label for="'+name+'_y" style="font-weight:400;margin:0;">Yes</label></div>'+
        '<div class="pf-choice-row"><input type="radio" name="'+name+'" value="No" id="'+name+'_n"><label for="'+name+'_n" style="font-weight:400;margin:0;">No</label></div>'+help+'</div>';
    case 'rating':
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label>'+
        '<div class="pf-rating" data-name="'+name+'">'+[1,2,3,4,5].map(n=>'<span data-val="'+n+'" onclick="pfSetRating(this)">★</span>').join('')+'</div>'+
        '<input type="hidden" name="'+name+'">'+help+'</div>';
    default: // short
      return '<div class="pf-field"><label>'+pfEscape(f.label)+reqStar+'</label><input type="text" name="'+name+'" placeholder="'+pfEscape(f.placeholder)+'"'+(f.charLimit?' maxlength="'+f.charLimit+'"':'')+'>'+help+'</div>';
  }
}

function pfSetRating(el){
  const wrap = el.parentElement;
  const val = parseInt(el.dataset.val);
  Array.from(wrap.children).forEach(s => s.classList.toggle('on', parseInt(s.dataset.val) <= val));
  wrap.nextElementSibling.value = val;
}

async function loadPublicForm(){
  const card = document.getElementById('pf-card');
  try {
    const res = await fetch('/api/public/forms/' + SHARE_SLUG + '?device=' + (window.innerWidth < 700 ? 'Mobile' : 'Desktop'));
    const data = await res.json();
    if (!res.ok) {
      card.innerHTML = '<div class="pf-done"><h2>Form unavailable</h2><p style="color:var(--ink-soft);">'+ (data.error||'This form could not be found.') +'</p></div>';
      return;
    }
    PF_FIELDS = data.form.fields;
    card.innerHTML =
      '<h1>'+pfEscape(data.form.title)+'</h1>' +
      (data.form.description ? '<p class="pf-desc">'+pfEscape(data.form.description)+'</p>' : '') +
      '<form id="pf-form">' + PF_FIELDS.map(pfFieldHTML).join('') +
      '<button type="submit" class="btn btn-primary btn-block" id="pf-submit-btn">Submit</button></form>';
    document.getElementById('pf-form').addEventListener('submit', submitPublicForm);
  } catch (err) {
    card.innerHTML = '<div class="pf-done"><h2>Couldn\'t load this form</h2><p style="color:var(--ink-soft);">Check your connection and try again.</p></div>';
  }
}

async function submitPublicForm(e){
  e.preventDefault();
  const btn = document.getElementById('pf-submit-btn');
  btn.disabled = true; btn.textContent = 'Submitting…';
  const form = e.target;
  const answers = {};
  PF_FIELDS.forEach(f => {
    if (['heading','paragraph','divider'].includes(f.type)) return;
    const name = 'field_' + f.id;
    if (f.type === 'checkbox') {
      answers[f.id] = Array.from(form.querySelectorAll('[name="'+name+'"]:checked')).map(el => el.value);
    } else if (f.type === 'radio' || f.type === 'multiple' || f.type === 'yesno') {
      const checked = form.querySelector('[name="'+name+'"]:checked');
      answers[f.id] = checked ? checked.value : '';
    } else if (f.type === 'file') {
      const el = form.querySelector('[name="'+name+'"]');
      answers[f.id] = el && el.files.length ? el.files[0].name : '';
    } else {
      const el = form.querySelector('[name="'+name+'"]');
      answers[f.id] = el ? el.value : '';
    }
  });

  try {
    const res = await fetch('/api/public/forms/' + SHARE_SLUG + '/submit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ answers, device: window.innerWidth < 700 ? 'Mobile' : 'Desktop' }),
    });
    const data = await res.json();
    if (!res.ok) {
      toast(data.error || 'Please check the required fields.', 'error');
      btn.disabled = false; btn.textContent = 'Submit';
      return;
    }
    document.getElementById('pf-card').innerHTML =
      '<div class="pf-done"><h2>Thanks — your response was recorded.</h2><p style="color:var(--ink-soft);">You can close this page now.</p></div>';
  } catch (err) {
    toast('Network error — please try again.', 'error');
    btn.disabled = false; btn.textContent = 'Submit';
  }
}

document.addEventListener('DOMContentLoaded', loadPublicForm);
