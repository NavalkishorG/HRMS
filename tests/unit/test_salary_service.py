from app.services.salary_service import calculate_final_salary


def test_salary_calculation_positive():
    result = calculate_final_salary(50000, late_marks=2, leave_count=1, overtime_hours=10, bonuses=1000)
    assert result['final_salary'] > 0
    assert result['late_deductions'] == 500
    assert result['leave_deductions'] == 500


def test_salary_calculation_no_deductions():
    result = calculate_final_salary(50000, late_marks=0, leave_count=0, overtime_hours=0, bonuses=0)
    assert result['final_salary'] == 50000
