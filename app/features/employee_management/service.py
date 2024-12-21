import logging
from typing import List, Optional

from app.core.security import get_password_hash
from app.features.employee_management.schemas import (
    DepartmentCreate,
    EmployeeCreate,
    EmployeeUpdate,
    PositionCreate,
)
from app.models.organization import Department, Position
from app.models.user import User
from fastapi import HTTPException, status
from psycopg2 import IntegrityError
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


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

    # Department and position route

    @staticmethod
    async def get_departments(db: Session) -> List[Department]:
        """Get all departments"""
        try:
            departments = db.query(Department).order_by(Department.name).all()
            logger.info(f"Retrieved {len(departments)} departments")
            return departments
        except Exception as e:
            logger.error(f"Error retrieving departments: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get departments: {str(e)}",
            )

    @staticmethod
    async def get_positions(db: Session) -> List[Position]:
        """Get all positions"""
        try:
            positions = db.query(Position).order_by(Position.name).all()
            logger.info(f"Retrieved {len(positions)} positions")
            return positions
        except Exception as e:
            logger.error(f"Error retrieving positions: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get positions: {str(e)}",
            )

    @staticmethod
    async def add_department(db: Session, data: DepartmentCreate) -> Department:
        """Add new department"""
        try:
            department = Department(name=data.name, description=data.description)
            db.add(department)
            db.commit()
            db.refresh(department)
            return department

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Department already exists: {data.name}",
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add department: {str(e)}",
            )

    @staticmethod
    async def add_position(db: Session, data: PositionCreate) -> Position:
        """Add new position"""
        try:
            position = Position(name=data.name, description=data.description)
            db.add(position)
            db.commit()
            db.refresh(position)
            return position

        except IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Position already exists: {data.name}",
            )

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to add position: {str(e)}",
            )

    @staticmethod
    async def delete_department(db: Session, department_id: int) -> bool:
        """Delete department"""
        department = db.query(Department).filter(Department.id == department_id).first()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with id {department_id} not found",
            )

        try:
            db.query(User).filter(User.department == department.name).update(
                {User.department: None}
            )

            db.delete(department)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete department: {str(e)}",
            )

    @staticmethod
    async def delete_position(db: Session, position_id: int) -> bool:
        """Delete position"""
        position = db.query(Position).filter(Position.id == position_id).first()

        if not position:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Position with id {position_id} not found",
            )

        try:
            db.query(User).filter(User.position == position.name).update(
                {User.position: None}
            )

            db.delete(position)
            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete position: {str(e)}",
            )
