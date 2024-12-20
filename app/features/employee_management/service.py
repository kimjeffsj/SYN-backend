from re import U
from typing import Optional

from app.core.security import get_password_hash
from app.features.employee_management.schemas import EmployeeCreate, EmployeeUpdate
from app.models.user import User
from fastapi import HTTPException
from sqlalchemy.orm import Session


class EmployeeManagementService:
    @staticmethod
    async def create_employee(db: Session, data: EmployeeCreate) -> User:
        if db.query(User).filter(User.email == data.email).first():
            raise HTTPException(status_code=400, detail="Email already registered")

        user = User(
            email=data.email,
            full_name=data.full_name,
            hashed_password=get_password_hash(data.password),
            department=data.department,
            position=data.position,
            comment=data.comment,
            role="employee",
        )

        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    async def get_employees(
        db: Session, skip: int = 0, limit: int = 100, search: Optional[str] = None
    ) -> list[User]:
        query = db.query(User).filter(User.role == "employee")

        if search:
            search = f"%{search}%"
            query = query.filter(
                User.full_name.ilike(search)
                | User.email.ilike(search)
                | User.department.ilike(search)
                | User.position.ilike(search)
            )

        return query.offset(skip).limit(limit).all()

    @staticmethod
    async def get_employee(db: Session, employee_id: int) -> User:
        user = db.query(User).filter(User.id == employee_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")
        return user

    @staticmethod
    async def update_employee(
        db: Session, employee_id: int, data: EmployeeUpdate
    ) -> User:
        user = db.query(User).filter(User.id == employee_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Employee not found")

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user
