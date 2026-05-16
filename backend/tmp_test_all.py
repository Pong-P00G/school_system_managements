"""Test all API endpoints."""
import httpx
import sys

BASE = "http://localhost:8000/api/v1"
TOKEN = None

def login():
    global TOKEN
    r = httpx.post(f"{BASE}/auth/login", json={"username": "superadmin", "password": "SuperAdmin@123"}, timeout=10)
    if r.status_code == 200:
        TOKEN = r.json()["access_token"]
        print(f"[OK] LOGIN: {r.status_code}")
        return True
    else:
        print(f"[FAIL] LOGIN: {r.status_code} - {r.text}")
        return False

def headers():
    return {"Authorization": f"Bearer {TOKEN}"}

def test(method, path, expected=None, json_data=None, label=None):
    """Test an endpoint and return response."""
    url = f"{BASE}{path}"
    display = label or f"{method.upper()} {path}"
    try:
        kwargs = {"headers": headers(), "timeout": 10}
        if json_data is not None:
            kwargs["json"] = json_data
        r = getattr(httpx, method)(url, **kwargs)
        status = r.status_code
        ok = status < 400 if expected is None else status == expected
        symbol = "[OK]" if ok else "[FAIL]"
        detail = ""
        if not ok:
            detail = f" - {r.text[:100]}"
        print(f"  {symbol} {display}: {status}{detail}")
        return r
    except Exception as e:
        print(f"  [FAIL] {display}: ERROR - {e}")
        return None

def main():
    print("=" * 60)
    print("SCHOOL MANAGEMENT SYSTEM - API ENDPOINT TEST")
    print("=" * 60)
    
    if not login():
        print("\nCannot proceed without login.")
        sys.exit(1)
    
    # --- Health ---
    print("\n[Health]")
    test("get", "/health")
    test("get", "/health/db")
    
    # --- Auth ---
    print("\n[Auth]")
    test("post", "/auth/login", json_data={"username": "superadmin", "password": "SuperAdmin@123"}, label="POST /auth/login")
    
    # --- Users ---
    print("\n[Users]")
    test("get", "/users/")
    test("get", "/users/me", label="GET /users/me")
    
    # --- Departments ---
    print("\n[Departments]")
    r = test("get", "/departments/")
    dept_id = None
    if r and r.status_code == 200:
        data = r.json()
        depts = data.get("departments", data) if isinstance(data, dict) else data
        if depts and len(depts) > 0:
            dept_id = depts[0].get("department_id")
    if dept_id:
        test("get", f"/departments/{dept_id}")
    
    # --- Programs ---
    print("\n[Programs]")
    r = test("get", "/programs/")
    prog_id = None
    if r and r.status_code == 200:
        data = r.json()
        progs = data.get("programs", data) if isinstance(data, dict) else data
        if progs and len(progs) > 0:
            prog_id = progs[0].get("program_id")
    if prog_id:
        test("get", f"/programs/{prog_id}")
        test("get", f"/programs/{prog_id}/students")
    
    # --- Courses ---
    print("\n[Courses]")
    r = test("get", "/courses/")
    course_id = None
    if r and r.status_code == 200:
        data = r.json()
        courses = data.get("courses", data) if isinstance(data, dict) else data
        if courses and len(courses) > 0:
            course_id = courses[0].get("course_id")
    if course_id:
        test("get", f"/courses/{course_id}")
    
    # --- Students ---
    print("\n[Students]")
    r = test("get", "/students/")
    student_id = None
    if r and r.status_code == 200:
        data = r.json()
        students = data.get("students", data) if isinstance(data, dict) else data
        if students and len(students) > 0:
            student_id = students[0].get("student_id")
    if student_id:
        test("get", f"/students/{student_id}")
    
    # --- Faculty ---
    print("\n[Faculty]")
    r = test("get", "/faculty/")
    faculty_id = None
    if r and r.status_code == 200:
        data = r.json()
        facs = data.get("faculty", data) if isinstance(data, dict) else data
        if facs and len(facs) > 0:
            faculty_id = facs[0].get("faculty_id")
    if faculty_id:
        test("get", f"/faculty/{faculty_id}")
    
    # --- Staff ---
    print("\n[Staff]")
    r = test("get", "/staff/")
    staff_id = None
    if r and r.status_code == 200:
        data = r.json()
        staffs = data.get("staff", data) if isinstance(data, dict) else data
        if staffs and len(staffs) > 0:
            staff_id = staffs[0].get("staff_id")
    if staff_id:
        test("get", f"/staff/{staff_id}")
    
    # --- Terms ---
    print("\n[Academic Terms]")
    r = test("get", "/terms/")
    term_id = None
    if r and r.status_code == 200:
        data = r.json()
        terms = data.get("terms", data) if isinstance(data, dict) else data
        if terms and len(terms) > 0:
            term_id = terms[0].get("term_id")
    if term_id:
        test("get", f"/terms/{term_id}")
    
    # --- Sections ---
    print("\n[Course Sections]")
    r = test("get", "/sections/")
    section_id = None
    if r and r.status_code == 200:
        data = r.json()
        sections = data.get("sections", data) if isinstance(data, dict) else data
        if sections and len(sections) > 0:
            section_id = sections[0].get("section_id")
    if section_id:
        test("get", f"/sections/{section_id}")
    
    # --- Enrollments ---
    print("\n[Enrollments]")
    test("get", "/enrollments/")
    
    # --- Assignments ---
    print("\n[Assignments]")
    r = test("get", "/assignments/")
    assignment_id = None
    if r and r.status_code == 200:
        data = r.json()
        assigns = data.get("assignments", data) if isinstance(data, dict) else data
        if assigns and len(assigns) > 0:
            assignment_id = assigns[0].get("assignment_id")
    if assignment_id:
        test("get", f"/assignments/{assignment_id}")
    
    # --- Reviews ---
    print("\n[Reviews]")
    test("get", "/reviews/")
    
    # --- Attendance ---
    print("\n[Attendance]")
    if section_id:
        test("get", f"/attendance/section/{section_id}")
    
    # --- Notifications ---
    print("\n[Notifications]")
    test("get", "/notifications/")
    test("get", "/notifications/unread-count")
    
    # --- Roles ---
    print("\n[Roles]")
    r = test("get", "/roles/")
    
    # --- Permissions ---
    print("\n[Permissions]")
    test("get", "/permissions/pages")
    test("get", "/permissions/my-pages")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()
