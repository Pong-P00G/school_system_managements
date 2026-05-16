import httpx

client = httpx.Client(timeout=10)

# Login as superadmin
r = client.post('http://localhost:8000/api/v1/auth/login', json={'username': 'superadmin', 'password': 'SuperAdmin@123'})
token = r.json()['access_token']
user_id = '8ccf601f-4eb9-4631-95de-5939e54360b5'  # superadmin user_id
headers = {'Authorization': f'Bearer {token}'}

# Create a test notification
notification_data = {
    'user_id': user_id,
    'title': 'Test Notification',
    'message': 'This is a real-time test notification!',
    'notification_type': 'info'
}

r = client.post('http://localhost:8000/api/v1/notifications/', headers=headers, json=notification_data)
print(f"Status: {r.status_code}")
if r.status_code == 201:
    print(f"Notification created: {r.json()}")
else:
    print(f"Error: {r.text}")

client.close()
