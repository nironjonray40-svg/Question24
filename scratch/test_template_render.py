import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from app import app, db
from models import User

client = app.test_client()

with app.app_context():
    print("Testing template rendering for admin and user management...")
    
    # 1. Login as Super Admin
    client.post('/api/auth/login', json={'mobile': '01794918384', 'password': 'admin123'})
    
    # 2. Render /admin
    resp = client.get('/admin')
    assert resp.status_code == 200, f"/admin returned {resp.status_code}"
    html = resp.get_data(as_text=True)
    assert 'ভূমিকা (Role) ও এক্সেস আপডেট' in html
    assert 'adminRoleModal' in html
    print("✓ /admin rendered successfully with adminRoleModal!")

    # 3. Render /settings/users
    resp2 = client.get('/settings/users')
    assert resp2.status_code == 200, f"/settings/users returned {resp2.status_code}"
    html2 = resp2.get_data(as_text=True)
    assert 'quickRoleModal' in html2
    assert 'ভূমিকা (Role) পরিবর্তন' in html2
    print("✓ /settings/users rendered successfully with quickRoleModal!")

    # 4. Render /settings/users as non-admin
    client2 = app.test_client()
    resp3 = client2.get('/settings/users')
    assert resp3.status_code == 200
    html3 = resp3.get_data(as_text=True)
    assert 'ইউজার তালিকা' in html3
    print("✓ /settings/users rendered safely for non-admin viewers!")

print("\nAll Template Tests Passed 100%!")
