// app.js

// Utility: get cookie (for CSRF fetch)
function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(';').shift();
  return null;
}

// Example: mark all notifications read (dashboard page)
async function markAllRead() {
  try {
    const resp = await fetch('/api/notifications/mark_all_read/', {
      method: 'POST',
      headers: {
        'X-CSRFToken': getCookie('csrftoken'),
      },
    });
    if (resp.ok) {
      location.reload();
    }
  } catch (err) {
    console.error('Failed to mark all read', err);
  }
}

// Attach events
document.addEventListener('DOMContentLoaded', () => {
  const btn = document.getElementById('markAll');
  if (btn) {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      markAllRead();
    });
  }

  // Example: theme toggle
  const themeToggle = document.getElementById('themeToggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      document.body.classList.toggle('dark-mode');
    });
  }
});

