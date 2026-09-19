import urllib.request
import json
import http.cookiejar
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:5000"
cookie_jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cookie_jar))

# Login as Super Admin
req = urllib.request.Request(
    f"{BASE_URL}/api/auth/login",
    data=json.dumps({"mobile": "01794918384", "password": "admin123"}).encode('utf-8'),
    headers={"Content-Type": "application/json"},
    method="POST"
)
with opener.open(req) as resp:
    print("Login:", resp.status)

routes = [
    '/dashboard',
    '/admin',
    '/admin/panel',
    '/questions',
    '/api/questions?page=1&per_page=50&paginate=true',
    '/school-profile',
    '/settings',
    '/users',
    '/saved-papers',
    '/api/admin/system-stats'
]

for r in routes:
    with opener.open(f"{BASE_URL}{r}") as resp:
        content = resp.read().decode('utf-8')
        print(f"✓ Route {r:<50} -> HTTP {resp.status} (Length: {len(content)} chars)")
