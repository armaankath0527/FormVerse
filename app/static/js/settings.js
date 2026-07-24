function handleThemeToggle(){
  const next = toggleTheme();
  document.getElementById('dark-mode-switch').classList.toggle('on', next === 'dark');
  toast(next === 'dark' ? 'Dark mode on.' : 'Dark mode off.', 'success');
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('dark-mode-switch').classList.toggle('on', currentTheme() === 'dark');
});

async function saveProfile(){
  const name = document.getElementById('profile-name').value.trim();
  if (!name) { toast('Name can\'t be empty.', 'error'); return; }
  try {
    await api('/auth/me', { method:'PATCH', body: JSON.stringify({ name }) });
    toast('Profile updated.', 'success');
  } catch (err) { /* toast shown */ }
}

async function changePassword(){
  const currentPassword = document.getElementById('current-password').value;
  const newPassword = document.getElementById('new-password').value;
  if (newPassword.length < 8) { toast('New password must be at least 8 characters.', 'error'); return; }
  try {
    await api('/auth/change-password', { method:'POST', body: JSON.stringify({ currentPassword, newPassword }) });
    toast('Password changed.', 'success');
    document.getElementById('current-password').value = '';
    document.getElementById('new-password').value = '';
  } catch (err) { /* toast shown */ }
}

async function deleteAccount(){
  if (!confirm('This permanently deletes your account, forms, and responses. Continue?')) return;
  try {
    await api('/auth/me', { method:'DELETE' });
    window.location.href = '/';
  } catch (err) { /* toast shown */ }
}
