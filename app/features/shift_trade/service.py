from typing import List, Optional

from app.core.events import Event, event_bus
from app.features.notifications.events.types import NotificationEventType
from app.models.notification import Notification, NotificationPriority, NotificationType
from app.models.schedule import Schedule
from app.models.shift_trade import (
    ResponseStatus,
    ShiftTrade,
    ShiftTradeResponse,
    TradeStatus,
    TradeType,
)
from app.models.user import User
from fastapi import HTTPException, status
from sqlalchemy.orm import Session


class ShiftTradeService:
    @staticmethod
    async def _format_trade_response(response: ShiftTradeResponse) -> dict:
        """Format trade response for API response"""
        return {
            "id": response.id,
            "trade_request_id": response.trade_request_id,
            "respondent": {
                "id": response.respondent.id,
                "name": response.respondent.full_name,
                "position": response.respondent.position,
            },
            "offered_shift": {
                "id": response.offered_shift.id,
                "start_time": response.offered_shift.start_time.isoformat(),
                "end_time": response.offered_shift.end_time.isoformat(),
                "type": response.offered_shift.shift_type,
            },
            "content": response.content,
            "status": response.status,
            "created_at": response.created_at.isoformat(),
            "updated_at": (
                response.updated_at.isoformat() if response.updated_at else None
            ),
        }

    @staticmethod
    async def _format_trade_request(trade_request: ShiftTrade) -> dict:
        return {
            "id": trade_request.id,
            "type": trade_request.type,
            "author_id": trade_request.author_id,
            "original_shift_id": trade_request.original_shift_id,
            "preferred_shift_id": trade_request.preferred_shift_id,
            "reason": trade_request.reason,
            "status": trade_request.status,
            "urgency": trade_request.urgency,
            "created_at": trade_request.created_at,
            "author": {
                "id": trade_request.author.id,
                "name": trade_request.author.full_name,
                "position": trade_request.author.position,
            },
            "original_shift": {
                "id": trade_request.original_shift.id,
                "start_time": trade_request.original_shift.start_time.isoformat(),
                "end_time": trade_request.original_shift.end_time.isoformat(),
                "type": trade_request.original_shift.shift_type,
            },
        }

    @staticmethod
    def get_trade_requests(
        db: Session,
        status: Optional[str] = None,
        type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[ShiftTrade]:
        query = db.query(ShiftTrade)

        if status:
            query = query.filter(ShiftTrade.status == status)
        if type:
            query = query.filter(ShiftTrade.type == type)
        if search:
            # Search in user names or schedule details
            query = query.join(ShiftTrade.author).filter(
                User.full_name.ilike(f"%{search}%")
            )

        trades = query.order_by(ShiftTrade.created_at.desc()).all()

        # Convert to response format
        return [
            {
                "id": trade.id,
                "type": trade.type,
                "author_id": trade.author_id,
                "original_shift_id": trade.original_shift_id,
                "preferred_shift_id": trade.preferred_shift_id,
                "reason": trade.reason,
                "status": trade.status,
                "urgency": trade.urgency,
                "created_at": trade.created_at,
                "updated_at": trade.updated_at,
                "author": {
                    "id": trade.author.id,
                    "name": trade.author.full_name,
                    "position": trade.author.position,
                },
                "original_shift": {
                    "id": trade.original_shift.id,
                    "start_time": trade.original_shift.start_time.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "end_time": trade.original_shift.end_time.strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                    "type": trade.original_shift.shift_type,
                },
                "preferred_shift": (
                    {
                        "id": trade.preferred_shift.id,
                        "start_time": trade.preferred_shift.start_time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "end_time": trade.preferred_shift.end_time.strftime(
                            "%Y-%m-%d %H:%M"
                        ),
                        "type": trade.preferred_shift.shift_type,
                    }
                    if trade.preferred_shift
                    else None
                ),
                "responses": [
                    {
                        "id": response.id,
                        "respondent": {
                            "id": response.respondent.id,
                            "name": response.respondent.full_name,
                            "position": response.respondent.position,
                        },
                        "offered_shift": {
                            "id": response.offered_shift.id,
                            "start_time": response.offered_shift.start_time.strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "end_time": response.offered_shift.end_time.strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "type": response.offered_shift.shift_type,
                        },
                        "content": response.content,
                        "status": response.status,
                        "created_at": response.created_at,
                    }
                    for response in trade.responses
                ],
            }
            for trade in trades
        ]

    @staticmethod
    def get_trade_request(db: Session, trade_id: int) -> ShiftTrade:
        trade = db.query(ShiftTrade).filter(ShiftTrade.id == trade_id).first()
        if not trade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trade request not found"
            )
        return trade

    @staticmethod
    async def create_trade_request(
        db: Session, request_data: dict, user_id: int
    ) -> ShiftTrade:
        # Validate original shift belongs to user
        original_shift = (
            db.query(Schedule)
            .filter(
                Schedule.id == request_data["original_shift_id"],
                Schedule.user_id == user_id,
            )
            .first()
        )

        if not original_shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Original shift not found or doesn't belong to user",
            )

        # Check for existing active trade request
        if not await ShiftTradeService._check_schedule_availability(
            db, original_shift.id
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An active trade request already exists for this shift",
            )

        trade_request = ShiftTrade(author_id=user_id, **request_data)

        try:
            db.add(trade_request)
            db.commit()
            db.refresh(trade_request)

            return await ShiftTradeService._format_trade_request(trade_request)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def create_trade_response(
        db: Session, trade_id: int, response_data: dict, user_id: int
    ) -> ShiftTradeResponse:

        trade_request = ShiftTradeService.get_trade_request(db, trade_id)
        print(f"Processing trade response - Trade ID: {trade_id}")
        print(f"Trade request author: {trade_request.author_id}")
        print(f"Responding user: {user_id}")
        print(f"Response data: {response_data}")

        # Validate offered shift belongs to responding user
        offered_shift = (
            db.query(Schedule)
            .filter(
                Schedule.id == response_data["offered_shift_id"],
                Schedule.user_id == user_id,
            )
            .first()
        )

        print(f"Offered shift: {offered_shift}")

        if not offered_shift:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Offered shift not found or doesn't belong to user",
            )

        # Create response
        response = ShiftTradeResponse(
            trade_request_id=trade_id,
            respondent_id=user_id,
            offered_shift_id=response_data["offered_shift_id"],
            content=response_data.get("content", ""),
        )
        print(f"Created response object: {response.__dict__}")

        try:
            db.add(response)
            print("Response added to DB")
            db.commit()
            print("DB committed")
            db.refresh(response)
            print("Response refreshed")

            # Send notification to trade request author
            try:
                notification = Notification(
                    user_id=trade_request.author_id,
                    type=NotificationType.SHIFT_TRADE,
                    title="New Response to Your Trade Request",  # title 필드 필요
                    message=f"{response.respondent.full_name} has responded to your shift trade request",  # message 필드 필요
                    priority=NotificationPriority.HIGH,
                    data={  # content 대신 data 필드 사용
                        "trade_id": trade_id,
                        "response_id": response.id,
                        "type": "response_received",
                    },
                )
                print(f"Creating notification: {notification.__dict__}")
                db.add(notification)
                db.commit()
                print("Notification created successfully")

                # Event publishing
                try:
                    formatted_trade = await ShiftTradeService._format_trade_request(
                        trade_request
                    )
                    formatted_response = await ShiftTradeService._format_trade_response(
                        response
                    )

                    await event_bus.publish(
                        Event(
                            type=NotificationEventType.TRADE_RESPONDED,
                            data={
                                "trade": formatted_trade,
                                "response": formatted_response,
                            },
                        )
                    )
                    print("Event published successfully")
                except Exception as e:
                    print(f"Event publishing error: {str(e)}")
                    # Don't raise here to prevent transaction rollback

                return await ShiftTradeService._format_trade_response(response)
            except Exception as e:
                print(f"Notification error: {str(e)}")
            raise

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def update_response_status(
        db: Session, trade_id: int, response_id: int, status: str, user_id: int
    ) -> ShiftTradeResponse:
        trade_request = ShiftTradeService.get_trade_request(db, trade_id)
        print(
            f"Processing trade response - Trade ID: {trade_id}, Response ID: {response_id}, Status: {status}"
        )

        if trade_request.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the trade request author can update response status",
            )

        response = (
            db.query(ShiftTradeResponse)
            .filter(
                ShiftTradeResponse.id == response_id,
                ShiftTradeResponse.trade_request_id == trade_id,
            )
            .first()
        )

        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Trade response not found"
            )

        try:
            response.status = status
            if status == ResponseStatus.ACCEPTED:
                if trade_request.type == TradeType.TRADE:
                    print("Processing trade acceptance...")
                    await ShiftTradeService._process_trade_acceptance(
                        db, trade_request, response
                    )
                else:
                    print("Processing giveaway acceptance...")
                    await ShiftTradeService._process_giveaway_acceptance(
                        db, trade_request, response
                    )

            await ShiftTradeService._send_response_notifications(
                db, trade_request, response
            )
            db.commit()
            print("Trade response processed successfully")

            return await ShiftTradeService._format_trade_response(response)

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def cancel_trade_request(db: Session, trade_id: int, user_id: int):
        trade_request = ShiftTradeService.get_trade_request(db, trade_id)

        if trade_request.author_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the trade request author can cancel it",
            )

        if trade_request.status == TradeStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot cancel completed trade request",
            )

        try:
            # Notify all responders
            notifications = [
                Notification(
                    user_id=response.respondent_id,
                    type=NotificationType.SHIFT_TRADE,
                    title="Trade Request Cancelled",
                    message="A trade request you responded to has been cancelled",
                    priority=NotificationPriority.NORMAL,
                    data={"trade_id": trade_id, "type": "trade_cancelled"},
                )
                for response in trade_request.responses
            ]

            for notification in notifications:
                db.add(notification)

            db.delete(trade_request)
            db.commit()

            return {"message": "Trade request cancelled successfully"}

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
            )

    @staticmethod
    async def _process_trade_acceptance(
        db: Session, trade_request: ShiftTrade, response: ShiftTradeResponse
    ):
        # Swap schedules between users
        original_shift = trade_request.original_shift
        offered_shift = response.offered_shift

        # Store original user IDs before swap
        original_user_id = original_shift.user_id
        offered_user_id = offered_shift.user_id

        try:
            # Perform the swap
            original_shift.user_id = offered_user_id
            offered_shift.user_id = original_user_id

            # Update trade request status
            trade_request.status = TradeStatus.COMPLETED

            # Explicitly update both shifts
            db.add(original_shift)
            db.add(offered_shift)
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process trade acceptance: {str(e)}",
            )

    @staticmethod
    async def _process_giveaway_acceptance(
        db: Session, trade_request: ShiftTrade, response: ShiftTradeResponse
    ):
        # Transfer schedule to respondent
        trade_request.original_shift.user_id = response.respondent_id
        trade_request.status = TradeStatus.COMPLETED

    @staticmethod
    async def _check_schedule_availability(db: Session, schedule_id: int) -> bool:
        return (
            not db.query(ShiftTrade)
            .filter(
                ShiftTrade.original_shift_id == schedule_id,
                ShiftTrade.status == TradeStatus.OPEN,
            )
            .first()
        )

    @staticmethod
    async def _send_response_notifications(
        db: Session, trade_request: ShiftTrade, response: ShiftTradeResponse
    ):
        notifications = []
        if response.status == ResponseStatus.ACCEPTED:
            notifications.extend(
                [
                    Notification(
                        user_id=trade_request.author_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Trade Request Completed",
                        message="Your shift trade has been completed successfully",
                        priority=NotificationPriority.HIGH,
                        data={"trade_id": trade_request.id},
                    ),
                    Notification(
                        user_id=response.respondent_id,
                        type=NotificationType.SHIFT_TRADE,
                        title="Trade Response Accepted",
                        message="Your shift trade response has been accepted",
                        priority=NotificationPriority.HIGH,
                        data={"trade_id": trade_request.id},
                    ),
                ]
            )
        db.add_all(notifications)
