import urllib.request
import urllib.parse
import http.cookiejar
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def run_live_server_tests():
    print("[1] Setting up Cookie Handler for session tracking...")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    
    # 1. Registration Test
    print("\n[2] Testing Registration via POST /api/auth/register...")
    reg_data = json.dumps({
        "name": "মো: আশরাফুল ইসলাম",
        "mobile": "01712998877",
        "password": "ashrafpass123",
        "role": "সিনিয়র শিক্ষক"
    }).encode('utf-8')
    
    req = urllib.request.Request(
        f"{BASE_URL}/api/auth/register",
        data=reg_data,
        headers={"Content-Type": "application/json"}
    )
    
    try:
        with opener.open(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print("Response Status:", resp.status)
            print("Response Body:", data)
            assert data.get('success') is True, "Registration failed"
            assert data['user']['name'] == "মো: আশরাফুল ইসলাম"
            print("✅ User registration successful!")
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        print("HTTP Error:", e.code, body)
        if e.code == 409:
            print("User already exists, continuing test...")
        else:
            raise e

    # 2. Access Settings Users Page with active session
    print("\n[3] Testing GET /settings/users with active session...")
    req_users = urllib.request.Request(f"{BASE_URL}/settings/users")
    with opener.open(req_users) as resp:
        html = resp.read().decode('utf-8')
        assert resp.status == 200
        assert "নিবন্ধিত ইউজার তালিকা" in html
        assert "01712998877" in html
        print("✅ /settings/users loaded successfully and contains user 01712998877!")

    # 3. Access /api/users/list
    print("\n[4] Testing GET /api/users/list...")
    req_api_users = urllib.request.Request(f"{BASE_URL}/api/users/list?search=01712998877")
    with opener.open(req_api_users) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Users count for 01712998877:", len(data['users']))
        assert len(data['users']) >= 1
        print("✅ /api/users/list returned matching user record!")

    # 4. Logout Test
    print("\n[5] Testing Logout via GET /logout...")
    req_logout = urllib.request.Request(f"{BASE_URL}/logout")
    with opener.open(req_logout) as resp:
        print("Logout status:", resp.status)
        print("✅ Successfully logged out!")

    # 5. Login Test with Mobile and Password
    print("\n[6] Testing Login via POST /api/auth/login...")
    login_data = json.dumps({
        "mobile": "01712998877",
        "password": "ashrafpass123"
    }).encode('utf-8')
    
    req_login = urllib.request.Request(
        f"{BASE_URL}/api/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    with opener.open(req_login) as resp:
        data = json.loads(resp.read().decode('utf-8'))
        print("Login Response:", data)
        assert data.get('success') is True, "Login failed"
        assert data['user']['name'] == "মো: আশরাফুল ইসলাম"
        print("✅ Successful login with Mobile and Password!")

    # 6. Access Dashboard after login
    print("\n[7] Testing GET /dashboard after login...")
    req_dash = urllib.request.Request(f"{BASE_URL}/dashboard")
    with opener.open(req_dash) as resp:
        html = resp.read().decode('utf-8')
        assert resp.status == 200
        assert "মো: আশরাফুল ইসলাম" in html or "ড্যাশবোর্ড" in html
        print("✅ Dashboard accessible with authenticated user!")

    print("\n=======================================================")
    print("🎉 ALL LIVE HTTP ENDPOINT TESTS PASSED SUCCESSFULLY! 🎉")
    print("=======================================================")

if __name__ == '__main__':
    run_live_server_tests()
