import json
import urllib.request
import urllib.parse
import http.cookiejar
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

def create_client():
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))
    
    def req_fn(path, method='GET', data=None):
        url = f"{BASE_URL}{path}"
        headers = {}
        payload = None
        if data is not None:
            payload = json.dumps(data).encode('utf-8')
            headers['Content-Type'] = 'application/json'
        req = urllib.request.Request(url, data=payload, headers=headers, method=method)
        try:
            with opener.open(req) as resp:
                content = resp.read().decode('utf-8')
                try:
                    return resp.status, json.loads(content), content
                except Exception:
                    return resp.status, None, content
        except urllib.error.HTTPError as e:
            err_content = e.read().decode('utf-8')
            try:
                return e.code, json.loads(err_content), err_content
            except Exception:
                return e.code, None, err_content
    return req_fn

print("==================================================")
print("TESTING SUPER ADMIN ROLE UPDATE & SECURITY SYSTEM")
print("==================================================")

admin_client = create_client()
teacher_client = create_client()

# 1. Super Admin Login
print("\n[1] Logging in as Super Admin (01794918384)...")
status, res, _ = admin_client("/api/auth/login", method="POST", data={
    "mobile": "01794918384",
    "password": "admin123"
})
print(f"Status: {status}, User: {res['user']['name']} ({res['user']['role']})")
assert status == 200
assert res['user']['is_admin'] is True
assert res['user']['is_super_admin'] is True
super_admin_id = res['user']['id']
print("✓ Super Admin authenticated successfully!")

# 2. Register a new teacher
test_mobile = f"018{int(time.time() * 1000) % 100000000:08d}"
test_pass = "teacher1234"
print(f"\n[2] Registering new test teacher with mobile {test_mobile}...")
status, reg_res, _ = admin_client("/api/auth/register", method="POST", data={
    "name": "মো: জহিরুল ইসলাম (টেস্ট)",
    "mobile": test_mobile,
    "password": test_pass,
    "role": "সহকারী শিক্ষক"
})
assert status == 200
test_user_id = reg_res['user']['id']
print(f"✓ Registered User ID: {test_user_id}, Initial Role: {reg_res['user']['role']}")

# 3. Super Admin Updates Role: Senior Teacher
print(f"\n[3] Super Admin updating User {test_user_id} role to 'সিনিয়র শিক্ষক'...")
status, update_res, _ = admin_client(f"/api/admin/update-role/{test_user_id}", method="POST", data={
    "role": "সিনিয়র শিক্ষক"
})
print(f"Status: {status}, Response: {update_res['message']}")
assert status == 200
assert update_res['success'] is True
assert update_res['role'] == 'সিনিয়র শিক্ষক'
print("✓ Role update to 'সিনিয়র শিক্ষক' PASSED!")

# 4. Super Admin Updates Role: Exam Committee / Moderator
print(f"\n[4] Super Admin updating User {test_user_id} role to 'পরীক্ষা কমিটি / মডারেটর'...")
status, update_res, _ = admin_client(f"/api/admin/update-role/{test_user_id}", method="POST", data={
    "role": "পরীক্ষা কমিটি / মডারেটর",
    "is_admin": False
})
assert status == 200
assert update_res['role'] == 'পরীক্ষা কমিটি / মডারেটর'
print("✓ Role update to 'পরীক্ষা কমিটি / মডারেটর' PASSED!")

# 5. Super Admin Updates Role: Headmaster (with Admin privilege)
print(f"\n[5] Super Admin updating User {test_user_id} role to 'প্রধান শিক্ষক'...")
status, update_res, _ = admin_client(f"/api/admin/update-role/{test_user_id}", method="POST", data={
    "role": "প্রধান শিক্ষক",
    "is_admin": True
})
assert status == 200
assert update_res['is_admin'] is True
print("✓ Role update to 'প্রধান শিক্ষক' with is_admin=True PASSED!")

# 6. Super Admin Updates Role: Custom Role
print(f"\n[6] Super Admin updating User {test_user_id} to Custom Role 'পরীক্ষা মূল্যায়ন সমন্বয়ক'...")
status, update_res, _ = admin_client(f"/api/admin/update-role/{test_user_id}", method="POST", data={
    "role": "পরীক্ষা মূল্যায়ন সমন্বয়ক",
    "is_admin": False
})
assert status == 200
assert update_res['role'] == "পরীক্ষা মূল্যায়ন সমন্বয়ক"
print("✓ Custom role update PASSED!")

# 7. Non-Super Admin Security Verification
print(f"\n[7] Logging in as regular teacher ({test_mobile}) to test authorization restrictions...")
status, t_login_res, _ = teacher_client("/api/auth/login", method="POST", data={
    "mobile": test_mobile,
    "password": test_pass
})
assert status == 200
print(f"Teacher logged in: {t_login_res['user']['name']}")

# Attempt 7a: Teacher trying to update role via /api/admin/update-role
print("\n[7a] Regular user attempting to update role via /api/admin/update-role (MUST BE FORBIDDEN 403)...")
status, err_res, raw_err = teacher_client(f"/api/admin/update-role/{test_user_id}", method="POST", data={
    "role": "সুপার অ্যাডমিন"
})
print(f"Status: {status}, Message: {err_res.get('message') if err_res else raw_err}")
assert status == 403, f"Expected 403 Forbidden, got {status}"
assert "শুধুমাত্র" in err_res['message']
print("✓ Security Check 7a PASSED: Regular user blocked from /api/admin/update-role with 403 Forbidden!")

# Attempt 7b: Teacher trying to toggle role via /api/admin/toggle-role
print("\n[7b] Regular user attempting to toggle role via /api/admin/toggle-role (MUST BE FORBIDDEN 403)...")
status, err_res, _ = teacher_client(f"/api/admin/toggle-role/{test_user_id}", method="POST")
print(f"Status: {status}, Message: {err_res.get('message')}")
assert status == 403, f"Expected 403 Forbidden, got {status}"
print("✓ Security Check 7b PASSED: Regular user blocked from /api/admin/toggle-role with 403 Forbidden!")

# Attempt 7c: Teacher trying to change role via /api/users/edit
print("\n[7c] Regular user attempting to change role via /api/users/edit (MUST BE FORBIDDEN 403)...")
status, err_res, _ = teacher_client(f"/api/users/edit/{test_user_id}", method="POST", data={
    "role": "অ্যাডমিন / পরিচালক"
})
print(f"Status: {status}, Message: {err_res.get('message')}")
assert status == 403, f"Expected 403 Forbidden, got {status}"
print("✓ Security Check 7c PASSED: Regular user blocked from changing role in /api/users/edit with 403 Forbidden!")

# 8. Super Admin Protection from Demotion
print(f"\n[8] Testing Root Super Admin protection (User ID: {super_admin_id})...")
status, demote_res, _ = admin_client(f"/api/admin/update-role/{super_admin_id}", method="POST", data={
    "role": "সহকারী শিক্ষক"
})
print(f"Status: {status}, Response: {demote_res.get('message')}")
assert status == 400
assert "ডিমোট করা যাবে না" in demote_res['message'] or "সুপার অ্যাডমিন" in demote_res['message']
print("✓ Security Check 8 PASSED: Root Super Admin account protected from demotion!")

print("\n==================================================")
print("ALL SUPER ADMIN ROLE UPDATE TESTS PASSED! 100% SUCCESS")
print("==================================================")
