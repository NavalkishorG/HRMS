from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.datetime import utcnow


class PayrollRecord(Base):
    __tablename__ = 'payroll_records'
    __table_args__ = (UniqueConstraint('employee_id', 'month', name='uq_payroll_employee_month'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(7), nullable=False, index=True)  # YYYY-MM
    working_days: Mapped[int] = mapped_column(nullable=False)
    present_days: Mapped[int] = mapped_column(nullable=False)
    leave_count: Mapped[int] = mapped_column(nullable=False)
    late_marks: Mapped[int] = mapped_column(nullable=False)
    overtime_hours: Mapped[float] = mapped_column(Float, nullable=False)
    bonuses: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    deductions: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    final_salary: Mapped[float] = mapped_column(Float, nullable=False)
    payslip_path: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    employee = relationship('Employee', back_populates='payroll_records')
