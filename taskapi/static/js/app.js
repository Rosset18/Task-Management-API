// CSRF
function getCookie(name) {
  const v = `; ${document.cookie}`.split(`; ${name}=`);
  if (v.length === 2) return v.pop().split(";").shift();
  return null;
}

// Toasts
function showToast(text, ms = 3200) {
  const root = document.getElementById("toast-container");
  if (!root) return;
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = text;
  root.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => { t.classList.remove("show"); setTimeout(() => t.remove(), 250); }, ms);
}

// Django messages → toasts
if (window.__django_messages__ && Array.isArray(window.__django_messages__)) {
  window.__django_messages__.forEach(m => showToast(m.text));
}

// Dashboard: complete + delete
document.addEventListener("click", (e) => {
  // Complete
  const completeBtn = e.target.closest("[data-complete-task]");
  if (completeBtn) {
    e.preventDefault();
    const id = completeBtn.getAttribute("data-complete-task");
    fetch(`/tasks/${id}/complete/`, {
      method: "POST",
      headers: { "X-CSRFToken": getCookie("csrftoken") }
    }).then(r => {
      if (r.ok) { showToast("Task completed"); location.reload(); }
      else showToast("Could not complete task");
    }).catch(() => showToast("Network error"));
  }

  // Delete
  const delBtn = e.target.closest("[data-delete-task]");
  if (delBtn) {
    // The button lives inside a form; let the form submit normally unless JS intercepted:
    if (!confirm("Delete this task?")) { e.preventDefault(); }
  }
});

// Pomodoro
(function(){
  const wrap = document.getElementById("pomodoro");
  if (!wrap) return;
  const display = document.getElementById("pomo-display");
  const start = document.getElementById("pomo-start");
  const stop = document.getElementById("pomo-stop");
  const reset = document.getElementById("pomo-reset");
  const mins = parseInt(wrap.dataset.min || "25", 10);
  let left = mins*60, timer=null;

  function render(){
    const m = String(Math.floor(left/60)).padStart(2,"0");
    const s = String(left%60).padStart(2,"0");
    display.textContent = `${m}:${s}`;
  }
  render();

  start.addEventListener("click", ()=>{
    if (timer) return;
    timer = setInterval(()=>{
      left -= 1;
      if (left <= 0) {
        clearInterval(timer); timer=null; left=0; render(); showToast("Pomodoro done!");
      } else render();
    }, 1000);
  });
  stop.addEventListener("click", ()=>{ if (timer){ clearInterval(timer); timer=null; }});
  reset.addEventListener("click", ()=>{ if (timer){ clearInterval(timer); timer=null; } left=mins*60; render(); });
})();

