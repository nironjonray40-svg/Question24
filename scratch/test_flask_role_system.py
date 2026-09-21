import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from app import app, db, seed_database
from models import User

print("==================================================")
print("TESTING SUPER ADMIN ROLE UPDATE (FLASK TEST CLIENT)")
print("==================================================")

client = app.test_client()

with app.app_context():
    seed_database()
    # 1. Ensure Super Admin exists
    super_admin = User.query.filter_by(mobile="01794918384").first()
    assert super_admin is not None, "Super admin must exist"
    assert super_admin.is_super_admin_user is True
    print(f"[1] Verified Super Admin in DB: {super_admin.name} ({super_admin.mobile}) - SuperAdmin: {super_admin.is_super_admin_user}")

    # 2. Login as Super Admin
    login_resp = client.post('/api/auth/login', json={
        'mobile': '01794918384',
        'password': 'admin123'
    })
    assert login_resp.status_code == 200
    login_data = login_resp.get_json()
    assert login_data['success'] is True
    assert login_data['user']['is_super_admin'] is True
    print("[2] Super Admin login via test_client PASSED!")

    # 3. Create a test teacher
    reg_resp = client.post('/api/auth/register', json={
        'name': 'মোছা: মরিয়ম বেগম',
        'mobile': '01855667788',
        'password': 'password123',
        'role': 'সহকারী শিক্ষক'
    })
    assert reg_resp.status_code in [200, 409]
    user = User.query.filter_by(mobile='01855667788').first()
    assert user is not None
    user_id = user.id
    print(f"[3] Test teacher ID: {user_id}, Current Role: {user.role}")

    # 4. Super Admin Updates Role: 'সিনিয়র শিক্ষক'
    client.post('/api/auth/login', json={'mobile': '01794918384', 'password': 'admin123'})
    up_resp = client.post(f'/api/admin/update-role/{user_id}', json={
        'role': 'সিনিয়র শিক্ষক'
    })
    assert up_resp.status_code == 200
    up_data = up_resp.get_json()
    assert up_data['success'] is True
    assert up_data['role'] == 'সিনিয়র শিক্ষক'
    db.session.refresh(user)
    assert user.role == 'সিনিয়র শিক্ষক'
    print("[4] Role update to 'সিনিয়র শিক্ষক' PASSED!")

    # 5. Super Admin Updates Role: 'প্রধান শিক্ষক'
    up_resp2 = client.post(f'/api/admin/update-role/{user_id}', json={
        'role': 'প্রধান শিক্ষক',
        'is_admin': True
    })
    assert up_resp2.status_code == 200
    db.session.refresh(user)
    assert user.role == 'প্রধান শিক্ষক'
    assert user.is_admin is True
    print("[5] Role update to 'প্রধান শিক্ষক' (Admin=True) PASSED!")

    # 6. Super Admin Updates Role: 'পরীক্ষা কমিটি / মডারেটর'
    up_resp3 = client.post(f'/api/admin/update-role/{user_id}', json={
        'role': 'পরীক্ষা কমিটি / মডারেটর',
        'is_admin': False
    })
    assert up_resp3.status_code == 200
    db.session.refresh(user)
    assert user.role == 'পরীক্ষা কমিটি / মডারেটর'
    assert user.is_admin is False
    print("[6] Role update to 'পরীক্ষা কমিটি / মডারেটর' (Admin=False) PASSED!")

    # 7. Non-Super Admin Security Verification
    # Login as regular teacher
    teacher_client = app.test_client()
    t_login = teacher_client.post('/api/auth/login', json={
        'mobile': '01855667788',
        'password': 'password123'
    })
    assert t_login.status_code == 200
    print("[7] Logged in as regular teacher.")

    # Try to call /api/admin/update-role
    err_resp = teacher_client.post(f'/api/admin/update-role/{user_id}', json={
        'role': 'সুপার অ্যাডমিন'
    })
    assert err_resp.status_code == 403
    err_data = err_resp.get_json()
    assert err_data['success'] is False
    assert "শুধুমাত্র" in err_data['message']
    print(f"[7a] Regular teacher blocked from /api/admin/update-role: {err_data['message']}")

    # Try to call /api/admin/toggle-role
    err_resp2 = teacher_client.post(f'/api/admin/toggle-role/{user_id}')
    assert err_resp2.status_code == 403
    print(f"[7b] Regular teacher blocked from /api/admin/toggle-role: 403 Forbidden")

    # Try to change role via /api/users/edit
    err_resp3 = teacher_client.post(f'/api/users/edit/{user_id}', json={
        'name': 'মোছা: মরিয়ম বেগম',
        'role': 'সুপার অ্যাডমিন'
    })
    assert err_resp3.status_code == 403
    print(f"[7c] Regular teacher blocked from changing role in /api/users/edit: 403 Forbidden")

    # 8. Protection of Root Super Admin account from demotion
    client.post('/api/auth/login', json={'mobile': '01794918384', 'password': 'admin123'})
    protect_resp = client.post(f'/api/admin/update-role/{super_admin.id}', json={
        'role': 'সহকারী শিক্ষক'
    })
    assert protect_resp.status_code == 400
    print(f"[8] Root Super Admin demotion prevented: {protect_resp.get_json()['message']}")

    # Clean up test user
    db.session.delete(user)
    db.session.commit()

print("\n==================================================")
print("ALL FLASK TEST CLIENT ROLE TESTS PASSED 100%!")
print("==================================================")
