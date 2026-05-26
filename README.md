# HRMS Backend

A modular HRMS backend built with FastAPI, PostgreSQL, SQLAlchemy ORM, JWT authentication, RBAC, attendance workflows, salary calculation, and payroll/payslip generation.

## Features

- Authentication with JWT access + refresh tokens
- Role-based access control (`Admin`, `HR`, `Employee`)
- Employee lifecycle management
- Attendance check-in/check-out with rule validation
- Monthly attendance summary and correction API
- Salary calculation engine
- Payroll generation with duplicate prevention
- Payslip PDF generation and secure download

## Tech Stack

- FastAPI
- PostgreSQL
- SQLAlchemy ORM
- Alembic
- python-jose (JWT)
- passlib[bcrypt]
- Pydantic
- Pytest

## Architecture

Layered design:

1. API Layer (`app/api`): routes, request/response validation, auth guards
2. Service Layer (`app/services`): business rules and domain logic
3. Data Layer (`app/models`, `app/db`): models, session management, persistence

Request flow:

`Router -> Service -> SQLAlchemy -> PostgreSQL`

## Project Structure

- `main.py`: app bootstrap (`FastAPI`, middleware, routers, `/health`)
- `app/core`: configuration, security, exceptions
- `app/api`: dependencies + versioned routers
- `app/services`: module business logic
- `app/models`: SQLAlchemy entities
- `app/db`: engine/session/base/seed
- `migrations`: Alembic configuration and revisions
- `tests`: unit and integration tests

## Module Overview

### 1) Authentication and RBAC

Key files:
- `app/api/v1/auth.py`
- `app/api/deps.py`
- `app/services/auth_service.py`
- `app/core/security.py`

Capabilities:
- Register, login, refresh, logout
- Password hashing and token expiry handling
- Route protection by role

Rules enforced:
- Invalid/expired token handling
- Access token type enforcement
- Employee blocked from HR/Admin-only endpoints
- Public registration restricted to Employee role

### 2) Employee Management

Key files:
- `app/api/v1/employees.py`
- `app/services/employee_service.py`

Capabilities:
- Create employee
- Update employee
- List employees
- Get employee by ID
- Deactivate employee

Rules enforced:
- Unique employee ID and email
- Joining date cannot be in the future
- Inactive employees cannot be updated
- HR cannot deactivate Admin accounts
- Employee can only access own profile

### 3) Attendance Management

Key files:
- `app/api/v1/attendance.py`
- `app/services/attendance_service.py`

Capabilities:
- Daily check-in and check-out
- Personal attendance history
- Monthly attendance summary
- Attendance correction (HR/Admin)

Rules enforced:
- Double check-in not allowed
- Check-out before check-in invalid
- Future attendance invalid
- Multiple active sessions not allowed
- Overtime max cap enforced
- Half-day and late-mark logic based on configured thresholds

### 4) Salary Calculation Engine

Key file:
- `app/services/salary_service.py`

Formula:

`final_salary = base_salary - late_deductions - leave_deductions + overtime_amount + bonuses`

### 5) Payroll and Payslip

Key files:
- `app/api/v1/payroll.py`
- `app/services/payroll_service.py`

Capabilities:
- Generate monthly payroll by employee and month
- Payroll history
- Generate payslip PDF
- Secure payslip download

Rules enforced:
- Duplicate payroll generation blocked for same employee-month
- Negative salary blocked
- Employee can only view/download own payroll artifacts
- Payslip path traversal protection

## API Endpoints

Base path: `/api/v1`

Auth:
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/refresh`
- `POST /auth/logout`

Employees:
- `POST /employees`
- `GET /employees`
- `GET /employees/{employee_id}`
- `PUT /employees/{employee_id}`
- `DELETE /employees/{employee_id}`

Attendance:
- `POST /attendance/check-in`
- `POST /attendance/check-out`
- `GET /attendance/me/history`
- `GET /attendance/reports/{employee_id}?month=YYYY-MM`
- `PATCH /attendance/corrections/{employee_id}`

Payroll:
- `POST /payroll/generate`
- `GET /payroll/history/{employee_id}`
- `POST /payroll/payslips/{employee_id}/{month}`
- `GET /payroll/payslips/download?path=...`

Health:
- `GET /health`

## Setup and Run

### Prerequisites

- Python 3.11
- PostgreSQL 15+
- Git

### 1) Create and activate virtual environment (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment

```powershell
Copy-Item .env.example .env
```

Update `.env` values:
- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `CORS_ORIGINS`

### 4) Create database

```sql
CREATE DATABASE hrms;
```

### 5) Apply migrations

```powershell
alembic upgrade head
```

### 6) Seed roles and default admin

```powershell
python -m app.db.seed
```

Default admin email:
- `admin@hrms.local`

### 7) Run application

```powershell
uvicorn main:app --reload
```

### 8) Open API docs

- Swagger: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Configuration

Key `.env` controls:

- JWT: `JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`
- Attendance timing: `OFFICE_START_*`, `LATE_AFTER_*`, `FULL_DAY_HOURS`, `HALF_DAY_MIN_HOURS`
- Payroll rules: `LATE_DEDUCTION_PER_MARK`, `LEAVE_DEDUCTION_PER_DAY`, `OVERTIME_MAX_HOURS_PER_DAY`, `OVERTIME_HOURLY_RATE_MULTIPLIER`

## Testing

Run tests:

```powershell
.\venv\Scripts\python.exe -m pytest -q
```

Run full API smoke test (prints JWTs, credentials, endpoint responses, and downloads payslip):

```powershell
.\venv\Scripts\python.exe test.py
```

`test.py` coverage includes:
- Auth: register, login, refresh, logout
- Employee APIs: create/list/get/update
- Attendance: check-in, check-out, history, monthly report, correction
- Payroll: generate, history, payslip create, payslip download

Downloaded payslip location:
- `zz/api_test_downloads/`

Run lint:

```powershell
ruff check .
```

Run type checks:

```powershell
mypy .
```

## Error Response Model

```json
{
  "error": {
    "code": "validation_error",
    "message": "Input validation failed",
    "trace_id": "...",
    "timestamp": "2026-05-24T00:00:00Z",
    "details": []
  }
}
```

## Troubleshooting

- Migration failures:
  - Verify `DATABASE_URL` and DB availability.
- Auth failures:
  - Verify JWT secret and token expiry configuration.
- Duplicate payroll errors:
  - Expected when regenerating the same employee-month payroll.
