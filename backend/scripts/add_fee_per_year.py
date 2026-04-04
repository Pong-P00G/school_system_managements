import asyncio
import sys
import os
from sqlalchemy import text

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine

async def add_column():
    print("Adding fee_per_year column to programs table...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE programs ADD COLUMN fee_per_year NUMERIC(10, 2) DEFAULT 0.00;"))
            print("Column added successfully.")
        except Exception as e:
            print(f"Error adding column (might already exist): {e}")

if __name__ == "__main__":
    asyncio.run(add_column())
