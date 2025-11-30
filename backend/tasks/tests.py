from django.test import TestCase
from datetime import date, timedelta
from .scoring import analyze_tasks, detect_cycles

class ScoringTests(TestCase):

    def test_overdue_boost(self):
        t = {
            'id': 't1',
            'title': 'Overdue',
            'due_date': (date.today() - timedelta(days=2)).isoformat(),
            'estimated_hours': 3,
            'importance': 5
        }
        res = analyze_tasks([t])
        top = res['sorted'][0]
        self.assertTrue(top['score'] > 50)  # should be boosted

    def test_quick_win_bonus(self):
        t1 = {'id': 'quick', 'title': 'Quick', 'due_date': None, 'estimated_hours': 1, 'importance': 3}
        t2 = {'id': 'long', 'title': 'Long', 'due_date': None, 'estimated_hours': 8, 'importance': 3}
        res = analyze_tasks([t1, t2])
        # quick should rank above long due to quick win
        self.assertEqual(res['sorted'][0]['id'], 'quick')

    def test_cycle_detection(self):
        a = {'id': 'a', 'dependencies': ['b']}
        b = {'id': 'b', 'dependencies': ['c']}
        c = {'id': 'c', 'dependencies': ['a']}
        cycles = detect_cycles([a,b,c])
        self.assertTrue(len(cycles) >= 1)
