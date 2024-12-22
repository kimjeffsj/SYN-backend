from typing import Optional

from app.core.events import Event, event_bus
from app.features.notifications.events.types import NotificationEventType
from app.models import leave_request
from app.models.leave_request import LeaveRequest, LeaveStatus
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy import and_
from sqlalchemy.orm import Session


class LeaveRequestService:
    @staticmethod
    def _format_leave_request(request: LeaveRequest) -> dict:
        """Format leave request to dict for response"""

        employee_data = {
            "id": request.employee.id,
            "name": request.employee.full_name,  # full_name -> name으로 매핑
            "position": request.employee.position,
            "department": request.employee.department,
        }

        formatted = {
            "id": request.id,
            "employee_id": request.employee_id,
            "employee": employee_data,
            "leave_type": request.leave_type,
            "start_date": (
                request.start_date.isoformat() if request.start_date else None
            ),
            "end_date": request.end_date.isoformat() if request.end_date else None,
            "reason": request.reason,
            "status": request.status,
            "created_at": (
                request.created_at.isoformat() if request.created_at else None
            ),
            "updated_at": (
                request.updated_at.isoformat() if request.updated_at else None
            ),
        }

        # Add admin response if exists
        if request.admin_id:
            formatted["admin_response"] = {
                "admin_id": request.admin_id,
                "admin_name": request.admin.full_name,
                "comment": request.admin_comment,
                "processed_at": (
                    request.processed_at.isoformat() if request.processed_at else None
                ),
            }

        return formatted

    @staticmethod
    def get_leave_requests(
        db: Session, employee_id: Optional[int] = None, status: Optional[str] = None
    ) -> list[LeaveRequest]:
        """Get leave requests with filtering"""
        query = db.query(LeaveRequest)

        if employee_id:
            query = query.filter(LeaveRequest.employee_id == employee_id)

        if status:
            query = query.filter(LeaveRequest.status == status)

        requests = query.order_by(LeaveRequest.created_at.desc()).all()
        return [LeaveRequestService._format_leave_request(req) for req in requests]

    @staticmethod
    def get_leave_request(db: Session, request_id: int) -> LeaveRequest:
        """Get a leave request"""
        request = db.query(LeaveRequest).filter(LeaveRequest.id == request_id).first()
        if not request:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leave request not found",
            )
        return request

    @staticmethod
    async def create_leave_request(
        db: Session, request_data: dict, employee_id: int
    ) -> LeaveRequest:
        """Create a new leave request"""
        employee = (
            db.query(Schedule)
            .filter(
                Schedule.user_id == employee_id,
                Schedule.start_time <= request_data["start_date"],
                Schedule.end_time >= request_data["end_date"],
            )
            .all()
        )

        leave_request = LeaveRequest(employee_id=employee_id, **request_data)

        try:
            db.add(leave_request)
            db.commit()
            db.refresh(leave_request)

            # Notification for admin
            notification = Notification(
                type=NotificationType.LEAVE_REQUEST,
                title="New Leave Request",
                message=f"New leave request from {leave_request.employee.full_name}",
                priority=NotificationPriority.HIGH,
                data=LeaveRequestService._format_leave_request(leave_request),
            )

            # Find admin and create notifications
            admin_users = db.query(User).filter(User.role == "admin").all()
            for admin in admin_users:
                notification.user_id = admin.id
                db.add(notification)

            db.commit()

            await event_bus.publish(
                Event(
                    type=NotificationEventType.LEAVE_REQUESTED,
                    data={
                        "leave_request": LeaveRequestService._format_leave_request(
                            leave_request
                        ),
                        "notification": notification.to_dict(),
                    },
                )
            )

            return LeaveRequestService._format_leave_request(leave_request)

        except Exception as e:
            db.rollback()
            print(f"Failed to create leave request: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create leave request: {str(e)}",
            )

    @staticmethod
    async def process_leave_request(
        db: Session,
        request_id: int,
        admin_id: int,
        status: LeaveStatus,
        comment: Optional[str] = None,
    ) -> dict:
        """Process leave request"""
        leave_request = LeaveRequestService.get_leave_request(db, request_id)

        if leave_request.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot process request with status: {leave_request.status}",
            )

        try:
            if status == LeaveStatus.APPROVED:
                leave_request.approve(admin_id, comment)

                # Update employee's leave balance
                leave_duration = leave_request.duration_days
                employee = leave_request.employee
                employee.leave_balance = max(0, employee.leave_balance - leave_duration)

                # Cancel existing schedules
                schedules = (
                    db.query(Schedule)
                    .filter(
                        and_(
                            Schedule.user_id == leave_request.employee_id,
                            Schedule.start_time >= leave_request.start_date,
                            Schedule.end_time <= leave_request.end_date,
                            Schedule.status != ScheduleStatus.CANCELLED,
                        )
                    )
                    .all()
                )

                for schedule in schedules:
                    schedule.status = ScheduleStatus.CANCELLED

            else:
                leave_request.reject(admin_id, comment)

            # Create notification for employee
            notification = Notification(
                user_id=leave_request.employee_id,
                type=NotificationType.LEAVE_REQUEST,
                title=f"Leave Request {status.capitalize()}",
                message=f"Your leave request has been {status.lower()}",
                priority=NotificationPriority.HIGH,
                data=LeaveRequestService._format_leave_request(leave_request),
            )

            db.add(notification)
            db.commit()
            db.refresh(leave_request)  # Refresh to get updated data

            formatted_response = LeaveRequestService._format_leave_request(
                leave_request
            )

            await event_bus.publish(
                Event(
                    type=NotificationEventType.LEAVE_RESPONDED,
                    data={
                        "leave_request": formatted_response,
                        "notification": notification.to_dict(),
                    },
                )
            )

            return formatted_response

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process leave request: {str(e)}",
            )

    @staticmethod
    async def cancel_leave_request(
        db: Session, request_id: int, employee_id: int
    ) -> dict:
        """Cancel leave request"""
        leave_request = LeaveRequestService.get_leave_request(db, request_id)

        if leave_request.employee_id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to cancel this request",
            )

        if leave_request.status != LeaveStatus.PENDING:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only cancel pending requests",
            )

        try:
            leave_request.cancel()
            db.commit()

            return {"message": "Leave request cancelled successfully"}

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to cancel leave request: {str(e)}",
            )
