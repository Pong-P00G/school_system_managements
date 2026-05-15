import asyncio
from app.core.database import engine
from sqlalchemy import text

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT conname, pg_get_constraintdef(oid) FROM pg_constraint WHERE conname LIKE '%degree%' OR conname LIKE '%chk%'"))
        rows = result.fetchall()
        print("Constraints found:")
        for r in rows:
            print(r)
    await engine.dispose()

asyncio.run(check())
