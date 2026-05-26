from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx
from sqlalchemy import select

from app.core.constants import RoleName
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.attendance import AttendanceRecord  # noqa: F401
from app.models.employee import Employee
from app.models.payroll import PayrollRecord  # noqa: F401
from app.models.refresh_token import RefreshToken  # noqa: F401
from app.models.role import Role
from app.models.user import User


BASE_URL = "http://127.0.0.1:8000/api/v1"
DOWNLOAD_DIR = Path("zz") / "api_test_downloads"


ADMIN_EMAIL = "temp_admin@example.com"
ADMIN_PASSWORD = "Admin@12345"

HR_EMPLOYEE_ID = "TEMP_HR001"
HR_EMAIL = "temp_hr@example.com"
HR_PASSWORD = "ChangeMe@123"

EMP_EMPLOYEE_ID = "TEMP_EMP001"
EMP_EMAIL = "temp_employee@example.com"
EMP_PASSWORD = "ChangeMe@123"

PUBLIC_EMP_EMAIL = "temp_public_employee@example.com"
PUBLIC_EMP_PASSWORD = "Public@12345"


def pretty(value: object) -> str:
    try:
        return json.dumps(value, indent=2, default=str)
    except Exception:
        return str(value)


def print_section(title: str) -> None:
    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)


def api_call(
    client: httpx.Client,
    method: str,
    path: str,
    token: str | None = None,
    json_body: dict | None = None,
    params: dict | None = None,
    expected_status: int | None = None,
) -> dict | str | bytes:
    url = f"{BASE_URL}{path}"
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    print_section(f"{method} {url}")
    if headers:
        print("Headers:", pretty(headers))
    if json_body is not None:
        print("Request JSON:", pretty(json_body))
    if params is not None:
        print("Request Params:", pretty(params))

    response = client.request(method, url, headers=headers, json=json_body, params=params, timeout=60.0)
    content_type = response.headers.get("content-type", "")
    print("Status:", response.status_code)
    print("Content-Type:", content_type)

    if "application/json" in content_type:
        body: dict | str = response.json()
        print("Response JSON:", pretty(body))
    else:
        body = response.content
        print("Response Bytes Length:", len(response.content))

    if expected_status is not None and response.status_code != expected_status:
        raise RuntimeError(
            f"Expected HTTP {expected_status} but got {response.status_code} for {method} {path}.\n"
            f"Response: {response.text}"
        )

    return body


def ensure_roles_and_users() -> None:
    db = SessionLocal()
    try:
        role_map: dict[str, Role] = {}
        for role_name in (RoleName.ADMIN.value, RoleName.HR.value, RoleName.EMPLOYEE.value):
            role = db.execute(select(Role).where(Role.name == role_name)).scalar_one_or_none()
            if role is None:
                role = Role(name=role_name)
                db.add(role)
                db.flush()
            role_map[role_name] = role

        users_to_create = [
            (ADMIN_EMAIL, ADMIN_PASSWORD, RoleName.ADMIN.value),
            (HR_EMAIL, HR_PASSWORD, RoleName.HR.value),
            (EMP_EMAIL, EMP_PASSWORD, RoleName.EMPLOYEE.value),
        ]
        for email, password, role_name in users_to_create:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user is None:
                db.add(User(email=email, password_hash=hash_password(password), role_id=role_map[role_name].id))

        db.commit()
    finally:
        db.close()


def ensure_employee_profiles() -> None:
    db = SessionLocal()
    try:
        profiles = [
            (HR_EMPLOYEE_ID, HR_EMAIL, "HR Manager", "Human Resources", "HR Lead", 75000.0, "monthly"),
            (EMP_EMPLOYEE_ID, EMP_EMAIL, "Backend Engineer", "Engineering", "Software Engineer", 50000.0, "monthly"),
        ]
        for emp_id, email, name, department, designation, base_salary, salary_type in profiles:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
            if user is None:
                continue
            existing = db.execute(select(Employee).where(Employee.employee_id == emp_id)).scalar_one_or_none()
            if existing is None:
                by_user = db.execute(select(Employee).where(Employee.user_id == user.id)).scalar_one_or_none()
                if by_user is None:
                    db.add(
                        Employee(
                            user_id=user.id,
                            employee_id=emp_id,
                            name=name,
                            department=department,
                            designation=designation,
                            joining_date=datetime.now(timezone.utc).date(),
                            base_salary=base_salary,
                            salary_type=salary_type,
                            is_active=True,
                        )
                    )
        db.commit()
    finally:
        db.close()


