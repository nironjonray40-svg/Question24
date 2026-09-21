import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# CRITICAL: Use in-memory SQLite database to protect instance/question_bank.db
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from app import app, db, User, ClassLevel, Subject, Chapter, RolePermissionConfig, seed_default_role_permissions


class TestSuperAdminOnlyViews(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.create_all()
            seed_default_role_permissions(force=True)

            # Get or create class and subject for rendering
            c = ClassLevel.query.first()
            if not c:
                c = ClassLevel(name="নবম শ্রেণি", code="9", order_num=1)
                db.session.add(c)
                db.session.flush()

            s = Subject.query.filter_by(class_id=c.id).first()
            if not s:
                s = Subject(name="পদার্থবিজ্ঞান", code="PHY", class_id=c.id)
                db.session.add(s)
                db.session.commit()

            # Create Super Admin User
            self.super_admin = User(
                name="প্রধান অ্যাডমিন",
                mobile="01794918384",
                password="password123",
                role="সুপার অ্যাডমিন",
                is_admin=True,
                status="active"
            )
            # Create Regular Teacher
            self.teacher = User(
                name="সহকারী শিক্ষক মোস্তফা",
                mobile="01811111111",
                password="password123",
                role="সহকারী শিক্ষক",
                is_admin=False,
                status="active"
            )
            # Create Headmaster (High role but not Super Admin)
            self.headmaster = User(
                name="অধ্যক্ষ আব্দুর রহমান",
                mobile="01711111111",
                password="password123",
                role="অধ্যক্ষ / প্রধান শিক্ষক",
                is_admin=False,
                status="active"
            )
            db.session.add_all([self.super_admin, self.teacher, self.headmaster])
            db.session.commit()

            self.super_admin_id = self.super_admin.id
            self.teacher_id = self.teacher.id
            self.headmaster_id = self.headmaster.id

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def login_user(self, user_id, role, mobile):
        with self.client.session_transaction() as sess:
            sess['user'] = {
                'id': user_id,
                'name': 'Test User',
                'mobile': mobile,
                'role': role
            }

    def test_01_super_admin_has_full_access_to_question_bank_and_settings(self):
        self.login_user(self.super_admin_id, 'সুপার অ্যাডমিন', '01794918384')

        # 1. Route access
        resp_q = self.client.get('/questions')
        self.assertEqual(resp_q.status_code, 200)

        resp_s = self.client.get('/settings')
        self.assertEqual(resp_s.status_code, 200)

        # 2. Navigation bar presence
        resp_d = self.client.get('/dashboard')
        self.assertEqual(resp_d.status_code, 200)
        html_d = resp_d.get_data(as_text=True)

        self.assertIn('/questions', html_d)
        self.assertIn('/settings', html_d)
        self.assertIn('প্রশ্ন সম্ভার', html_d)
        self.assertIn('সিলেবাস সেটিংস', html_d)

    def test_02_regular_teacher_cannot_see_or_access_question_bank_and_settings(self):
        self.login_user(self.teacher_id, 'সহকারী শিক্ষক', '01811111111')

        # 1. Route access is denied and redirected
        resp_q = self.client.get('/questions', follow_redirects=True)
        self.assertEqual(resp_q.status_code, 200)
        html_q = resp_q.get_data(as_text=True)
        self.assertIn('প্রোফাইলের জন্য সংরক্ষিত', html_q)
        self.assertIn('প্রশ্ন সম্ভার', html_q)

        resp_s = self.client.get('/settings', follow_redirects=True)
        self.assertEqual(resp_s.status_code, 200)
        html_s = resp_s.get_data(as_text=True)
        self.assertIn('প্রোফাইলের জন্য সংরক্ষিত', html_s)
        self.assertIn('সেটিংস', html_s)

        # 2. Dashboard should NOT show question_list or settings links
        resp_d = self.client.get('/dashboard')
        self.assertEqual(resp_d.status_code, 200)
        html_d = resp_d.get_data(as_text=True)

        self.assertNotIn('href="/questions"', html_d)
        self.assertNotIn('href="/settings"', html_d)
        self.assertNotIn('প্রশ্ন সম্ভার', html_d)
        self.assertNotIn('সিলেবাস সেটিংস', html_d)

        # 3. School profile should NOT show settings link
        resp_sp = self.client.get('/school-profile')
        self.assertEqual(resp_sp.status_code, 200)
        html_sp = resp_sp.get_data(as_text=True)
        self.assertNotIn('href="/settings"', html_sp)
        self.assertNotIn('সিলেবাস সেটিংস', html_sp)

    def test_03_headmaster_cannot_see_or_access_question_bank_and_settings(self):
        self.login_user(self.headmaster_id, 'অধ্যক্ষ / প্রধান শিক্ষক', '01711111111')

        # 1. Dashboard should not contain links to questions or settings
        resp_d = self.client.get('/dashboard')
        self.assertEqual(resp_d.status_code, 200)
        html_d = resp_d.get_data(as_text=True)
        self.assertNotIn('href="/questions"', html_d)
        self.assertNotIn('href="/settings"', html_d)
        self.assertNotIn('প্রশ্ন সম্ভার', html_d)
        self.assertNotIn('সিলেবাস সেটিংস', html_d)

        # 2. Direct route access should be restricted strictly to super admin
        resp_q = self.client.get('/questions', follow_redirects=False)
        self.assertEqual(resp_q.status_code, 302)

        resp_s = self.client.get('/settings', follow_redirects=False)
        self.assertEqual(resp_s.status_code, 302)

    def test_04_anonymous_user_is_redirected(self):
        resp_q = self.client.get('/questions', follow_redirects=False)
        self.assertEqual(resp_q.status_code, 302)

        resp_s = self.client.get('/settings', follow_redirects=False)
        self.assertEqual(resp_s.status_code, 302)


if __name__ == '__main__':
    unittest.main()
