from .models import Employee, Review, Score, ReviewCycle, Goal
from django.db.models import Avg, Q
import math
from statistics import mean, stdev
from collections import defaultdict

# helper to get average numeric score for a review
def _avg_score_for_review(review):
    scores = review.scores.all()
    if not scores or scores.count() == 0:
        return None
    vals = [s.score for s in scores]
    return sum(vals)/len(vals)

def calculate_final_score(employee_id, cycle_id):
    """
    Calculate weighted final score for employee for given cycle_id.
    Weights:
      - Manager: 50%
      - Self: 30%
      - Peers: 20% (average of all peer reviews)
    Returns final numeric score (0-10) or None if insufficient data.
    """
    employee = Employee.objects.filter(id=employee_id, is_deleted=False).first()
    if not employee:
        return None

    cycle = ReviewCycle.objects.filter(id=cycle_id).first()
    if not cycle:
        return None

    reviews = Review.objects.filter(employee=employee, cycle=cycle, status='submitted', is_deleted=False)
    # manager
    manager_reviews = reviews.filter(review_type='manager')
    self_reviews = reviews.filter(review_type='self')
    peer_reviews = reviews.filter(review_type='peer')

    manager_score = None
    if manager_reviews.exists():
        # if more than one manager review, average them
        manager_score_vals = [_avg_score_for_review(r) for r in manager_reviews if _avg_score_for_review(r) is not None]
        if manager_score_vals:
            manager_score = mean(manager_score_vals)

    self_score = None
    if self_reviews.exists():
        self_vals = [_avg_score_for_review(r) for r in self_reviews if _avg_score_for_review(r) is not None]
        if self_vals:
            self_score = mean(self_vals)

    peer_score = None
    if peer_reviews.exists():
        peer_vals = [_avg_score_for_review(r) for r in peer_reviews if _avg_score_for_review(r) is not None]
        if peer_vals:
            peer_score = mean(peer_vals)

    # require at least a manager review or self+peer to compute
    # business rule: manager review required for final score; if not present, compute best-effort
    if manager_score is None:
        # weight self 60% and peers 40%
        if self_score is None and peer_score is None:
            return None
        total = 0
        weight_sum = 0
        if self_score is not None:
            total += 0.6 * self_score
            weight_sum += 0.6
        if peer_score is not None:
            total += 0.4 * peer_score
            weight_sum += 0.4
        return round(total / weight_sum, 2) if weight_sum > 0 else None


    total = 0
    total += 0.5 * manager_score
    weight_sum = 0.5
    if self_score is not None:
        total += 0.3 * self_score
        weight_sum += 0.3
    if peer_score is not None:
        total += 0.2 * peer_score
        weight_sum += 0.2
    final = total / weight_sum
    return round(final, 2)

def get_performance_trend(employee_id, num_cycles=3):
    """
    Return list of last num_cycles final scores for employee ordered oldest->newest.
    """
    cycles = ReviewCycle.objects.order_by('-start_date')[:num_cycles]
    trend = []
    cycles = list(cycles)[::-1]  # oldest to newest
    for cycle in cycles:
        final = calculate_final_score(employee_id, cycle.id)
        trend.append({'cycle': cycle.name, 'final_score': final})
    return trend

def identify_outliers(department):
    """
    Find performance outliers in department.
    Definition: an employee whose most recent final score differs from department average by >1.5 stddev.
    Returns list of dict {employee_id, name, final_score, dept_avg, dept_std, zscore}
    """

    latest_cycle = ReviewCycle.objects.order_by('-start_date').first()
    if not latest_cycle:
        return []

    employees = Employee.objects.filter(department=department, is_deleted=False)
    final_scores = []
    emp_map = {}
    for e in employees:
        s = calculate_final_score(e.id, latest_cycle.id)
        if s is not None:
            final_scores.append(s)
            emp_map[e.id] = {'employee': e, 'score': s}

    if not final_scores:
        return []

    avg = mean(final_scores)
    std = stdev(final_scores) if len(final_scores) > 1 else 0.0
    threshold = 1.5 * std
    outliers = []
    for eid, info in emp_map.items():
        score = info['score']
        if std == 0:
            continue
        z = (score - avg) / std
        if abs(z) > 1.5:
            outliers.append({
                'employee_id': eid,
                'name': info['employee'].name,
                'final_score': score,
                'department_avg': round(avg,2),
                'department_std': round(std,2),
                'zscore': round(z,2)
            })
    return outliers

def calculate_goal_achievement(employee_id, cycle_id):
    """
    Calculate goal completion percentage for employee in cycle.
    Return:
        {
            'employee_id': ..,
            'cycle_id': ..,
            'total_goals': n,
            'completed': x,
            'completion_rate': 0.0-1.0,
            'weighted_goal_score': 0-10 (optionally)
        }
    Weighted goal score: completion_rate * 10
    """
    qs = Goal.objects.filter(employee_id=employee_id, cycle_id=cycle_id, is_deleted=False)
    total = qs.count()
    if total == 0:
        return {'employee_id': employee_id, 'cycle_id': cycle_id, 'total_goals': 0, 'completed': 0, 'completion_rate': None, 'weighted_goal_score': None}
    completed = qs.filter(status='completed').count()
    # Additionally we can calculate progress-weighted completion: cap progress at 100
    progress_sum = sum([min(100, g.progress) for g in qs])
    completion_rate = completed / total
    progress_avg = progress_sum / total / 100.0
    # weighted goal score: 0-10, combine completion rate 70% and average progress 30%
    weighted_score = round(((0.7 * completion_rate) + (0.3 * progress_avg)) * 10, 2)
    return {
        'employee_id': employee_id,
        'cycle_id': cycle_id,
        'total_goals': total,
        'completed': completed,
        'completion_rate': round(completion_rate,3),
        'avg_progress': round(progress_avg,3),
        'weighted_goal_score': weighted_score
    }
