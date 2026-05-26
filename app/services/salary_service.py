from app.core.config import settings


def calculate_final_salary(base_salary: float, late_marks: int, leave_count: int, overtime_hours: float, bonuses: float) -> dict:
    late_deductions = late_marks * settings.LATE_DEDUCTION_PER_MARK
    leave_deductions = leave_count * settings.LEAVE_DEDUCTION_PER_DAY
    overtime_amount = overtime_hours * ((base_salary / 30) / settings.FULL_DAY_HOURS) * settings.OVERTIME_HOURLY_RATE_MULTIPLIER
    final_salary = base_salary - late_deductions - leave_deductions + overtime_amount + bonuses
    return {
        'late_deductions': round(late_deductions, 2),
        'leave_deductions': round(leave_deductions, 2),
        'overtime_amount': round(overtime_amount, 2),
        'final_salary': round(final_salary, 2),
    }
