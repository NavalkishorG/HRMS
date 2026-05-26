from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: str = 'Employee'


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class EmployeeCreateRequest(BaseModel):
    employee_id: str
    name: str
    email: EmailStr
    department: str
    designation: str
    joining_date: date
    base_salary: float = Field(gt=0)
    salary_type: str = 'monthly'
    role: str = 'Employee'


class EmployeeUpdateRequest(BaseModel):
    name: str | None = None
    department: str | None = None
    designation: str | None = None
    base_salary: float | None = Field(default=None, gt=0)
    salary_type: str | None = None


class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str
    name: str
    department: str
    designation: str
    base_salary: float
    salary_type: str
    is_active: bool


class AttendanceActionResponse(BaseModel):
    message: str


class PayrollGenerateRequest(BaseModel):
    employee_id: str
    month: str = Field(pattern=r'^\d{4}-\d{2}$')
    bonuses: float = 0


class PayrollResponse(BaseModel):
    employee: str
    month: str
    working_days: int
    present_days: int
    late_marks: int
    overtime_hours: float
    deductions: float
    final_salary: float


class AttendanceCorrectionRequest(BaseModel):
    attendance_date: date
    check_in_time: datetime | None = None
    check_out_time: datetime | None = None
