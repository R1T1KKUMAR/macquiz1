import os

import requests

BASE_URL = os.environ.get("MACQUIZ_BASE_URL", "http://localhost:8000")
EMAIL = os.environ.get("MACQUIZ_TEST_EMAIL", "admin@macquiz.com")
PASSWORD = os.environ.get("MACQUIZ_TEST_PASSWORD", "admin123")

login_response = requests.post(
    f"{BASE_URL}/api/v1/auth/login-json",
    json={"username": EMAIL, "password": PASSWORD},
    timeout=10,
)

if login_response.status_code == 200:
    token = login_response.json()["access_token"]
    print(f"Logged in as {EMAIL}")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/attempts/my-attempts",
        headers=headers,
        timeout=10,
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        attempts = response.json()
        print(f"Found {len(attempts)} attempts")
        for a in attempts:
            print(f"  Quiz: {a.get('quiz_title')}, Score: {a.get('score')}/{a.get('total_marks')}")
    else:
        print(f"Error: {response.text}")
else:
    print(f"Login failed: {login_response.status_code}")
    print(login_response.text)
