import os
import sys
import unittest
import json

# Set in-memory db before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, seed_database, get_permissions_for_role
import models
from models import User, RolePermissionConfig

class RoleCrudTests(unittest.TestCase):
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

    def test_01_security_blocks_non_super_admin(self):
        """Non-super admin and guest requests MUST be blocked with 403 Forbidden"""
        # Guest attempts to create a role
        res1 = self.client.post('/api/admin/role-permissions/create', json={
            'role_name': 'টেস্ট ভূমিকা'
        })
        self.assertEqual(res1.status_code, 403)
        self.assertFalse(res1.get_json()['success'])

        # Guest attempts to delete a role
        res2 = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': 'সিনিয়র শিক্ষক'
        })
        self.assertEqual(res2.status_code, 403)
        self.assertFalse(res2.get_json()['success'])

        # Regular teacher attempts to create and delete
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 50,
                'name': 'কামাল উদ্দিন',
                'mobile': '01900000000',
                'role': 'সহকারী শিক্ষক',
                'is_admin': False,
                'is_super_admin': False
            }

        res3 = self.client.post('/api/admin/role-permissions/create', json={
            'role_name': 'নতুন সহকারী'
        })
        self.assertEqual(res3.status_code, 403)

        res4 = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': 'সিনিয়র শিক্ষক'
        })
        self.assertEqual(res4.status_code, 403)

    def test_02_super_admin_creates_new_role(self):
        """Super Admin can successfully create a new role with granular permissions"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        new_role_name = "সহকারী লাইব্রেরিয়ান"
        create_res = self.client.post('/api/admin/role-permissions/create', json={
            'role_name': new_role_name,
            'can_create_exam': False,
            'can_view_questions': True,
            'can_add_question': False,
            'can_edit_question': False,
            'can_view_saved_exams': True,
            'can_manage_curriculum': False,
            'can_manage_school_profile': False,
            'can_view_users': False,
            'can_manage_users': False,
            'can_access_admin_hub': False,
            'can_download_backup': False
        })
        self.assertEqual(create_res.status_code, 200)
        data = create_res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['role_permission']['role_name'], new_role_name)
        self.assertFalse(data['role_permission']['can_create_exam'])
        self.assertTrue(data['role_permission']['can_view_questions'])
        self.assertTrue(data['role_permission']['can_view_saved_exams'])

        # Duplicate role creation must return 409
        dup_res = self.client.post('/api/admin/role-permissions/create', json={
            'role_name': new_role_name
        })
        self.assertEqual(dup_res.status_code, 409)

        # Verify DB and helper
        with app.app_context():
            perm = get_permissions_for_role(new_role_name)
            self.assertFalse(perm['can_create_exam'])
            self.assertTrue(perm['can_view_questions'])
            self.assertTrue(perm['can_view_saved_exams'])

    def test_03_protected_roles_cannot_be_deleted(self):
        """Root roles ('সুপার অ্যাডমিন', 'সহকারী শিক্ষক') MUST be protected from deletion"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        # Attempt to delete Super Admin
        res_super = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': 'সুপার অ্যাডমিন'
        })
        self.assertEqual(res_super.status_code, 400)
        self.assertIn('নিষিদ্ধ', res_super.get_json()['message'])

        # Attempt to delete fallback Assistant Teacher
        res_teacher = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': 'সহকারী শিক্ষক'
        })
        self.assertEqual(res_teacher.status_code, 400)
        self.assertIn('সহকারী শিক্ষক', res_teacher.get_json()['message'])

    def test_04_role_deletion_and_user_migration(self):
        """When a role is deleted, all existing users in that role must be safely migrated to 'সহকারী শিক্ষক'"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        # 1. Create a custom role
        custom_role = "ল্যাব সহকারী (Lab Assistant)"
        self.client.post('/api/admin/role-permissions/create', json={
            'role_name': custom_role,
            'can_create_exam': True,
            'can_view_questions': True
        })

        # 2. Create users with this role
        with app.app_context():
            u1 = User(name="ল্যাব শিক্ষক ১", mobile="01711223344", role=custom_role, status="active")
            u1.set_password("pass123")
            u2 = User(name="ল্যাব শিক্ষক ২", mobile="01711223355", role=custom_role, status="active")
            u2.set_password("pass123")
            db.session.add_all([u1, u2])
            db.session.commit()

            self.assertEqual(User.query.filter_by(role=custom_role).count(), 2)

        # 3. Super Admin deletes the custom role
        del_res = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': custom_role
        })
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.get_json()
        self.assertTrue(del_data['success'])
        self.assertEqual(del_data['migrated_users_count'], 2)

        # 4. Verify in DB: Role is gone and users are migrated to 'সহকারী শিক্ষক'
        with app.app_context():
            cfg = RolePermissionConfig.query.filter_by(role_name=custom_role).first()
            self.assertIsNone(cfg)

            migrated_u1 = User.query.filter_by(mobile="01711223344").first()
            migrated_u2 = User.query.filter_by(mobile="01711223355").first()
            self.assertEqual(migrated_u1.role, "সহকারী শিক্ষক")
            self.assertEqual(migrated_u2.role, "সহকারী শিক্ষক")

    def test_05_admin_panel_template_has_add_and_delete_buttons(self):
        """Admin panel template renders add new role modal and action buttons without error"""
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
        self.assertIn('adminAddRoleModal', html)
        self.assertIn('+ নতুন ভূমিকা যুক্ত করুন', html)
        self.assertIn('adminDeleteRole', html)

if __name__ == '__main__':
    unittest.main()
