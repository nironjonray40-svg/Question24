import json
import urllib.request
import urllib.parse
import http.cookiejar
import sys
import time

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"

cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

def make_request(path, method='GET', data=None):
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

print("========================================")
print("TESTING FULL ADMIN CONTROL SYSTEM")
print("========================================")

# 1. Super Admin Login
print("\n[1] Testing Super Admin Login (01700000000)...")
status, res, raw = make_request("/api/auth/login", method="POST", data={
    "mobile": "01700000000",
    "password": "admin123"
})
print(f"Status: {status}, Response: {res}")
assert status == 200, f"Expected 200, got {status}"
assert res['success'] is True
assert res['user']['is_admin'] is True, "Super Admin must have is_admin=True"
super_admin_id = res['user']['id']
print(f"✓ Super Admin Login PASSED with is_admin=True (ID: {super_admin_id})")

# 2. Access Admin Panel View
print("\n[2] Testing Admin Panel HTML Page (/admin)...")
status, _, html = make_request("/admin")
if status != 200:
    print(f"Error accessing /admin: {status}\n{html[:1000]}")
assert status == 200, f"Expected 200, got {status}"
assert "অ্যাডমিন কন্ট্রোল হাব" in html
assert "১-ক্লিক সম্পূর্ণ ব্যাকআপ" in html
print("✓ Admin Panel View loaded successfully")

# 3. System Stats API
print("\n[3] Testing System Stats API (/api/admin/system-stats)...")
status, stats_res, _ = make_request("/api/admin/system-stats")
print(f"Status: {status}, Stats: {stats_res}")
assert status == 200
assert stats_res['success'] is True
assert 'total_users' in stats_res['stats']
assert 'total_questions' in stats_res['stats']
print(f"✓ System Stats PASSED: {stats_res['stats']['total_users']} Users, {stats_res['stats']['total_questions']} Questions")

# 4. Register a new user (Teacher)
test_mobile = f"018{int(time.time()) % 100000000:08d}"
print(f"\n[4] Registering a new teacher ({test_mobile})...")
status, reg_res, _ = make_request("/api/auth/register", method="POST", data={
    "name": "সহকারী শিক্ষক টেস্ট",
    "mobile": test_mobile,
    "password": "teacherpass123",
    "role": "সহকারী শিক্ষক"
})
print(f"Register Status: {status}")
assert status == 200
test_user_id = reg_res['user']['id']
assert reg_res['user']['is_admin'] is False, "New teacher should initially NOT be admin"
print(f"✓ Test Teacher registered with ID: {test_user_id} and is_admin=False")

# 5. Promote Teacher to Admin
print(f"\n[5] Promoting Teacher ID {test_user_id} to Admin via /api/admin/toggle-role/{test_user_id}...")
status, toggle_res, _ = make_request(f"/api/admin/toggle-role/{test_user_id}", method="POST")
print(f"Status: {status}, Response: {toggle_res}")
assert status == 200
assert toggle_res['success'] is True
assert toggle_res['is_admin'] is True
print("✓ Promotion to Admin PASSED!")

# 6. Toggle Status (Active -> Inactive -> Active)
print(f"\n[6] Toggling Status for User ID {test_user_id}...")
status, status_res, _ = make_request(f"/api/admin/toggle-status/{test_user_id}", method="POST")
assert status == 200
assert status_res['status'] == 'inactive'
print(f"✓ Status toggled to inactive: {status_res['message']}")

status, status_res, _ = make_request(f"/api/admin/toggle-status/{test_user_id}", method="POST")
assert status == 200
assert status_res['status'] == 'active'
print(f"✓ Status toggled back to active: {status_res['message']}")

# 7. Reset Password
print(f"\n[7] Resetting Password for User ID {test_user_id}...")
status, pass_res, _ = make_request(f"/api/admin/reset-user-password/{test_user_id}", method="POST", data={
    "password": "newadminpassword2026"
})
assert status == 200
assert pass_res['success'] is True
print("✓ Password reset PASSED!")

# 8. Full Backup Data Download
print("\n[8] Testing Full System JSON Backup (/api/admin/backup-data)...")
status, backup_json, raw_bk = make_request("/api/admin/backup-data")
if status != 200:
    print(f"Backup Error ({status}): {backup_json or raw_bk[:1000]}")
assert status == 200
assert backup_json['system_name'] is not None
assert 'summary' in backup_json
assert 'users' in backup_json
assert 'classes' in backup_json
assert 'subjects' in backup_json
print(f"✓ System Backup PASSED! Summary: {backup_json['summary']}")

# 9. Super Admin Demote Protection
print(f"\n[9] Testing Super Admin protection against demotion (User ID {super_admin_id})...")
status, protect_res, _ = make_request(f"/api/admin/toggle-role/{super_admin_id}", method="POST")
print(f"Status: {status}, Response: {protect_res}")
assert status == 400
assert "সুপার অ্যাডমিন" in protect_res['message']
print("✓ Super Admin demotion prevented properly!")

print("\n========================================")
print("ALL ADMIN SYSTEM TESTS PASSED SUCCESSFULLY! 100%")
print("========================================")
