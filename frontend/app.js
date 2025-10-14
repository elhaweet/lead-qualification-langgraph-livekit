const statusEl = document.getElementById('status');
const numbersEl = document.getElementById('numbers');
const runBadge = document.getElementById('runBadge');
const startBtn = document.getElementById('startBtn');
const statTotal = document.getElementById('statTotal');
const statCompleted = document.getElementById('statCompleted');
const statFailed = document.getElementById('statFailed');
const bar = document.getElementById('bar');
// New chip elements
const chipTotal = document.getElementById('chipTotal');
const chipCompleted = document.getElementById('chipCompleted');
const chipFailed = document.getElementById('chipFailed');

function createToast(message, type = 'success') {
  const container = document.getElementById('toasts');
  if (!container) return;
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = message;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

async function refresh() {
  const r = await fetch('/status');
  const s = await r.json();
  const pct = s.total ? Math.round(((s.completed.length) / s.total) * 100) : 0;

  // badge state
  runBadge.textContent = s.running ? 'Running' : 'Idle';
  runBadge.className = 'badge ' + (s.running ? 'running' : 'idle');
  if (startBtn) {
    startBtn.disabled = !!s.running;
    startBtn.textContent = s.running ? 'Running…' : 'Start Campaign';
  }

  // stats + progress
  statTotal.textContent = s.total || 0;
  statCompleted.textContent = s.completed?.length || 0;
  statFailed.textContent = s.failed?.length || 0;
  // mirror in chips
  if (chipTotal) chipTotal.textContent = statTotal.textContent;
  if (chipCompleted) chipCompleted.textContent = statCompleted.textContent;
  if (chipFailed) chipFailed.textContent = statFailed.textContent;

  bar.style.width = pct + '%';
  bar.classList.toggle('active', !!s.running);

  const pendingPills = (s.pending || []).map(n => `<span class="pill pending">${n}</span>`).join(' ');
  const completedPills = (s.completed || []).map(n => `<span class="pill done">${n}</span>`).join(' ');
  const failedPills = (s.failed || []).map(n => `<span class="pill failed">${n}</span>`).join(' ');

  statusEl.innerHTML = `
    <table>
      <tr><th>In Progress</th><th>Progress</th></tr>
      <tr>
        <td>${s.in_progress ? `<span class="pill running">${s.in_progress}</span>` : '-'}</td>
        <td>${pct}%</td>
      </tr>
    </table>
    <table>
      <tr><th>Pending</th><th>Completed</th><th>Failed</th></tr>
      <tr>
        <td class="list">${pendingPills || '-'}</td>
        <td class="list">${completedPills || '-'}</td>
        <td class="list">${failedPills || '-'}</td>
      </tr>
    </table>
  `;

  const allSet = new Set([...(s.pending || []), ...(s.completed || []), ...(s.failed || []), ...(s.in_progress ? [s.in_progress] : [])]);
  const items = Array.from(allSet).map(n => {
    let cls = 'pending';
    if (s.in_progress === n) cls = 'running';
    else if (s.completed?.includes(n)) cls = 'done';
    else if (s.failed?.includes(n)) cls = 'failed';
    return `<span class="pill ${cls}">${n}</span>`;
  });
  numbersEl.innerHTML = items.join(' ') || '-';
  numbersEl.classList.toggle('loading', !!s.running);
}

document.getElementById('uploadForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const fileInput = document.getElementById('fileInput');
  if (!fileInput.files.length) return;
  startBtn.disabled = true;
  startBtn.textContent = 'Starting…';
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  try {
    const resp = await fetch('/upload', { method: 'POST', body: fd });
    if (!resp.ok) throw new Error('Upload failed');
    const data = await resp.json().catch(() => ({ total: 0 }));
    createToast(`Campaign started for ${data.total ?? 0} numbers`, 'success');
    await refresh();
  } catch (err) {
    startBtn.disabled = false;
    startBtn.textContent = 'Start Campaign';
    createToast('Upload failed. Please check your CSV.', 'error');
  }
});

setInterval(refresh, 2000);
refresh();

// Theme logic: apply, persist, and toggle
const THEME_KEY = "theme";

function getInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") return saved;
  // Prefer dark by default; you could detect media here if desired
  return "dark";
}

function applyTheme(theme) {
  const root = document.documentElement;
  root.setAttribute("data-theme", theme);

  // Update theme-color for better mobile address bar coloring
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) meta.setAttribute("content", theme === "light" ? "#ffffff" : "#0b0f17");

  // Update toggle icon
  const icon = document.getElementById("themeIcon");
  if (icon) icon.textContent = theme === "light" ? "☀️" : "🌙";
}

// Initialize theme on load
applyTheme(getInitialTheme());

// Bind toggle immediately (no need to wait for DOMContentLoaded)
const toggle = document.getElementById("themeToggle");
if (toggle) {
  toggle.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme") || "dark";
    const next = current === "dark" ? "light" : "dark";
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
  });
}