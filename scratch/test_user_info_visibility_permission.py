import os
import sys
import unittest
import json

# Set in-memory db before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, seed_database, get_permissions_for_role, get_current_user_permissions
from models import User, RolePermissionConfig

class UserInfoVisibilityPermissionTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            seed_database()

            # Create a test teacher user
            teacher = User(
                name="সহকারী শিক্ষক রহিম",
                mobile="01711223344",
                role="সহকারী শিক্ষক",
                status="active",
                is_admin=False
            )
            teacher.set_password("123456")
            db.session.add(teacher)

            # Create another user under "বিষয় শিক্ষক"
            subject_teacher = User(
                name="বিষয় শিক্ষক করিম",
                mobile="01755667788",
                role="বিষয় শিক্ষক",
                status="active",
                is_admin=False
            )
            subject_teacher.set_password("123456")
            db.session.add(subject_teacher)
            db.session.commit()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_01_role_permissions_includes_user_info(self):
        """Verify api_admin_get_role_permissions returns users_count and users list"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        res = self.client.get('/api/admin/role-permissions')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('role_permissions', data)

        role_map = {r['role_name']: r for r in data['role_permissions']}
        self.assertIn('সহকারী শিক্ষক', role_map)
        teacher_role = role_map['সহকারী শিক্ষক']
        self.assertIn('users_count', teacher_role)
        self.assertIn('users', teacher_role)
        self.assertGreaterEqual(teacher_role['users_count'], 1)
        user_names = [u['name'] for u in teacher_role['users']]
        self.assertIn('সহকারী শিক্ষক রহিম', user_names)

    def test_02_non_permitted_user_cannot_view_users(self):
        """User without can_view_users permission cannot view user list or API"""
        # Logged in as assistant teacher (can_view_users = False by default)
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'name': 'সহকারী শিক্ষক রহিম',
                'mobile': '01711223344',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        # 1. Access /settings/users (should redirect to dashboard)
        res_view = self.client.get('/settings/users', follow_redirects=False)
        self.assertEqual(res_view.status_code, 302)
        self.assertIn('/dashboard', res_view.location)

        # 2. Access /users (should redirect to dashboard)
        res_view2 = self.client.get('/users', follow_redirects=False)
        self.assertEqual(res_view2.status_code, 302)
        self.assertIn('/dashboard', res_view2.location)

        # 3. Call /api/users/list (should return 403 Forbidden)
        res_api = self.client.get('/api/users/list')
        self.assertEqual(res_api.status_code, 403)
        data = res_api.get_json()
        self.assertFalse(data['success'])
        self.assertIn('ইউজার তালিকা দেখার পারমিশন নেই', data['message'])

    def test_03_super_admin_updates_permission_action_to_allow_user_view(self):
        """Super Admin grants can_view_users to 'সহকারী শিক্ষক', and user info becomes visible"""
        # 1. Super Admin logs in and updates role permission
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        res_update = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_view_users': True
        })
        self.assertEqual(res_update.status_code, 200)
        self.assertTrue(res_update.get_json()['success'])

        # 2. Teacher now accesses user management and API
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'name': 'সহকারী শিক্ষক রহিম',
                'mobile': '01711223344',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        # Now /settings/users should return 200 OK
        res_view = self.client.get('/settings/users')
        self.assertEqual(res_view.status_code, 200)

        # /api/users/list should return 200 OK and users
        res_api = self.client.get('/api/users/list')
        self.assertEqual(res_api.status_code, 200)
        api_data = res_api.get_json()
        self.assertTrue(api_data['success'])
        self.assertGreater(api_data['total'], 0)

        # 3. Super Admin revokes can_view_users
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        res_revoke = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_view_users': False
        })
        self.assertEqual(res_revoke.status_code, 200)

        # 4. Teacher is blocked again
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'name': 'সহকারী শিক্ষক রহিম',
                'mobile': '01711223344',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        res_api2 = self.client.get('/api/users/list')
        self.assertEqual(res_api2.status_code, 403)

    def test_04_admin_hub_access_permission_action(self):
        """User without can_access_admin_hub cannot access /admin, but can if permitted"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'name': 'সহকারী শিক্ষক রহিম',
                'mobile': '01711223344',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        # /admin should redirect to /dashboard
        res_admin = self.client.get('/admin', follow_redirects=False)
        self.assertEqual(res_admin.status_code, 302)
        self.assertIn('/dashboard', res_admin.location)

        # Now grant can_access_admin_hub
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_access_admin_hub': True
        })

        # Teacher accesses /admin now
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 10,
                'name': 'সহকারী শিক্ষক রহিম',
                'mobile': '01711223344',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        res_admin2 = self.client.get('/admin')
        self.assertEqual(res_admin2.status_code, 200)

    def test_05_super_admin_always_has_full_access(self):
        """Super Admin always has full access to user information and admin hub regardless of configs"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        res_admin = self.client.get('/admin')
        self.assertEqual(res_admin.status_code, 200)

        res_users = self.client.get('/settings/users')
        self.assertEqual(res_users.status_code, 200)

        res_api = self.client.get('/api/users/list')
        self.assertEqual(res_api.status_code, 200)


if __name__ == '__main__':
    unittest.main()
