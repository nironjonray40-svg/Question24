import os
import sys
import unittest
import json
from flask import session

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, seed_database, get_permissions_for_role, get_current_user_permissions, DEFAULT_ROLE_PERMISSIONS
from models import User, RolePermissionConfig

class DynamicRolePermissionTests(unittest.TestCase):
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

    def test_01_seed_and_defaults(self):
        """Verify that role permissions are seeded properly on initialization"""
        with app.app_context():
            configs = RolePermissionConfig.query.all()
            self.assertGreater(len(configs), 5)
            
            # Check Teacher default: can create exams, cannot access admin hub
            teacher_perm = get_permissions_for_role("সহকারী শিক্ষক")
            self.assertTrue(teacher_perm['can_create_exam'])
            self.assertTrue(teacher_perm['can_view_questions'])
            self.assertFalse(teacher_perm['can_edit_question'])
            self.assertFalse(teacher_perm['can_access_admin_hub'])
            self.assertFalse(teacher_perm['can_download_backup'])

            # Check Super Admin default: all true
            super_perm = get_permissions_for_role("সুপার অ্যাডমিন")
            self.assertTrue(super_perm['can_create_exam'])
            self.assertTrue(super_perm['can_access_admin_hub'])
            self.assertTrue(super_perm['can_download_backup'])

    def test_02_security_gatekeeper_blocks_non_super_admin(self):
        """Non-super admin and guest requests MUST receive 403 Forbidden"""
        # Guest access
        res = self.client.get('/api/admin/role-permissions')
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertFalse(data['success'])
        self.assertIn('অননুমোদিত এক্সেস', data['message'])

        res_update = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_access_admin_hub': True
        })
        self.assertEqual(res_update.status_code, 403)

        res_reset = self.client.post('/api/admin/role-permissions/reset-defaults', json={})
        self.assertEqual(res_reset.status_code, 403)

        # Logged in as regular teacher
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 99,
                'name': 'আব্দুল করিম',
                'mobile': '01811111111',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        res2 = self.client.get('/api/admin/role-permissions')
        self.assertEqual(res2.status_code, 403)

        res2_update = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_access_admin_hub': True
        })
        self.assertEqual(res2_update.status_code, 403)

    def test_03_super_admin_dynamic_permission_update(self):
        """Super Admin can dynamically update any role's permission matrix at any time"""
        # Login as Super Admin
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        # 1. Fetch current permissions
        res = self.client.get('/api/admin/role-permissions')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['role_permissions'], list)
        
        # 2. Modify "সহকারী শিক্ষক" permissions: Grant can_access_admin_hub and can_edit_question
        update_res = self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_access_admin_hub': True,
            'can_edit_question': True
        })
        self.assertEqual(update_res.status_code, 200)
        update_data = update_res.get_json()
        self.assertTrue(update_data['success'])
        self.assertTrue(update_data['role_permission']['can_access_admin_hub'])
        self.assertTrue(update_data['role_permission']['can_edit_question'])

        # 3. Verify in database & helper
        with app.app_context():
            updated_perm = get_permissions_for_role('সহকারী শিক্ষক')
            self.assertTrue(updated_perm['can_access_admin_hub'])
            self.assertTrue(updated_perm['can_edit_question'])

        # 4. Verify context processor for a logged in teacher
        with app.test_request_context('/dashboard'):
            session['user'] = {
                'id': 105,
                'name': 'রফিকুল ইসলাম',
                'mobile': '01755555555',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }
            perms = get_current_user_permissions()
            self.assertTrue(perms['can_access_admin_hub'])
            self.assertTrue(perms['can_edit_question'])

    def test_04_reset_to_factory_defaults(self):
        """Super Admin can reset modified permissions back to factory defaults"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        # Modify "সহকারী শিক্ষক"
        self.client.post('/api/admin/role-permissions/update', json={
            'role_name': 'সহকারী শিক্ষক',
            'can_download_backup': True
        })

        with app.app_context():
            self.assertTrue(get_permissions_for_role('সহকারী শিক্ষক')['can_download_backup'])

        # Reset single role
        reset_res = self.client.post('/api/admin/role-permissions/reset-defaults', json={
            'role_name': 'সহকারী শিক্ষক'
        })
        self.assertEqual(reset_res.status_code, 200)

        with app.app_context():
            self.assertFalse(get_permissions_for_role('সহকারী শিক্ষক')['can_download_backup'])

    def test_05_admin_panel_template_rendering(self):
        """Verify admin panel renders Role Permission Matrix without template errors"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)
        self.assertIn('ভূমিকা অনুযায়ী স্বয়ংক্রিয় পারমিশন স্তর কনফিগারেশন', html)
        self.assertIn('adminRolePermissionModal', html)
        self.assertIn('সহকারী শিক্ষক', html)

if __name__ == '__main__':
    unittest.main()
