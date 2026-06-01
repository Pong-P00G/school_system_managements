import asyncio
import selectors
import sys
import uuid
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

DATABASE_URL = "postgresql+psycopg://postgres:123@localhost:5432/school_system_db_v2"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed():
    engine = create_async_engine(DATABASE_URL)
    async with AsyncSession(engine) as session:
        # Check if superadmin already exists
        result = await session.execute(
            text("SELECT user_id FROM users WHERE username = 'superadmin'")
        )
        existing = result.fetchone()
        if existing:
            print(f"superadmin already exists: user_id={existing[0]}")
            return

        user_id = str(uuid.uuid4())
        password_hash = pwd_context.hash("SuperAdmin@123")

        # Insert user
        await session.execute(text("""
            INSERT INTO users (user_id, username, email, password_hash, is_active, is_verified)
            VALUES (:uid, 'superadmin', 'superadmin@school.local', :ph, true, true)
        """), {"uid": user_id, "ph": password_hash})

        # Ensure super-admin role exists with level 0 (highest privilege)
        await session.execute(text("""
            INSERT INTO user_roles (role_name, description, is_system_role, role_level)
            VALUES ('super-admin', 'Super Administrator', true, 0)
            ON CONFLICT (role_name) DO UPDATE SET role_level = 0, is_system_role = true
        """))

        # Get role_id
        role_result = await session.execute(
            text("SELECT role_id FROM user_roles WHERE role_name = 'super-admin'")
        )
        role_id = role_result.scalar_one()

        # Assign role
        await session.execute(text("""
            INSERT INTO user_role_assignments (user_id, role_id, is_active)
            VALUES (:uid, :rid, true)
            ON CONFLICT (user_id, role_id) DO NOTHING
        """), {"uid": user_id, "rid": role_id})

        await session.commit()
        print(f"✅ superadmin created! user_id={user_id}")
        print("   username: superadmin")
        print("   password: SuperAdmin@123")

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

asyncio.run(seed())
