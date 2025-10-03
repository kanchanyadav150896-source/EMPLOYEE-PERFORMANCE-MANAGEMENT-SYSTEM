from django.test import TestCase
from .models import Employee, ReviewCycle, Review, Score, Goal
from .services import calculate_final_score, calculate_goal_achievement, identify_outliers, get_performance_trend
from django.utils import timezone

class CoreLogicTests(TestCase):
    def setUp(self):
        # create employees, cycles, reviews & scores
        e1 = Employee.objects.create(name='A', email='a@example.com', department='Eng')
        e2 = Employee.objects.create(name='B', email='b@example.com', department='Eng')
        c1 = ReviewCycle.objects.create(name='2024 Q3', start_date='2024-07-01', end_date='2024-09-30', status='closed')
        c2 = ReviewCycle.objects.create(name='2024 Q4', start_date='2024-10-01', end_date='2024-12-31', status='closed')
        r1 = Review.objects.create(employee=e1, reviewer=e1, cycle=c1, review_type='self', status='submitted', submitted_date=timezone.now())
        Score.objects.create(review=r1, criteria='technical', score=8)
        Score.objects.create(review=r1, criteria='communication', score=8)
        Score.objects.create(review=r1, criteria='leadership', score=7)
        Score.objects.create(review=r1, criteria='goals', score=9)
        r2 = Review.objects.create(employee=e1, reviewer=e2, cycle=c1, review_type='peer', status='submitted', submitted_date=timezone.now())
        Score.objects.create(review=r2, criteria='technical', score=7)
        Score.objects.create(review=r2, criteria='communication', score=7)
        Score.objects.create(review=r2, criteria='leadership', score=6)
        Score.objects.create(review=r2, criteria='goals', score=7)
        r3 = Review.objects.create(employee=e1, reviewer=e2, cycle=c1, review_type='manager', status='submitted', submitted_date=timezone.now())
        Score.objects.create(review=r3, criteria='technical', score=9)
        Score.objects.create(review=r3, criteria='communication', score=8)
        Score.objects.create(review=r3, criteria='leadership', score=8)
        Score.objects.create(review=r3, criteria='goals', score=9)

    def test_calculate_final_score(self):
        e1 = Employee.objects.get(email='a@example.com')
        cycle = ReviewCycle.objects.get(name='2024 Q3')
        final = calculate_final_score(e1.id, cycle.id)
        # compute expected: manager avg = (9+8+8+9)/4 = 8.5;
        self.assertAlmostEqual(final, 8.0, places=2)

    def test_calculate_goal_achievement_empty(self):
        e1 = Employee.objects.get(email='a@example.com')
        cycle = ReviewCycle.objects.get(name='2024 Q3')
        ga = calculate_goal_achievement(e1.id, cycle.id)
        self.assertEqual(ga['total_goals'], 0)
