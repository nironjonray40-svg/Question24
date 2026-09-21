import os
import sys
import unittest
import json

# Set in-memory db before importing app
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db, seed_database, seed_default_role_permissions, get_permissions_for_role
from models import User, RolePermissionConfig

class PermanentRoleDeletionTests(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = app.test_client()
        with app.app_context():
            db.create_all()
            seed_default_role_permissions(force=True)

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_01_super_admin_deletes_role_permanently(self):
        """Deleting a role removes it completely from database and migrates users"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        target_role = "খণ্ডকালীন / অতিথি শিক্ষক"

        # Verify role exists prior to delete
        with app.app_context():
            cfg_before = RolePermissionConfig.query.filter_by(role_name=target_role).first()
            self.assertIsNotNone(cfg_before)

            # Assign a user to this role
            test_user = User(name="পরীক্ষামূলক শিক্ষক", mobile="01811223344", role=target_role, status="active")
            test_user.set_password("pass123")
            db.session.add(test_user)
            db.session.commit()

        # Delete role via Super Admin API
        del_res = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': target_role
        })
        self.assertEqual(del_res.status_code, 200)
        del_data = del_res.get_json()
        self.assertTrue(del_data['success'])
        self.assertIn('স্থায়ীভাবে মুছে ফেলা হয়েছে', del_data['message'])
        self.assertEqual(del_data['migrated_users_count'], 1)

        # Verify role is gone from DB
        with app.app_context():
            cfg_after = RolePermissionConfig.query.filter_by(role_name=target_role).first()
            self.assertIsNone(cfg_after)

            migrated_user = User.query.filter_by(mobile="01811223344").first()
            self.assertEqual(migrated_user.role, "সহকারী শিক্ষক")

        # Verify seed_default_role_permissions() does NOT resurrect it
        with app.app_context():
            seed_default_role_permissions(force=False)
            cfg_resurrect_check = RolePermissionConfig.query.filter_by(role_name=target_role).first()
            self.assertIsNone(cfg_resurrect_check, "Deleted role should NOT be resurrected by seed_default_role_permissions!")

    def test_02_admin_panel_template_reflects_permanent_deletion(self):
        """Admin panel template does not render deleted role in table or role selection modal"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        target_role = "বিভাগীয় প্রধান (Head of Dept)"

        # Delete the role
        del_res = self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': target_role
        })
        self.assertEqual(del_res.status_code, 200)

        # Fetch admin panel page
        res = self.client.get('/admin')
        self.assertEqual(res.status_code, 200)
        html = res.get_data(as_text=True)

        # Role table body must not contain the role
        self.assertNotIn(f'<span>{target_role}</span>', html)

        # adminRoleSelect options must not contain the role
        self.assertNotIn(f'<option value="{target_role}">{target_role}</option>', html)

    def test_03_get_permissions_for_deleted_role(self):
        """Permissions for a deleted role fall back to active 'সহকারী শিক্ষক' permissions"""
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': 1,
                'name': 'প্রধান অ্যাডমিন',
                'mobile': '01794918384',
                'role': 'সুপার অ্যাডমিন',
                'is_admin': True,
                'is_super_admin': True
            }

        target_role = "সিনিয়র শিক্ষক"
        self.client.post('/api/admin/role-permissions/delete', json={
            'role_name': target_role
        })

        with app.app_context():
            perms = get_permissions_for_role(target_role)
            default_asst_perms = get_permissions_for_role("সহকারী শিক্ষক")
            self.assertEqual(perms['can_create_exam'], default_asst_perms['can_create_exam'])
            self.assertEqual(perms['can_edit_question'], default_asst_perms['can_edit_question'])

if __name__ == '__main__':
    unittest.main()
