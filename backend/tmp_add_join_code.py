import asyncio
from app.core.database import engine
from sqlalchemy import text

async def add():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE course_sections ADD COLUMN join_code VARCHAR(8) UNIQUE;"))
            print("join_code column added successfully.")
        except Exception as e:
            print(f"Error: {e}")
    await engine.dispose()

asyncio.run(add())
