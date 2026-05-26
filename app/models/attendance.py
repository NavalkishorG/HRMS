from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.datetime import utcnow


class AttendanceRecord(Base):
    __tablename__ = 'attendance_records'

    id: Mapped[int] = mapped_column(primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey('employees.id'), nullable=False, index=True)
    attendance_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    check_in_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    worked_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    late_mark: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    half_day: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overtime_hours: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    employee = relationship('Employee', back_populates='attendance_records')
