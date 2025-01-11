from datetime import datetime, timedelta

import pytest
from app.features.shift_trade.service import ShiftTradeService
from app.models.schedule import Schedule
from app.models.schedule_enums import ScheduleStatus, ShiftType
from app.models.shift_trade import ResponseStatus, ShiftTrade, TradeStatus, TradeType
from fastapi import HTTPException


@pytest.fixture
def basic_schedule(db_session, test_user, test_admin):
    """Create a basic schedule for testing trades"""
    start_time = datetime.now().replace(hour=9, minute=0) + timedelta(days=1)
    schedule = Schedule(
        user_id=test_user.id,
        start_time=start_time,
        end_time=start_time + timedelta(hours=8),
        shift_type=ShiftType.MORNING,
        created_by=test_admin.id,
        status=ScheduleStatus.CONFIRMED,
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    return schedule


@pytest.fixture
def basic_trade_request(db_session, basic_schedule):
    """Create a basic trade request"""
    return {
        "type": TradeType.TRADE,
        "original_shift_id": basic_schedule.id,
        "reason": "Test trade request",
        "urgency": "NORMAL",
    }


@pytest.mark.asyncio
async def test_create_trade_request(db_session, test_user, basic_trade_request):
    """Test creating a new trade request"""
    trade = await ShiftTradeService.create_trade_request(
        db_session, basic_trade_request, test_user.id
    )

    assert trade is not None
    assert trade["author_id"] == test_user.id
    assert trade["status"] == TradeStatus.OPEN.value
    assert trade["type"] == TradeType.TRADE.value


@pytest.mark.asyncio
async def test_create_trade_request_with_invalid_shift(db_session, test_user):
    """Test creating trade request with invalid shift ID"""
    invalid_request = {
        "type": TradeType.TRADE,
        "original_shift_id": 99999,  # Non-existent shift
        "reason": "Test trade request",
    }

    with pytest.raises(HTTPException) as exc_info:
        await ShiftTradeService.create_trade_request(
            db_session, invalid_request, test_user.id
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_respond_to_trade_request(
    db_session, test_employee2, basic_schedule, basic_trade_request
):
    """Test responding to a trade request"""
    # Create initial trade request
    trade = await ShiftTradeService.create_trade_request(
        db_session, basic_trade_request, basic_schedule.user_id
    )

    # Create a schedule for the responding employee
    response_start_time = basic_schedule.start_time + timedelta(days=1)
    response_schedule = Schedule(
        user_id=test_employee2.id,
        start_time=response_start_time,
        end_time=response_start_time + timedelta(hours=8),
        shift_type=ShiftType.MORNING,
        status=ScheduleStatus.CONFIRMED,
        created_by=test_employee2.id,
    )
    db_session.add(response_schedule)
    db_session.commit()

    # Create response
    response_data = {
        "offered_shift_id": response_schedule.id,
        "content": "I can take this shift",
    }

    response = await ShiftTradeService.create_trade_response(
        db_session, trade["id"], response_data, test_employee2.id
    )

    assert response is not None
    assert response["status"] == ResponseStatus.PENDING.value


@pytest.mark.asyncio
async def test_accept_trade_response(
    db_session, test_user, test_employee2, basic_schedule, basic_trade_request
):
    """Test accepting a trade response"""
    # Create trade request
    trade = await ShiftTradeService.create_trade_request(
        db_session, basic_trade_request, test_user.id
    )

    # Create offered schedule
    response_start_time = basic_schedule.start_time + timedelta(days=1)
    offered_schedule = Schedule(
        user_id=test_employee2.id,
        start_time=response_start_time,
        end_time=response_start_time + timedelta(hours=8),
        shift_type=ShiftType.MORNING,
        status=ScheduleStatus.CONFIRMED,
        created_by=test_employee2.id,
    )
    db_session.add(offered_schedule)
    db_session.commit()

    # Create trade response
    response = await ShiftTradeService.create_trade_response(
        db_session,
        trade["id"],
        {"offered_shift_id": offered_schedule.id},
        test_employee2.id,
    )

    # Accept the response
    updated_response = await ShiftTradeService.update_response_status(
        db_session, trade["id"], response["id"], ResponseStatus.ACCEPTED, test_user.id
    )

    assert updated_response["status"] == ResponseStatus.ACCEPTED.value


@pytest.mark.asyncio
async def test_create_giveaway_request(db_session, test_user, basic_schedule):
    """Test creating a shift giveaway request"""
    giveaway_request = {
        "type": TradeType.GIVEAWAY,
        "original_shift_id": basic_schedule.id,
        "reason": "Cannot work this shift",
    }

    trade = await ShiftTradeService.create_trade_request(
        db_session, giveaway_request, test_user.id
    )

    assert trade is not None
    assert trade["type"] == TradeType.GIVEAWAY.value
    assert trade["status"] == TradeStatus.OPEN.value


@pytest.mark.asyncio
async def test_accept_giveaway(db_session, test_user, test_employee2, basic_schedule):
    """Test accepting a shift giveaway"""
    # Create giveaway request
    giveaway_request = {
        "type": TradeType.GIVEAWAY,
        "original_shift_id": basic_schedule.id,
        "reason": "Cannot work this shift",
    }

    trade = await ShiftTradeService.create_trade_request(
        db_session, giveaway_request, test_user.id
    )

    trade_obj = db_session.get(ShiftTrade, trade["id"])

    # Accept giveaway
    result = await ShiftTradeService.process_giveaway(
        db_session, trade_obj, test_employee2.id
    )

    assert result.status == TradeStatus.COMPLETED
