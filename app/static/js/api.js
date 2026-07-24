/* ============================================================
   Shared across every page — API calls, toasts, nav progress,
   theme (dark mode), and the share/QR modal.
   Auth is via the Flask session cookie (set at login/signup),
   so fetch() calls need no manual token handling.
   ============================================================ */

/* ---------- theme (dark mode) ---------- */
function applyTheme(theme){
  if (theme === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
  else document.documentElement.removeAttribute('data-theme');
  try { localStorage.setItem('formverse-theme', theme); } catch (e) { /* private browsing, etc. */ }
}
function currentTheme(){
  return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
}
function toggleTheme(){
  const next = currentTheme() === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  return next;
}
// Re-apply on every page load in case a page's own inline flash-guard script (see
// base templates) didn't run for some reason — cheap and idempotent.
(function(){
  try {
    const saved = localStorage.getItem('formverse-theme');
    if (saved === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
  } catch (e) {}
})();

/* ---------- share modal (link + QR code + embed snippet) ---------- */
function openShareModal(shareSlug, title){
  const link = window.location.origin + '/f/' + shareSlug;
  const qrUrl = 'https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=' + encodeURIComponent(link);
  const embedCode = '<iframe src="' + link + '" width="600" height="700" frameborder="0"></iframe>';

  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'share-modal-overlay';
  overlay.innerHTML =
    '<div class="modal-box">' +
      '<div class="modal-head"><h3>Share "' + escapeForAttr(title||'this form') + '"</h3>' +
      '<button class="modal-close-btn" onclick="closeShareModal()">✕</button></div>' +
      '<p class="modal-sub">Anyone with this link can fill out the form.</p>' +
      '<div class="share-link-row">' +
        '<input type="text" id="share-link-input" value="' + link + '" readonly onclick="this.select()">' +
        '<button class="btn btn-primary btn-sm" onclick="copyShareLink()">Copy</button>' +
      '</div>' +
      '<div class="qr-wrap"><img src="' + qrUrl + '" alt="QR code for this form" width="160" height="160"></div>' +
      '<div class="share-actions" style="margin-bottom:18px;">' +
        '<a class="btn btn-outline btn-sm btn-block" href="' + qrUrl + '" download="form-qr-code.png" target="_blank" rel="noopener">Download QR code</a>' +
        '<a class="btn btn-outline btn-sm btn-block" href="' + link + '" target="_blank" rel="noopener">Open form</a>' +
      '</div>' +
      '<label class="small-label">Embed code</label>' +
      '<textarea class="embed-box" rows="2" readonly onclick="this.select()">' + embedCode + '</textarea>' +
      '<button class="btn btn-ghost btn-sm" style="width:100%;justify-content:center;" onclick="copyEmbedCode()">Copy embed code</button>' +
      (window.location.pathname.startsWith('/app/builder') ?
        '<a class="btn btn-ghost btn-sm" style="width:100%;justify-content:center;margin-top:4px;" href="/app/forms">← Back to my forms</a>' : '') +
    '</div>';
  document.body.appendChild(overlay);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeShareModal(); });
}
function closeShareModal(){
  const overlay = document.getElementById('share-modal-overlay');
  if (overlay) overlay.remove();
}
function copyShareLink(){
  const input = document.getElementById('share-link-input');
  input.select();
  copyViaClipboardAPI(input.value);
  toast('Link copied.', 'success');
}
function copyEmbedCode(){
  const box = document.querySelector('.embed-box');
  box.select();
  copyViaClipboardAPI(box.value);
  toast('Embed code copied.', 'success');
}
function copyViaClipboardAPI(text){
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).catch(()=>{ try { document.execCommand('copy'); } catch(e){} });
  } else {
    try { document.execCommand('copy'); } catch(e){}
  }
}
function escapeForAttr(s){ return String(s).replace(/"/g,'&quot;'); }

function showProgress(){
  let bar = document.getElementById('nav-progress');
  if (!bar) {
    bar = document.createElement('div');
    bar.id = 'nav-progress';
    document.body.appendChild(bar);
  }
  bar.classList.add('active');
  bar.style.width = '70%';
  return bar;
}
function hideProgress(){
  const bar = document.getElementById('nav-progress');
  if (!bar) return;
  bar.style.width = '100%';
  setTimeout(()=>{ bar.classList.remove('active'); bar.style.width='0%'; }, 250);
}

function toast(message, type){
  let stack = document.getElementById('toast-stack');
  if (!stack) {
    stack = document.createElement('div');
    stack.id = 'toast-stack';
    document.body.appendChild(stack);
  }
  const el = document.createElement('div');
  el.className = 'toast' + (type ? ' '+type : '');
  el.textContent = message;
  stack.appendChild(el);
  setTimeout(()=>{ el.style.opacity='0'; el.style.transition='opacity .25s'; setTimeout(()=>el.remove(), 260); }, 3400);
}

async function api(path, options = {}) {
  const headers = Object.assign({ 'Content-Type': 'application/json' }, options.headers || {});
  const bar = showProgress();
  let res;
  try {
    res = await fetch('/api' + path, Object.assign({}, options, { headers, credentials: 'same-origin' }));
  } catch (err) {
    hideProgress();
    toast('Network error — is the server running?', 'error');
    throw err;
  }
  hideProgress();
  let data = {};
  try { data = await res.json(); } catch (e) { /* empty body, fine */ }
  if (res.status === 401) {
    window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
    throw new Error('Session expired');
  }
  if (!res.ok) {
    const msg = data.error || ('Request failed (' + res.status + ')');
    toast(msg, 'error');
    throw new Error(msg);
  }
  return data;
}

function skeletonRows(n, cols){
  let rows = '';
  for (let i=0;i<n;i++){
    rows += '<tr>' + Array.from({length: cols}).map(()=>'<td><div class="skeleton" style="height:14px;width:'+(60+Math.random()*30)+'%;"></div></td>').join('') + '</tr>';
  }
  return rows;
}

// Fade the pointer/scrollbar in gently and mark active sidebar link from the current URL.
document.addEventListener('DOMContentLoaded', () => {
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar .nav-item').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
});
