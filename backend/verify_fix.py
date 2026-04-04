import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.core.database import async_session
from sqlalchemy import select
from app.models.user import User, UserRole, UserRoleAssignment
from app.models.academic import CourseSection
from sqlalchemy.orm import selectinload

async def verify():
    async with async_session() as db:
        print("Verifying API data loading...")
        
        # 2. Test get_section_enrollments logic
        from app.models.people import Enrollment, Student
        
        # Get a section with enrollments
        stmt = (
            select(Enrollment)
            .limit(1)
        )
        result = await db.execute(stmt)
        enrollment_sample = result.scalar_one_or_none()
        
        if not enrollment_sample:
            print("No enrollments found to test.")
            return

        section_id = enrollment_sample.section_id
        print(f"Testing enrollments for Section ID: {section_id}")

        query = (
            select(Enrollment)
            .join(Student, Enrollment.student_id == Student.student_id)
            .join(User, Student.student_id == User.user_id)
            .options(
                selectinload(Enrollment.student).selectinload(Student.user),
                selectinload(Enrollment.section).selectinload(CourseSection.course),
                selectinload(Enrollment.section).selectinload(CourseSection.term),
                selectinload(Enrollment.section).selectinload(CourseSection.room),
            )
            .where(Enrollment.section_id == section_id)
        )
        
        result = await db.execute(query)
        enrollments = result.scalars().all()
        
        print(f"Found {len(enrollments)} enrollments.")
        
        for e in enrollments:
            print(f"Enrollment {e.enrollment_id}:")
            print(f"  - Student: {e.student.user.personal_info.first_name if e.student and e.student.user and e.student.user.personal_info else 'Unknown'}")
            print(f"  - Section Term: {e.section.term.term_name if e.section and e.section.term else 'None'}")
            print(f"  - Section Room: {e.section.room.room_number if e.section and e.section.room else 'None'}")
            
            if e.section and e.section.term:
                 print("  [OK] Term loaded.")
            else:
                 print("  [ERROR] Term missing!")

if __name__ == "__main__":
    asyncio.run(verify())
