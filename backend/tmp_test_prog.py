import httpx
BASE = 'http://localhost:8000/api/v1'
r = httpx.post(f'{BASE}/auth/login', json={'username':'superadmin','password':'SuperAdmin@123'}, timeout=5)
token = r.json()['access_token']
h = {'Authorization': f'Bearer {token}'}

# Create a test program
r = httpx.post(f'{BASE}/programs/', headers=h, json={
    'program_name': 'Test Notification Program',
    'program_code': 'TNP-001',
    'department_id': 6,
    'degree_level': 'Bachelor',
    'duration_years': 4,
    'total_credits_required': 120
}, timeout=10)
print(f'Create Program: {r.status_code}')
if r.status_code >= 400:
    print(r.text[:200])
else:
    prog = r.json()
    pid = prog["program_id"]
    print(f'  ID: {pid}, Name: {prog["program_name"]}')
    
    # Check notifications
    r2 = httpx.get(f'{BASE}/notifications/unread-count', headers=h, timeout=5)
    print(f'Unread count: {r2.json()}')
    
    # Check latest notification
    r3 = httpx.get(f'{BASE}/notifications/?limit=1', headers=h, timeout=5)
    notifs = r3.json()
    if notifs.get("notifications"):
        n = notifs["notifications"][0]
        print(f'Latest notification: {n["title"]} - {n["message"]}')
    
    # Clean up
    r4 = httpx.delete(f'{BASE}/programs/{pid}', headers=h, timeout=5)
    print(f'Delete Program: {r4.status_code}')
