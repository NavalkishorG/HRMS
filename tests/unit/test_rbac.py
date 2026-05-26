from app.core.constants import RoleName


def can_access(role: str, allowed: set[str]) -> bool:
    return role in allowed


def test_employee_cannot_access_admin_hr_routes():
    allowed = {RoleName.ADMIN.value, RoleName.HR.value}
    assert can_access(RoleName.EMPLOYEE.value, allowed) is False


def test_admin_can_access_admin_hr_routes():
    allowed = {RoleName.ADMIN.value, RoleName.HR.value}
    assert can_access(RoleName.ADMIN.value, allowed) is True
