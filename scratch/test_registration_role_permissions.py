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

class RegistrationRolePermissionTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            seed_database()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_01_api_roles_available_returns_synchronized_roles(self):
        """Verify /api/roles/available returns active roles and permissions without super admin"""
        res = self.client.get('/api/roles/available')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('roles', data)

        role_names = [r['role_name'] for r in data['roles']]
        self.assertIn('সহকারী শিক্ষক', role_names)
        self.assertIn('সিনিয়র শিক্ষক', role_names)
        self.assertIn('অধ্যক্ষ / প্রধান শিক্ষক', role_names)
        # Super admin should not be in public registration roles
        for n in role_names:
            self.assertNotIn('সুপার', n)

        # Check permission structure
        teacher_role = next(r for r in data['roles'] if r['role_name'] == 'সহকারী শিক্ষক')
        self.assertIn('can_create_exam', teacher_role)
        self.assertIn('can_view_questions', teacher_role)
        self.assertIn('can_view_users', teacher_role)

    def test_02_registration_with_selected_role(self):
        """User registers with a specific institutional role and is saved accordingly"""
        payload = {
            'name': 'মো: জহিরুল ইসলাম',
            'mobile': '01988776655',
            'password': 'password123',
            'role': 'সিনিয়র শিক্ষক'
        }
        res = self.client.post('/api/auth/register', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'সিনিয়র শিক্ষক')

        with app.app_context():
            u = User.query.filter_by(mobile='01988776655').first()
            self.assertIsNotNone(u)
            self.assertEqual(u.name, 'মো: জহিরুল ইসলাম')
            self.assertEqual(u.role, 'সিনিয়র শিক্ষক')

    def test_03_super_admin_updates_role_syncs_immediately(self):
        """Super admin updates a role, and /api/roles/available immediately reflects it"""
        # Super admin logs in
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'সুপার অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        # 1. Update existing role permissions
        res_update = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_edit_question': True
        })
        self.assertEqual(res_update.status_code, 200)

        # 2. Check public available roles API
        res_public = self.client.get('/api/roles/available')
        data = res_public.get_json()
        teacher_role = next(r for r in data['roles'] if r['role_name'] == 'সহকারী শিক্ষক')
        self.assertTrue(teacher_role['can_edit_question'])

        # 3. Super admin creates a brand new role
        res_create = self.client.post('/api/admin/role-permissions/create', json={
            'role_name': 'আইসিটি ও রোবোটিক্স সমন্বয়ক',
            'can_create_exam': True,
            'can_view_questions': True,
            'can_add_question': True,
            'can_access_admin_hub': True
        })
        self.assertEqual(res_create.status_code, 200)

        # 4. Check that the new role is immediately available in registration
        res_public2 = self.client.get('/api/roles/available')
        data2 = res_public2.get_json()
        new_role_names = [r['role_name'] for r in data2['roles']]
        self.assertIn('আইসিটি ও রোবোটিক্স সমন্বয়ক', new_role_names)

        # 5. Register with this newly created role
        payload = {
            'name': 'হাসান মাহমুদ',
            'mobile': '01899001122',
            'password': 'password123',
            'role': 'আইসিটি ও রোবোটিক্স সমন্বয়ক'
        }
        res_reg = self.client.post('/api/auth/register', json=payload)
        self.assertEqual(res_reg.status_code, 200)
        self.assertEqual(res_reg.get_json()['user']['role'], 'আইসিটি ও রোবোটিক্স সমন্বয়ক')

    def test_04_super_admin_self_registration_is_safely_prevented(self):
        """Attempting to self-register as Super Admin falls back safely to 'সহকারী শিক্ষক'"""
        payload = {
            'name': 'হ্যাক চেষ্টারত ইউজার',
            'mobile': '01511223344',
            'password': 'password123',
            'role': 'সুপার অ্যাডমিন'
        }
        res = self.client.post('/api/auth/register', json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        # Must be sanitized to default teacher
        self.assertEqual(data['user']['role'], 'সহকারী শিক্ষক')
        self.assertFalse(data['user']['is_super_admin'])

        with app.app_context():
            u = User.query.filter_by(mobile='01511223344').first()
            self.assertIsNotNone(u)
            self.assertEqual(u.role, 'সহকারী শিক্ষক')
            self.assertFalse(u.is_super_admin_user)

    def test_05_landing_route_contains_registration_roles(self):
        """Verify /landing renders with registration_roles in context and HTML"""
        res = self.client.get('/landing')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('regRoleSelect', html)
        self.assertIn('regRolePermCard', html)
        self.assertIn('ভূমিকা ও পারমিশন স্তর', html)
        self.assertIn('সহকারী শিক্ষক', html)


if __name__ == '__main__':
    unittest.main()
