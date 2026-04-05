import httpx
import uuid
import time

BASE_URL = "https://zenithsec.onrender.com"

def run_tests():
    print(f"🚀 Testing API against: {BASE_URL}")
    print("-" * 50)
    
    # 1. Test Root Endpoint
    try:
        res = httpx.get(f"{BASE_URL}/", timeout=10.0)
        print(f"[GET /] Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"[GET /] Failed: {e}")

    # 2. Test Health Endpoint
    try:
        res = httpx.get(f"{BASE_URL}/api/health", timeout=10.0)
        print(f"[GET /api/health] Status: {res.status_code}")
        print(f"Response: {res.json()}")
    except Exception as e:
        print(f"[GET /api/health] Failed: {e}")

    # 3. Test Authentication (Register)
    # Generate a unique dummy email so we don't hit duplicates
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
            print("✅ User registration successful!")
            print(f"Response: {res.json()}")
        else:
            print(f"❌ Registration failed: {res.text}")
    except Exception as e:
        print(f"❌ Registration exception: {e}")

    # 4. Test Authentication (Login)
    try:
        print(f"\n[POST /api/auth/login] Attempting login...")
        login_data = {
            "email": test_email,
            "password": test_password
        }
        res = httpx.post(f"{BASE_URL}/api/auth/login", json=login_data, timeout=10.0)
        print(f"Status: {res.status_code}")
        
        if res.status_code == 200:
            print("✅ Login successful!")
            access_token = res.json().get("access_token")
        else:
            print(f"❌ Login failed: {res.text}")
    except Exception as e:
        print(f"❌ Login exception: {e}")

    if not access_token:
        print("\n⚠️ Skipping authenticated endpoint tests because login failed.")
        return

    headers = {"Authorization": f"Bearer {access_token}"}

    # 5. Test Authenticated Route (/api/auth/me)
    try:
        print("\n[GET /api/auth/me] Fetching profile...")
        res = httpx.get(f"{BASE_URL}/api/auth/me", headers=headers, timeout=10.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            print(f"✅ Profile: {res.json()}")
        else:
            print(f"❌ Profile failed: {res.text}")
    except Exception as e:
        print(f"❌ Profile exception: {e}")

    # 6. Test Learning Hub
    try:
        print("\n[GET /api/learning/courses] Fetching courses...")
        res = httpx.get(f"{BASE_URL}/api/learning/courses", headers=headers, timeout=10.0)
        print(f"Status: {res.status_code}")
        if res.status_code == 200:
            courses = res.json()
            print(f"✅ Found {len(courses)} courses.")
        else:
            print(f"❌ Courses failed: {res.text}")
    except Exception as e:
        print(f"❌ Courses exception: {e}")
        
    print("\n🎉 Test suite completed.")

if __name__ == "__main__":
    run_tests()
