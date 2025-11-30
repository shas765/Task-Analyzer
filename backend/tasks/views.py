import json
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .scoring import analyze_tasks

@csrf_exempt
def analyze_view(request):
    """
    POST /api/tasks/analyze/
    Accepts JSON: either { "tasks": [ ... ] } or an array directly
    """
    if request.method != "POST":
        return JsonResponse({'detail': 'Use POST'}, status=405)

    try:
        body = request.body.decode('utf-8')
        data = json.loads(body) if body else {}
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    if isinstance(data, dict) and 'tasks' in data:
        tasks = data['tasks']
    elif isinstance(data, list):
        tasks = data
    else:
        return JsonResponse({'error': 'JSON must be an array of tasks or { "tasks": [...] }'}, status=400)

    # run analysis
    result = analyze_tasks(tasks, today=date.today())
    return JsonResponse(result, safe=False)


def explain_choice(task):
    bd = task.get('score_breakdown', {})
    lines = []
    if 'days_until_due' in bd and bd['days_until_due'] is not None:
        d = bd['days_until_due']
        if d < 0:
            lines.append(f"Overdue by {abs(d)} day(s).")
        elif d == 0:
            lines.append("Due today.")
        else:
            lines.append(f"Due in {d} day(s).")
    if 'importance' in bd:
        lines.append(f"Importance contributed {bd['importance']}.")
    if 'effort' in bd:
        lines.append(f"Effort adjustment: {bd['effort']}.")
    if 'dependency' in bd:
        lines.append(f"{bd['dependency']}.")
    return " ".join(lines)

def suggest_view(request):
    """
    GET /api/tasks/suggest/
    Expects tasks passed as query param JSON-encoded ?tasks=[{...}, ...]
    Or falls back to static sample if none provided.
    """
    # For simplicity allow tasks via GET query param 'tasks' (JSON encoded) or load from body if POST
    tasks_json = request.GET.get('tasks')
    if tasks_json:
        try:
            tasks = json.loads(tasks_json)
        except Exception:
            return JsonResponse({'error': 'Invalid tasks query parameter JSON'}, status=400)
    else:
        # Not provided — return a helpful message
        return JsonResponse({'error': 'Please pass tasks as a JSON-encoded "tasks" query parameter, e.g. ?tasks=[...]'}, status=400)

    # analyze
    result = analyze_tasks(tasks, today=date.today())
    top3 = result['sorted'][:3]
    for t in top3:
        t['explanation'] = explain_choice(t)

    return JsonResponse({
        'top3': top3,
        'cycles': result['cycles']
    }, safe=False)
