console.log("SCRIPT LOADED OK");

// ------------------------------
// LOCAL TASK STORAGE
// ------------------------------
const localTasks = [];

function renderLocalList() {
  document.getElementById('localList').textContent = JSON.stringify(localTasks, null, 2);
}

// ------------------------------
// ADD TASK BUTTON (LEFT PANEL)
// ------------------------------
document.getElementById('addTask').addEventListener('click', () => {
  const title = document.getElementById('title').value.trim();
  if (!title) {
    alert('Title required');
    return;
  }

  const t = {
    id: title + '-' + Date.now(),
    title,
    due_date: document.getElementById('due_date').value || null,
    estimated_hours: parseInt(document.getElementById('estimated_hours').value) || 1,
    importance: parseInt(document.getElementById('importance').value) || 5,
    dependencies: (document.getElementById('dependencies').value || '')
      .split(',')
      .map(s => s.trim())
      .filter(Boolean)
  };

  localTasks.push(t);
  renderLocalList();
});

// ------------------------------
// ANALYZE TASKS BUTTON
// ------------------------------
document.getElementById('analyzeBtn').addEventListener('click', async () => {
  // Build final task list
let tasks = [];
const text = document.getElementById('taskInput').value.trim();

// 1. Add textarea tasks if present
if (text) {
  try {
    tasks = JSON.parse(text);
  } catch (e) {
    alert('Invalid JSON in textarea');
    return;
  }
}

// 2. Always include localTasks (local form tasks)
tasks = tasks.concat(localTasks);

// 3. Ensure something exists
if (!tasks || !Array.isArray(tasks) || tasks.length === 0) {
  alert('No tasks to analyze. Add tasks in form or paste JSON.');
  return;
}

// 4. Sorting strategy
const strategy = document.getElementById('strategy').value;

  // 2. SEND POST REQUEST TO DJANGO
  try {
    const resp = await fetch('http://127.0.0.1:8000/api/tasks/analyze/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tasks)
    });

    if (!resp.ok) {
      const err = await resp.json();
      alert('Server error: ' + (err.error || JSON.stringify(err)));
      return;
    }

    const result = await resp.json();
    let sorted = result.sorted || [];

    // 3. OPTIONAL SORT STRATEGIES (CLIENT SIDE)
    if (strategy === 'fastest') {
      sorted.sort((a, b) => (a.estimated_hours - b.estimated_hours) || (b.score - a.score));
    } else if (strategy === 'impact') {
      sorted.sort((a, b) => (b.importance - a.importance) || (b.score - a.score));
    } else if (strategy === 'deadline') {
      sorted.sort((a, b) => {
        const da = a.due_date ? new Date(a.due_date) : new Date(8640000000000000);
        const db = b.due_date ? new Date(b.due_date) : new Date(8640000000000000);
        return da - db;
      });
    }
    // Smart balance → use backend order

    // 4. DISPLAY RESULTS
    displayResults(sorted, result.cycles || []);

  } catch (err) {
    console.error('Network or server error:', err);
    alert('Failed to analyze tasks. Check console for details.');
  }
});

// ------------------------------
// DISPLAY RESULTS
// ------------------------------
function displayResults(sorted, cycles) {
  const root = document.getElementById('results');
  root.innerHTML = '';

  // Show cycle warnings
  if (cycles && cycles.length) {
    const c = document.createElement('div');
    c.className = 'card';
    c.style.background = '#fff0f0';
    c.innerHTML = `
      <strong>Dependency cycles detected:</strong>
      <pre>${JSON.stringify(cycles, null, 2)}</pre>
    `;
    root.appendChild(c);
  }

  // Show tasks
  sorted.forEach(t => {
    const div = document.createElement('div');
    const score = t.score || 0;

    let cls = 'priority-low';
    if (score >= 80) cls = 'priority-high';
    else if (score >= 40) cls = 'priority-medium';

    div.className = `card ${cls}`;
    div.innerHTML = `
      <div><strong>${t.title}</strong> <span class="score">(${score})</span></div>
      <div><small>Due: ${t.due_date || '—'} | Est: ${t.estimated_hours}h | Imp: ${t.importance}</small></div>
      <div><small>${t.score_breakdown ? JSON.stringify(t.score_breakdown) : ''}</small></div>
      <div><em>${t.explanation || ''}</em></div>
    `;
    root.appendChild(div);
  });
}
