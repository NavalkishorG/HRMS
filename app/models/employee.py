from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.datetime import utcnow


class Employee(Base):
    __tablename__ = 'employees'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    department: Mapped[str] = mapped_column(String(80), nullable=False)
    designation: Mapped[str] = mapped_column(String(80), nullable=False)
    joining_date: Mapped[date] = mapped_column(Date, nullable=False)
    base_salary: Mapped[float] = mapped_column(Float, nullable=False)
    salary_type: Mapped[str] = mapped_column(String(20), nullable=False, default='monthly')
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    user = relationship('User', back_populates='employee')
    attendance_records = relationship('AttendanceRecord', back_populates='employee')
    payroll_records = relationship('PayrollRecord', back_populates='employee')
