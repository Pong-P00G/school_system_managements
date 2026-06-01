import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text

engine = create_async_engine('postgresql+psycopg://postgre:123@localhost:5432/school_system_db_v2')

async def check():
    async with AsyncSession(engine) as s:
        r = await s.execute(text("SELECT username, is_active, password_hash FROM users WHERE username ILIKE '%admin%' OR username ILIKE '%super%'"))
        rows = r.fetchall()
        if rows:
            for row in rows:
                print(f"username={row[0]}, is_active={row[1]}, hash_prefix={row[2][:20]}")
        else:
            print("No admin/superadmin user found in the database!")
            # Show all users
            r2 = await s.execute(text("SELECT username, is_active FROM users LIMIT 10"))
            all_users = r2.fetchall()
            print("All users:", all_users)

asyncio.run(check())
