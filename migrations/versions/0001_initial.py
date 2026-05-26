"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-24
"""

from alembic import op
import sqlalchemy as sa


revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table('roles', sa.Column('id', sa.Integer(), primary_key=True), sa.Column('name', sa.String(length=32), nullable=False, unique=True))

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False, unique=True),
        sa.Column('employee_id', sa.String(length=32), nullable=False, unique=True),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('department', sa.String(length=80), nullable=False),
        sa.Column('designation', sa.String(length=80), nullable=False),
        sa.Column('joining_date', sa.Date(), nullable=False),
        sa.Column('base_salary', sa.Float(), nullable=False),
        sa.Column('salary_type', sa.String(length=20), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'attendance_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column('check_in_time', sa.DateTime(timezone=True)),
        sa.Column('check_out_time', sa.DateTime(timezone=True)),
        sa.Column('worked_hours', sa.Float(), nullable=False, server_default='0'),
        sa.Column('late_mark', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('half_day', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('overtime_hours', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'refresh_tokens',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('token', sa.String(length=512), nullable=False, unique=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'payroll_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('employee_id', sa.Integer(), sa.ForeignKey('employees.id'), nullable=False),
        sa.Column('month', sa.String(length=7), nullable=False),
        sa.Column('working_days', sa.Integer(), nullable=False),
        sa.Column('present_days', sa.Integer(), nullable=False),
        sa.Column('leave_count', sa.Integer(), nullable=False),
        sa.Column('late_marks', sa.Integer(), nullable=False),
        sa.Column('overtime_hours', sa.Float(), nullable=False),
        sa.Column('bonuses', sa.Float(), nullable=False, server_default='0'),
        sa.Column('deductions', sa.Float(), nullable=False, server_default='0'),
        sa.Column('final_salary', sa.Float(), nullable=False),
        sa.Column('payslip_path', sa.String(length=255)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('employee_id', 'month', name='uq_payroll_employee_month'),
    )


def downgrade() -> None:
    op.drop_table('payroll_records')
    op.drop_table('refresh_tokens')
    op.drop_table('attendance_records')
    op.drop_table('employees')
    op.drop_table('users')
    op.drop_table('roles')
