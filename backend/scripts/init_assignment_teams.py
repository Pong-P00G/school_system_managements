import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import engine, Base
# Import form app.models to trigger loading of all models correctly
from app.models import AssignmentTeam, AssignmentTeamMember, Assignment 

async def init_db():
    print("Initializing database tables...")
    async with engine.begin() as conn:
        # Create all tables. Existing tables will be skipped.
        await conn.run_sync(Base.metadata.create_all)
    
    print("Tables created successfully.")

if __name__ == "__main__":
    asyncio.run(init_db())
