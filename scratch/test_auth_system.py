import os
import sys
import unittest
import json

# Ensure app path
sys.path.insert(0, os.path.abspath('.'))

from app import app, db, User, seed_database, normalize_mobile_number

class TestAuthAndUserManagement(unittest.TestCase):
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

    def test_mobile_normalization(self):
        self.assertEqual(normalize_mobile_number("০১৭১২৩৪৫৬৭৮"), "01712345678")
        self.assertEqual(normalize_mobile_number("+8801712345678"), "01712345678")
        self.assertEqual(normalize_mobile_number("8801812345678"), "01812345678")
        self.assertEqual(normalize_mobile_number(" 01912-345678 "), "01912345678")

    def test_user_model_password_hashing(self):
        with app.app_context():
            u = User(name="মো: টেস্ট শিক্ষক", mobile="01711112233", role="শিক্ষক")
            u.set_password("secret123")
            db.session.add(u)
            db.session.commit()

            saved = User.query.filter_by(mobile="01711112233").first()
            self.assertIsNotNone(saved)
            self.assertTrue(saved.check_password("secret123"))
            self.assertFalse(saved.check_password("wrongpass"))
            self.assertEqual(saved.raw_password_display, "secret123")

    def test_registration_api(self):
        payload = {
            "name": "আব্দুর রহিম",
            "mobile": "01755667788",
            "password": "mypassword123",
            "role": "সহকারী শিক্ষক"
        }
        res = self.client.post('/api/auth/register', json=payload)
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['name'], "আব্দুর রহিম")
        self.assertEqual(data['user']['mobile'], "01755667788")

        # Test duplicate mobile prevention
        res_dup = self.client.post('/api/auth/register', json=payload)
        data_dup = json.loads(res_dup.data)
        self.assertEqual(res_dup.status_code, 409)
        self.assertFalse(data_dup['success'])

    def test_login_api(self):
        # Register user first
        self.client.post('/api/auth/register', json={
            "name": "করিম সাহেব",
            "mobile": "01899887766",
            "password": "pass789"
        })

        # Correct login
        res = self.client.post('/api/auth/login', json={
            "mobile": "01899887766",
            "password": "pass789"
        })
        data = json.loads(res.data)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['name'], "করিম সাহেব")

        # Bangla numeral input login test
        res_bn = self.client.post('/api/auth/login', json={
            "mobile": "০১৮৯৯৮৮৭৭৬৬",
            "password": "pass789"
        })
        data_bn = json.loads(res_bn.data)
        self.assertEqual(res_bn.status_code, 200)
        self.assertTrue(data_bn['success'])

        # Wrong password test
        res_wrong = self.client.post('/api/auth/login', json={
            "mobile": "01899887766",
            "password": "wrong"
        })
        data_wrong = json.loads(res_wrong.data)
        self.assertEqual(res_wrong.status_code, 401)
        self.assertFalse(data_wrong['success'])

    def test_settings_user_management_crud(self):
        # List users
        res_list = self.client.get('/api/users/list')
        data_list = json.loads(res_list.data)
        self.assertTrue(data_list['success'])
        initial_count = data_list['total']

        # Add user from settings panel
        res_add = self.client.post('/api/users/add', json={
            "name": "হাসান মাহমুদ",
            "mobile": "01600112233",
            "password": "hasanpass",
            "role": "সিনিয়র শিক্ষক",
            "status": "active"
        })
        data_add = json.loads(res_add.data)
        self.assertTrue(data_add['success'])
        new_id = data_add['user']['id']

        # Edit user
        res_edit = self.client.post(f'/api/users/edit/{new_id}', json={
            "name": "হাসান মাহমুদ (সংশোধিত)",
            "role": "প্রধান শিক্ষক"
        })
        data_edit = json.loads(res_edit.data)
        self.assertTrue(data_edit['success'])
        self.assertEqual(data_edit['user']['name'], "হাসান মাহমুদ (সংশোধিত)")

        # Delete user
        res_del = self.client.post(f'/api/users/delete/{new_id}')
        data_del = json.loads(res_del.data)
        self.assertTrue(data_del['success'])

    def test_user_management_page_render(self):
        res = self.client.get('/settings/users')
        self.assertEqual(res.status_code, 200)
        self.assertIn('নিবন্ধিত ইউজার তালিকা'.encode('utf-8'), res.data)

if __name__ == '__main__':
    unittest.main()
