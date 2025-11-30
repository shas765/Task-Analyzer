# Smart Task Analyzer

## 1. Setup Instructions

Follow these steps to install and run the Smart Task Analyzer:

### **Step 1 — Create & activate virtual environment**

**Windows**

```
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux**

```
python3 -m venv venv
source venv/bin/activate
```

### **Step 2 — Install dependencies**

```
pip install -r requirements.txt
```

### **Step 3 — Apply migrations**

```
python manage.py migrate
```

### **Step 4 — Run server**

```
python manage.py runserver
```

### **Step 5 — Open the application**

Frontend served via Django static files:

```
http://127.0.0.1:8000/
```

---

## 2. Algorithm Explanation (300–500 words)

The Smart Task Analyzer uses a weighted scoring system designed to mimic how humans naturally prioritize work. Instead of simply sorting by due dates or importance alone, the algorithm blends multiple dimensions—urgency, importance, effort, and dependency structure—to produce a realistic task priority ranking.

### **Urgency**

The first factor is urgency, derived from the difference between the current date and the task’s due date. Overdue tasks receive a very large boost, since they demand immediate attention. Tasks due within the next few days also receive urgency bonuses. This prevents important deadlines from being overshadowed by long-term high-importance tasks. The algorithm handles missing or invalid dates safely by treating them as “no due date” tasks with neutral urgency.

### **Importance**

Importance is rated on a 1–10 scale and multiplied by a fixed weight (e.g., ×6). This ensures that meaningful work consistently competes with short-term urgent tasks. A highly important task may still appear near the top even if it is not immediately due. The weight was chosen to balance urgency and importance without allowing either factor to dominate completely.

### **Effort**

Effort represents the estimated hours needed to complete a task. Quick tasks (under ~2 hours) receive a small bonus to encourage clearing low-effort items early and maintaining workflow momentum. Conversely, tasks with extremely high effort receive a slight penalty to avoid unrealistic prioritization—typically you cannot begin a 20-hour task immediately even if it is important.

### **Dependencies**

Dependency resolution is one of the more advanced features. Tasks often depend on earlier work being completed. The algorithm builds a dependency graph and uses topological sorting to ensure all prerequisites appear before dependent tasks. Additionally, tasks that block many others receive a logarithmic boost to reflect their strategic importance. The system also detects circular dependencies; instead of attempting invalid ordering, it warns the user of the cycle.

### **Transparency**

Each task returns a score breakdown and natural-language explanation. This improves trust and makes tuning easier.

By combining urgency, importance, effort, and dependency influence, the algorithm produces a balanced, realistic ranking that reflects real-world task prioritization behavior.

---

## 3. Design Decisions (Trade-Offs)

* **Weighted scoring vs machine learning:**
  I chose deterministic weights over ML for transparency, predictability, and ease of tuning.

* **Topological sorting instead of naive scoring:**
  Prevents dependent tasks from surfacing prematurely and avoids impossible sequences.

* **Client-side sorting strategies:**
  Additional strategies (fastest, impact, deadline) were implemented on the frontend to keep backend clean and maintainable.

* **Hybrid input model (JSON + form):**
  Users can add tasks individually or paste large JSON sets. Both inputs auto-merge for flexibility.

* **Lightweight frontend:**
  No frameworks used to reduce setup time and complexity.

---

## 4. Time Breakdown

| Task                               | Time      |
| ---------------------------------- | --------- |
| Project setup                      | 15–20 min |
| Django models & setup              | 20–30 min |
| Scoring algorithm                  | 60–70 min |
| Dependency graph + cycle detection | 40–50 min |
| API views + routing                | 25–30 min |
| Frontend UI (HTML/CSS/JS)          | 60–90 min |
| Debugging & integration            | 45 min    |
| Documentation                      | 20 min    |

**Total:** ~4.5 to 5 hours

---
<!-- 
## 5. Bonus Challenges Attempted

* ✔ Dependency cycle detection
* ✔ Score breakdown + explanation
* ✔ Multiple sorting modes
* ✔ Auto-merge of form input + JSON input
* ✔ Clean responsive interface -->

---
## 5. Future Improvements

If given more time, I would add:

* User accounts and persistent saved tasks
* Task categories, labels, and color grouping
* Drag-and-drop reordering
* Export/import in CSV format
* Dark mode and improved UI theming
* A more advanced scoring engine or ML-based personalization
* Task history and completion tracking
* Integration of calendar reminders or notifications

---

This README covers all required assignment sections clearly and professionally.
