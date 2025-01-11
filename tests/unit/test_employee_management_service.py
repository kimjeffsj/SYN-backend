import pytest
from app.features.employee_management.schemas import (
    DepartmentCreate,
    EmployeeCreate,
    EmployeeUpdate,
    PositionCreate,
)
from app.features.employee_management.service import EmployeeManagementService
from fastapi import HTTPException


@pytest.fixture
def employee_data():
    """Basic employee data fixture"""
    return {
        "email": "newemployee@example.com",
        "full_name": "New Employee",
        "password": "testpass123",
        "department": "IT",
        "position": "Developer",
        "comment": "Test employee",
    }


@pytest.fixture
def department_data():
    """Department data fixture"""
    return {"name": "Engineering", "description": "Software Engineering Department"}


@pytest.fixture
def position_data():
    """Position data fixture"""
    return {
        "name": "Senior Developer",
        "description": "Senior Software Developer Position",
    }


@pytest.mark.asyncio
async def test_create_employee(db_session, employee_data):
    """Test employee creation"""
    employee = await EmployeeManagementService.create_employee(
        db_session, EmployeeCreate(**employee_data)
    )

    assert employee is not None
    assert employee.email == employee_data["email"]
    assert employee.full_name == employee_data["full_name"]
    assert employee.department == employee_data["department"]
    assert employee.position == employee_data["position"]
    assert employee.role == "employee"


@pytest.mark.asyncio
async def test_create_duplicate_employee(db_session, employee_data):
    """Test creating employee with duplicate email"""
    # Create first employee
    await EmployeeManagementService.create_employee(
        db_session, EmployeeCreate(**employee_data)
    )

    # Try to create duplicate
    with pytest.raises(HTTPException) as exc_info:
        await EmployeeManagementService.create_employee(
            db_session, EmployeeCreate(**employee_data)
        )

    assert exc_info.value.status_code == 400
    assert "Email already registered" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_update_employee(db_session, employee_data):
    """Test employee update"""
    # Create employee first
    employee = await EmployeeManagementService.create_employee(
        db_session, EmployeeCreate(**employee_data)
    )

    # Update data
    update_data = {
        "full_name": "Updated Name",
        "department": "Updated Dept",
        "position": "Updated Position",
    }

    updated_employee = await EmployeeManagementService.update_employee(
        db_session, employee.id, EmployeeUpdate(**update_data)
    )

    assert updated_employee.full_name == update_data["full_name"]
    assert updated_employee.department == update_data["department"]
    assert updated_employee.position == update_data["position"]


@pytest.mark.asyncio
async def test_get_employees_with_search(db_session, employee_data):
    """Test employee search functionality"""
    # Create test employee
    await EmployeeManagementService.create_employee(
        db_session, EmployeeCreate(**employee_data)
    )

    # Search by name
    results = await EmployeeManagementService.get_employees(
        db_session, search="New Employee"
    )
    assert len(results) == 1
    assert results[0].full_name == employee_data["full_name"]

    # Search by department
    results = await EmployeeManagementService.get_employees(db_session, search="IT")
    assert len(results) == 1
    assert results[0].department == employee_data["department"]


@pytest.mark.asyncio
async def test_department_management(db_session, department_data):
    """Test department CRUD operations"""
    # Create department
    department = await EmployeeManagementService.add_department(
        db_session, DepartmentCreate(**department_data)
    )
    assert department.name == department_data["name"]

    # Get departments
    departments = await EmployeeManagementService.get_departments(db_session)
    assert len(departments) == 1

    # Delete department
    await EmployeeManagementService.delete_department(db_session, department.id)
    departments = await EmployeeManagementService.get_departments(db_session)
    assert len(departments) == 0


@pytest.mark.asyncio
async def test_position_management(db_session, position_data):
    """Test position CRUD operations"""
    # Create position
    position = await EmployeeManagementService.add_position(
        db_session, PositionCreate(**position_data)
    )
    assert position.name == position_data["name"]

    # Get positions
    positions = await EmployeeManagementService.get_positions(db_session)
    assert len(positions) == 1

    # Delete position
    await EmployeeManagementService.delete_position(db_session, position.id)
    positions = await EmployeeManagementService.get_positions(db_session)
    assert len(positions) == 0


@pytest.mark.asyncio
async def test_department_constraint(db_session, employee_data, department_data):
    """Test department foreign key constraints"""
    # Create employee with non-existent department
    employee_data["department"] = "Non-existent"
    employee = await EmployeeManagementService.create_employee(
        db_session, EmployeeCreate(**employee_data)
    )

    # Create department
    department = await EmployeeManagementService.add_department(
        db_session, DepartmentCreate(**department_data)
    )

    # Update employee with valid department
    update_data = {"department": department_data["name"]}
    updated_employee = await EmployeeManagementService.update_employee(
        db_session, employee.id, EmployeeUpdate(**update_data)
    )

    assert updated_employee.department == department_data["name"]
