/* Balaji OS — main.js */

// ── Sidebar collapse toggle ───────────────────────
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');

if (sidebarToggle && sidebar) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
  });
  // Restore state
  if (localStorage.getItem('sidebarCollapsed') === 'true') {
    sidebar.classList.add('collapsed');
  }
}

// ── Task toggle (checkbox click) ─────────────────
function toggleTask(taskId, btn) {
  const csrfToken = window.CSRF_TOKEN || document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
  fetch(`/api/toggle-task/${taskId}/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
  })
  .then(r => r.json())
  .then(data => {
    const item = btn ? btn.closest('.task-item') : document.querySelector(`[data-task-id="${taskId}"]`);
    if (item) {
      item.classList.toggle('completed', data.completed);
    }
  })
  .catch(err => console.error('Toggle task failed:', err));
}

// ── Focus mode toggle ─────────────────────────────
const focusToggle = document.getElementById('focusToggle');
if (focusToggle) {
  focusToggle.addEventListener('click', () => {
    const csrfToken = window.CSRF_TOKEN || document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '';
    fetch('/api/toggle-focus/', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken },
    })
    .then(r => r.json())
    .then(data => {
      focusToggle.classList.toggle('on', data.focus_mode);
      const statusEl = focusToggle.nextElementSibling;
      if (statusEl) statusEl.textContent = data.focus_mode ? 'On' : 'Off';
    })
    .catch(err => console.error('Focus toggle failed:', err));
  });
}

// ── Animate bar chart bars on load ───────────────
document.addEventListener('DOMContentLoaded', () => {
  const bars = document.querySelectorAll('.bar');
  bars.forEach(bar => {
    const target = bar.style.height;
    bar.style.height = '0%';
    requestAnimationFrame(() => {
      setTimeout(() => { bar.style.height = target; }, 60);
    });
  });
});
