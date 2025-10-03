import math
from statistics import mean, stdev

def analyze_company_performance(input_json):
    employees = input_json.get('employees', [])
    dept_avgs = input_json.get('department_averages', {})

    high_performers = []
    at_risk = []
    recommendations = []

    for emp in employees:
        emp_id = emp['employee_id']
        dept = emp['department']
        q_scores = emp.get('quarterly_scores', [])
        goals = emp.get('goal_completion_rates', [])

        if not q_scores:
            continue

        # 1) consistent high performer: last 4 quarters average >= 10% above department average for same quarters
        dept_avg = dept_avgs.get(dept)
        if dept_avg and len(dept_avg) >= len(q_scores):
            diffs = []
            for i, s in enumerate(q_scores):
                if i < len(dept_avg):
                    diffs.append((s - dept_avg[i]) / dept_avg[i])
            if diffs and all(d >= 0.1 for d in diffs[-3:]): 
                high_performers.append({
                    'employee_id': emp_id,
                    'reason': f'Consistently >=10% above department average (last {min(3,len(diffs))} quarters)',
                    'confidence': 0.85
                })

        # 2) at risk: rapid decline over last 2 quarters > 15% or last quarter performance drop >20%
        if len(q_scores) >= 3:
            prev_avg = mean(q_scores[-3:-1]) 
            last = q_scores[-1]
            if prev_avg and ((prev_avg - last) / prev_avg) >= 0.15:
                at_risk.append({
                    'employee_id': emp_id,
                    'reason': f'{round(((prev_avg - last)/prev_avg)*100,1)}% performance decline vs previous two-quarter avg',
                    'confidence': 0.92
                })
                recommendations.append({
                    'employee_id': emp_id,
                    'action': 'Schedule performance improvement plan meeting',
                    'priority': 'high'
                })
        elif len(q_scores) == 2:
            prev = q_scores[-2]
            last = q_scores[-1]
            if prev and ((prev - last) / prev) >= 0.2:
                at_risk.append({
                    'employee_id': emp_id,
                    'reason': f'{round(((prev-last)/prev)*100,1)}% performance decline over last 1 quarter',
                    'confidence': 0.85
                })
                recommendations.append({
                    'employee_id': emp_id,
                    'action': 'Manager check-in & coaching',
                    'priority': 'medium'
                })

    return {
        'high_performers': high_performers,
        'at_risk': at_risk,
        'recommendations': recommendations
    }