def login_and_get_tokens(client: httpx.Client, email: str, password: str) -> dict:
    data = api_call(
        client,
        "POST",
        "/auth/login",
        json_body={"email": email, "password": password},
        expected_status=200,
    )
    assert isinstance(data, dict)
    return data


def ensure_employee_exists(
    client: httpx.Client,
    admin_token: str,
    employee_id: str,
    email: str,
    role: str,
    name: str,
    department: str,
    designation: str,
    base_salary: float,
) -> None:
    payload = {
        "employee_id": employee_id,
        "name": name,
        "email": email,
        "department": department,
        "designation": designation,
        "joining_date": datetime.now(timezone.utc).date().isoformat(),
        "base_salary": base_salary,
        "salary_type": "monthly",
        "role": role,
    }
    body = api_call(
        client,
        "POST",
        "/employees",
        token=admin_token,
        json_body=payload,
    )
    if isinstance(body, dict) and body.get("error", {}).get("code") in {"duplicate_employee_id", "duplicate_email", "duplicate_employee"}:
        print(f"Employee already exists: {employee_id} / {email}")


def main() -> None:
    print_section("HRMS FULL API SMOKE TEST")
    print("BASE_URL:", BASE_URL)
    print("Admin  :", ADMIN_EMAIL, ADMIN_PASSWORD)
    print("HR     :", HR_EMAIL, HR_PASSWORD, "(bootstrap test user)")
    print("Employee:", EMP_EMAIL, EMP_PASSWORD, "(bootstrap test user)")
    print("Public Employee Register:", PUBLIC_EMP_EMAIL, PUBLIC_EMP_PASSWORD)
    ensure_roles_and_users()
    ensure_employee_profiles()

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

    with httpx.Client() as client:
        # Health check
        health_url = BASE_URL.replace("/api/v1", "/health")
        print_section(f"GET {health_url}")
        health = client.get(health_url, timeout=30.0)
        print("Status:", health.status_code)
        print("Body:", health.text)
        if health.status_code != 200:
            raise RuntimeError("Health check failed. Start your server first: uvicorn main:app --reload")

        # Public register endpoint (Employee-only by design)
        api_call(
            client,
            "POST",
            "/auth/register",
            json_body={"email": PUBLIC_EMP_EMAIL, "password": PUBLIC_EMP_PASSWORD, "role": "Employee"},
        )

        # Admin login
        admin_tokens = login_and_get_tokens(client, ADMIN_EMAIL, ADMIN_PASSWORD)
        admin_access = admin_tokens["access_token"]
        admin_refresh = admin_tokens["refresh_token"]
        print_section("ADMIN TOKENS")
        print("Admin Access JWT :", admin_access)
        print("Admin Refresh JWT:", admin_refresh)

        # Refresh and logout for admin
        api_call(
            client,
            "POST",
            "/auth/refresh",
            json_body={"refresh_token": admin_refresh},
            expected_status=200,
        )

        # Create HR + Employee profiles (and user accounts) through admin
        ensure_employee_exists(
            client,
            admin_access,
            HR_EMPLOYEE_ID,
            HR_EMAIL,
            "HR",
            "HR Manager",
            "Human Resources",
            "HR Lead",
            75000,
        )
        ensure_employee_exists(
            client,
            admin_access,
            EMP_EMPLOYEE_ID,
            EMP_EMAIL,
            "Employee",
            "Backend Engineer",
            "Engineering",
            "Software Engineer",
            50000,
        )

        # Employee APIs as admin
        api_call(client, "GET", "/employees", token=admin_access, expected_status=200)
        api_call(client, "GET", f"/employees/{HR_EMPLOYEE_ID}", token=admin_access, expected_status=200)
        api_call(
            client,
            "PUT",
            f"/employees/{EMP_EMPLOYEE_ID}",
            token=admin_access,
            json_body={"designation": "Senior Software Engineer", "base_salary": 52000},
            expected_status=200,
        )

        # Login HR + Employee
        hr_tokens = login_and_get_tokens(client, HR_EMAIL, HR_PASSWORD)
        emp_tokens = login_and_get_tokens(client, EMP_EMAIL, EMP_PASSWORD)
        hr_access = hr_tokens["access_token"]
        hr_refresh = hr_tokens["refresh_token"]
        emp_access = emp_tokens["access_token"]
        emp_refresh = emp_tokens["refresh_token"]

        print_section("HR TOKENS")
        print("HR Access JWT :", hr_access)
        print("HR Refresh JWT:", hr_refresh)

        print_section("EMPLOYEE TOKENS")
        print("Employee Access JWT :", emp_access)
        print("Employee Refresh JWT:", emp_refresh)

        # Employee attendance endpoints
        api_call(client, "POST", "/attendance/check-in", token=emp_access, expected_status=200)
        api_call(client, "POST", "/attendance/check-out", token=emp_access, expected_status=200)
        api_call(client, "GET", "/attendance/me/history", token=emp_access, expected_status=200)

        month = datetime.now(timezone.utc).strftime("%Y-%m")
        api_call(client, "GET", f"/attendance/reports/{EMP_EMPLOYEE_ID}", token=hr_access, params={"month": month}, expected_status=200)

        # Attendance correction by HR
        correction_date = (datetime.now(timezone.utc) - timedelta(days=1)).date().isoformat()
        check_in_time = datetime.now(timezone.utc).replace(hour=10, minute=5, second=0, microsecond=0).isoformat()
        check_out_time = datetime.now(timezone.utc).replace(hour=18, minute=10, second=0, microsecond=0).isoformat()
        api_call(
            client,
            "PATCH",
            f"/attendance/corrections/{EMP_EMPLOYEE_ID}",
            token=hr_access,
            json_body={
                "attendance_date": correction_date,
                "check_in_time": check_in_time,
                "check_out_time": check_out_time,
            },
            expected_status=200,
        )

        # Payroll + payslip flow
        payroll = api_call(
            client,
            "POST",
            "/payroll/generate",
            token=admin_access,
            json_body={"employee_id": EMP_EMPLOYEE_ID, "month": month, "bonuses": 1200},
        )
        if isinstance(payroll, dict) and payroll.get("error", {}).get("code") == "duplicate_payroll":
            print("Payroll already exists for this month; continuing with history/payslip checks.")

        api_call(client, "GET", f"/payroll/history/{EMP_EMPLOYEE_ID}", token=admin_access, expected_status=200)
        emp_history = api_call(client, "GET", f"/payroll/history/{EMP_EMPLOYEE_ID}", token=emp_access, expected_status=200)
        print_section("EMPLOYEE PAYROLL HISTORY (SELF)")
        print(pretty(emp_history))

        payslip_create = api_call(
            client,
            "POST",
            f"/payroll/payslips/{EMP_EMPLOYEE_ID}/{month}",
            token=admin_access,
            expected_status=200,
        )
        assert isinstance(payslip_create, dict)
        payslip_path = payslip_create["payslip_path"]
        print("Generated payslip path:", payslip_path)

        # Employee downloads own payslip
        file_bytes = api_call(
            client,
            "GET",
            "/payroll/payslips/download",
            token=emp_access,
            params={"path": payslip_path},
            expected_status=200,
        )
        assert isinstance(file_bytes, (bytes, bytearray))
        local_file = DOWNLOAD_DIR / f"{EMP_EMPLOYEE_ID}_{month}.pdf"
        local_file.write_bytes(file_bytes)
        print_section("PAYSLIP DOWNLOADED")
        print("Saved to:", str(local_file.resolve()))
        print("Downloaded bytes:", len(file_bytes))

        # Refresh/logout checks for other users
        api_call(client, "POST", "/auth/refresh", json_body={"refresh_token": hr_refresh}, expected_status=200)
        api_call(client, "POST", "/auth/logout", json_body={"refresh_token": hr_refresh}, expected_status=200)
        api_call(client, "POST", "/auth/refresh", json_body={"refresh_token": emp_refresh}, expected_status=200)
        api_call(client, "POST", "/auth/logout", json_body={"refresh_token": emp_refresh}, expected_status=200)
        api_call(client, "POST", "/auth/logout", json_body={"refresh_token": admin_refresh}, expected_status=200)

    print_section("DONE")
    print("Full API smoke test completed.")


if __name__ == "__main__":
    main()
