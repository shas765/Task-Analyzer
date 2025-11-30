from datetime import date, datetime
from typing import List, Dict, Tuple, Set
import math

# CONFIGURABLE WEIGHTS (easy to expose to UI later)
WEIGHT_URGENCY_CLOSE = 40
WEIGHT_OVERDUE = 100
WEIGHT_IMPORTANCE = 6   # multiplied by importance 1-10
WEIGHT_QUICK_WIN = 12   # bonus for small estimated_hours
WEIGHT_DEPENDENCY_BLOCKER = 20  # if other tasks depend on this task
MAX_DAYS_DECAY = 30  # for urgency scaling

def parse_date(d):
    if d is None:
        return None
    if isinstance(d, date):
        return d
    try:
        # expecting YYYY-MM-DD
        return datetime.strptime(d, "%Y-%m-%d").date()
    except Exception:
        # try common alternative formats
        try:
            return datetime.fromisoformat(d).date()
        except Exception:
            return None

def detect_cycles(tasks: List[Dict]) -> List[List[int]]:
    """
    Detect cycles in dependency graph. Returns list of cycles (each cycle list is IDs chain).
    Tasks are dictionaries and should include 'id' keys (if not, we use index).
    """
    # Build id -> deps mapping
    id_map = {}
    for idx, t in enumerate(tasks):
        tid = t.get('id', idx)
        id_map[tid] = t

    visited = {}
    cycles = []

    def dfs(node_id, stack):
        visited[node_id] = 1  # visiting
        stack.append(node_id)
        node = id_map.get(node_id, {})
        for dep in node.get('dependencies', []):
            if dep not in id_map:
                continue
            if visited.get(dep, 0) == 0:
                dfs(dep, stack)
            elif visited.get(dep, 0) == 1:
                # found cycle - slice stack
                try:
                    i = stack.index(dep)
                    cycles.append(stack[i:] + [dep])
                except ValueError:
                    cycles.append([dep, node_id])
        stack.pop()
        visited[node_id] = 2  # done

    for tid in id_map:
        if visited.get(tid, 0) == 0:
            try:
                dfs(tid, [])
            except RecursionError:
                # fallback - skip
                pass
    return cycles

def count_blockers(tasks: List[Dict]) -> dict:
    """
    For each task id, count how many other tasks depend on it.
    """
    id_map = {}
    for idx, t in enumerate(tasks):
        tid = t.get('id', idx)
        id_map[tid] = t

    blockers = {tid: 0 for tid in id_map}
    for tid, task in id_map.items():
        for dep in task.get('dependencies', []):
            if dep in blockers:
                blockers[dep] += 1
    return blockers

def calculate_task_score(task: Dict, today: date, blockers_count: dict) -> Tuple[float, dict]:
    """
    Compute a score for one task. Returns (score, breakdown)
    Higher score = higher priority.
    """
    score = 0.0
    breakdown = {}

    # Validate and normalize
    due_date_raw = task.get('due_date')
    due_date = parse_date(due_date_raw)
    importance = task.get('importance') or 5
    try:
        importance = int(importance)
    except Exception:
        importance = 5

    estimated_hours = task.get('estimated_hours')
    try:
        estimated_hours = int(estimated_hours)
        if estimated_hours < 0:
            estimated_hours = abs(estimated_hours)
    except Exception:
        estimated_hours = 1

    # URGENCY
    if due_date:
        days_until_due = (due_date - today).days
        breakdown['days_until_due'] = days_until_due
        if days_until_due < 0:
            # overdue: heavy boost but scaled by how overdue
            overdue_days = abs(days_until_due)
            boost = WEIGHT_OVERDUE + min(overdue_days * 5, 100)
            score += boost
            breakdown['urgency'] = f'OVERDUE +{boost}'
        else:
            # closeness: inverse scale, closer -> larger
            # scale such that 0 days -> close boost, >MAX_DAYS_DECAY -> small
            closeness = max(0, (MAX_DAYS_DECAY - days_until_due)) / MAX_DAYS_DECAY
            boost = WEIGHT_URGENCY_CLOSE * closeness
            score += boost
            breakdown['urgency'] = f'{boost:.1f}'
    else:
        breakdown['days_until_due'] = None
        # tasks with no due date get moderate default
        score += 5
        breakdown['urgency'] = 'no due date bonus 5'

    # IMPORTANCE
    importance_score = importance * WEIGHT_IMPORTANCE
    score += importance_score
    breakdown['importance'] = importance_score

    # EFFORT (quick wins)
    if estimated_hours <= 0:
        estimated_hours = 1
    if estimated_hours <= 2:
        score += WEIGHT_QUICK_WIN
        breakdown['effort'] = f'quick win +{WEIGHT_QUICK_WIN}'
    else:
        # slight negative effect for very large tasks (larger tasks less likely to be started)
        effort_penalty = min((estimated_hours - 2) * 1.5, 20)
        score -= effort_penalty
        breakdown['effort'] = f'penalty -{effort_penalty:.1f}'

    # DEPENDENCIES (is this a blocker?)
    tid = task.get('id')
    block_count = blockers_count.get(tid, 0)
    if block_count > 0:
        dep_boost = WEIGHT_DEPENDENCY_BLOCKER * math.log1p(block_count)
        score += dep_boost
        breakdown['dependency'] = f'blocks {block_count} tasks +{dep_boost:.1f}'
    else:
        breakdown['dependency'] = 'no blocks'

    # small normalization to keep scores neat
    breakdown['raw_score'] = round(score, 2)
    return round(score, 2), breakdown

def analyze_tasks(tasks: List[Dict], today: date = None) -> dict:
    """
    Main entry: returns dict {
      'sorted': [ {task + score + breakdown} ],
      'cycles': [...],
      'errors': [...]
    }
    """
    today = today or date.today()

    # ensure all tasks have stable ids (if none provided, use index)
    for i, t in enumerate(tasks):
        if 'id' not in t:
            t['id'] = t.get('title', f'__idx_{i}')

    cycles = detect_cycles(tasks)
    blockers_count = count_blockers(tasks)

    results = []
    errors = []
    for t in tasks:
        # Validate fields minimally
        if t.get('importance') is None:
            # default importance = 5
            t['importance'] = 5

        score, breakdown = calculate_task_score(t, today, blockers_count)
        result = t.copy()
        result['score'] = score
        result['score_breakdown'] = breakdown
        results.append(result)

    # sort by score desc
    sorted_tasks = sorted(results, key=lambda x: x['score'], reverse=True)
    return {
        'sorted': sorted_tasks,
        'cycles': cycles,
        'errors': errors
    }
