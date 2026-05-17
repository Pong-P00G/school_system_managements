"""Pytest configuration and fixtures for backend tests.

Provides:
- Async HTTP client for testing FastAPI endpoints
- Auth fixtures (registered users with tokens for each role)
- Composite fixtures for common test scenarios
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Windows requires SelectorEventLoop for psycopg async mode
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.main import app
from app.core.database import engine

from .helpers import (
    create_department,
    login_user,
    register_user,
    setup_academic_graph,
)


# ---------------------------------------------------------------------------
# Session-scoped event loop — prevents "Event loop is closed" errors
# when asyncpg connections try to clean up after the test loop is destroyed.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.run_until_complete(engine.dispose())
    loop.close()


# ---------------------------------------------------------------------------
# Basic test fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# Unique suffix per test session
# ---------------------------------------------------------------------------


@pytest.fixture
def suffix() -> str:
    """Return a unique hex suffix for use in test data creation."""
    return uuid.uuid4().hex[:10]


# ---------------------------------------------------------------------------
# Auth fixtures — registered users with login tokens
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_user(client, suffix: str) -> dict:
    """Register an admin user and return user data + token."""
    user = await register_user(client, f"{suffix}_admin")
    token_data = await login_user(client, user["username"])
    return {**user, "token": token_data["access_token"]}


@pytest_asyncio.fixture
async def student_user(client, suffix: str) -> dict:
    """Register a user with a student profile and return user + token."""
    # First create the academic graph needed for student
    acad = await setup_academic_graph(client, f"{suffix}_stu")
    user = await register_user(client, f"{suffix}_stu")
    from .helpers import create_student
    student = await create_student(
        client, f"{suffix}_stu", user["user_id"], acad["prog_id"],
    )
    token_data = await login_user(client, user["username"])
    return {
        **user,
        "student_id": student["student_id"],
        "academic": acad,
        "token": token_data["access_token"],
    }


@pytest_asyncio.fixture
async def faculty_user(client, suffix: str) -> dict:
    """Register a user with a faculty profile and return user + token."""
    dept = await create_department(client, f"{suffix}_d")
    dept_id = dept["department_id"]

    user = await register_user(client, f"{suffix}_fac")
    from .helpers import create_faculty
    faculty = await create_faculty(
        client, f"{suffix}_fac", user["user_id"], dept_id,
    )
    token_data = await login_user(client, user["username"])
    return {
        **user,
        "faculty_id": faculty["faculty_id"],
        "department_id": dept_id,
        "token": token_data["access_token"],
    }


@pytest_asyncio.fixture
async def staff_user(client, suffix: str) -> dict:
    """Register a user with a staff profile and return user + token."""
    user = await register_user(client, f"{suffix}_stf")
    from .helpers import create_staff
    staff = await create_staff(client, f"{suffix}_stf", user["user_id"])
    token_data = await login_user(client, user["username"])
    return {
        **user,
        "staff_id": staff["staff_id"],
        "token": token_data["access_token"],
    }


# ---------------------------------------------------------------------------
# Authorization header fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def admin_headers(admin_user: dict) -> dict[str, str]:
    """Authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_user['token']}"}


@pytest_asyncio.fixture
async def student_headers(student_user: dict) -> dict[str, str]:
    """Authorization headers for student user."""
    return {"Authorization": f"Bearer {student_user['token']}"}


@pytest_asyncio.fixture
async def faculty_headers(faculty_user: dict) -> dict[str, str]:
    """Authorization headers for faculty user."""
    return {"Authorization": f"Bearer {faculty_user['token']}"}


@pytest_asyncio.fixture
async def staff_headers(staff_user: dict) -> dict[str, str]:
    """Authorization headers for staff user."""
    return {"Authorization": f"Bearer {staff_user['token']}"}


# ---------------------------------------------------------------------------
# Composite domain fixtures
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def academic_graph(client, suffix: str) -> dict:
    """Full academic dependency graph (dept -> program -> course -> term -> section)."""
    return await setup_academic_graph(client, suffix)


# ---------------------------------------------------------------------------
# Helper needed for short UUID strings in fixtures above
# ---------------------------------------------------------------------------


def _short() -> str:
    return uuid.uuid4().hex[:4]
