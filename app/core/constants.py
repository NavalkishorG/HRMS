from enum import Enum


class RoleName(str, Enum):
    ADMIN = 'Admin'
    HR = 'HR'
    EMPLOYEE = 'Employee'
