import httpx
import uuid
import time
import sys

BASE_URL = "https://zenithsec.onrender.com"
TIMEOUT = 120.0  # extended timeout for Render cold start

def run_tests():
    print(f"[*] Testing API against: {BASE_URL}")
    print("-" * 50)
    
    # Wait for the backend to wake up using a simple GET request
    print("Wait: Waking up the server (this may take up to 60 seconds on Render)...")
    try:
        res = httpx.get(f"{BASE_URL}/", timeout=TIMEOUT)
        print(f"[GET /] Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"[GET /] Failed to wake up server: {e}")
        sys.exit(1)

    print("-" * 50)

    # Test Health Endpoint
    try:
        res = httpx.get(f"{BASE_URL}/api/health", timeout=15.0)
        print(f"[GET /api/health] Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"[GET /api/health] Failed: {e}")

    # Test Authentication (Register)
    test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    test_password = "SecurePassword123!"
    test_username = f"TestUser_{uuid.uuid4().hex[:4]}"
    
    user_data = {
        "email": test_email,
        "password": test_password,
        "username": test_username,
        "skill_level": "beginner"
    }

    access_token = None

    try:
        print(f"\n[POST /api/auth/register] Attempting to register {test_email}...")
        res = httpx.post(f"{BASE_URL}/api/auth/register", json=user_data, timeout=15.0)
        print(f"Status: {res.status_code}")
        
        if res.status_code == 201:
            print("[OK] User registration successful!")
            print(f"Response: {res.json()}")
        else:
            print(f"[ERR] Registration failed: {res.text}")
    except Exception as e:
        print(f"[ERR] Registration exception: {e}")

    # Test Authentication (Login)
    try:
        print(f"\n[POST /api/auth/login] Attempting login...")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        res = httpx.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=15.0)
        print(f"Status: {res.status_code}")
        
        if res.status_code == 200:
            print("[OK] Login successful!")
            access_token = res.json().get("access_token")
        else:
            print(f"[ERR] Login failed: {res.text}")
    except Exception as e:
        print(f"[ERR] Login exception: {e}")

    if not access_token:
        print("\n[WARN] Skipping authenticated endpoint tests because login failed.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    # Test Authenticated Route (/api/auth/me)
    try:
        print("\n[GET /api/auth/me] Fetching profile...")
        res = httpx.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=15.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(f"[OK] Profile: {res.json()}")
        else:
            print(f"[ERR] Profile failed: {res.text}")
    except Exception as e:
        print(f"[ERR] Profile exception: {e}")

    # Test Learning Hub
    try:
        print("\n[GET /api/learning/courses] Fetching courses...")
        res = httpx.get(f"{BASE_URL}/api/learning/courses", headers=headers, timeout=15.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            courses = res.json()
            if isinstance(courses, list):
                print(f"[OK] Found {len(courses)} courses.")
            else:
                print(f"[ERR] Courses unexpected response: {courses}")
        else:
            print(f"[ERR] Courses failed: {res.text}")
    except Exception as e:
        print(f"[ERR] Courses exception: {e}")
        
    print("\n[DONE] Test suite completed.")

if __name__ == "__main__":
    run_tests()
