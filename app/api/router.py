from fastapi import APIRouter

from app.api.v1.attendance import router as attendance_router
from app.api.v1.auth import router as auth_router
from app.api.v1.employees import router as employees_router
from app.api.v1.payroll import router as payroll_router


api_router = APIRouter()
api_router.include_router(auth_router, prefix='/auth', tags=['Auth'])
api_router.include_router(employees_router, prefix='/employees', tags=['Employees'])
api_router.include_router(attendance_router, prefix='/attendance', tags=['Attendance'])
api_router.include_router(payroll_router, prefix='/payroll', tags=['Payroll'])
