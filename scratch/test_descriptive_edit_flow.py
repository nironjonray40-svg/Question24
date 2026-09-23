# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question

def test_descriptive_edit_flow():
    client = app.test_client()
    
    with app.app_context():
        # 1. Test GET /questions/1977/edit
        res_get = client.get('/questions/1977/edit')
        assert res_get.status_code == 200, f"GET failed with {res_get.status_code}"
        html = res_get.data.decode('utf-8')
        
        # Verify that descriptive_sub_ka and descriptive_sub_kha appear in the rendered HTML
        assert 'name="descriptive_sub_ka"' in html, "descriptive_sub_ka missing from HTML!"
        assert 'name="descriptive_sub_kha"' in html, "descriptive_sub_kha missing from HTML!"
        assert 'দেখলুম সে চুপ থাকাটাই পছন্দ করছে।' in html, "Question 1977 text missing from HTML!"
        print("✓ Step 1: GET /questions/1977/edit rendered successfully with correct field names.")

        # 2. Test POST /questions/1977/edit with form data submitted by browser
        post_data = {
            'class_id': '6',
            'subject_id': '20',
            'chapter_id': '659',
            'topic_id': '',
            'question_type': 'descriptive',
            'difficulty': 'medium',
            'marks': '10.0',
            'descriptive_sub_ka': "'দেখলুম সে চুপ থাকাটাই পছন্দ করছে।'- কথাটি বুঝিয়ে লেখো। (সম্পাদিত)",
            'descriptive_sub_kha': "'মানবতাই বিশ্বমানবের একমাত্র যোগসূত্র।'- 'কাবুলের শেষ প্রহরে' রচনার আলোকে মন্তব্যটি মূল্যায়ন করো। [ক্রিয়েটিভ মডেল স্কুল]",
            'descriptive_ans_ka': 'ক এর নতুন উত্তর',
            'descriptive_ans_kha': 'খ এর নতুন উত্তর',
        }
        res_post = client.post('/questions/1977/edit', data=post_data, follow_redirects=True)
        assert res_post.status_code == 200, f"POST failed with {res_post.status_code}"
        
        # 3. Verify in database
        q_updated = Question.query.get(1977)
        assert q_updated is not None
        assert '(সম্পাদিত)' in q_updated.cq_sub_ka, f"Failed: cq_sub_ka got wiped or not updated: '{q_updated.cq_sub_ka}'"
        assert '[ক্রিয়েটিভ মডেল স্কুল]' in q_updated.cq_sub_kha, f"Failed: cq_sub_kha got wiped or not updated: '{q_updated.cq_sub_kha}'"
        assert 'ক) ক এর নতুন উত্তর' in q_updated.cq_solution, f"Failed: solution not updated: '{q_updated.cq_solution}'"
        print("✓ Step 2: POST /questions/1977/edit updated question without losing any text!")

        # 4. Revert back to original without '(সম্পাদিত)'
        post_data['descriptive_sub_ka'] = "'দেখলুম সে চুপ থাকাটাই পছন্দ করছে।'- কথাটি বুঝিয়ে লেখো।"
        client.post('/questions/1977/edit', data=post_data, follow_redirects=True)
        
        q_clean = Question.query.get(1977)
        assert q_clean.cq_sub_ka == "'দেখলুম সে চুপ থাকাটাই পছন্দ করছে।'- কথাটি বুঝিয়ে লেখো।"
        print("✓ Step 3: Verified clean update and data integrity.")

        # 5. Check all 8 questions in Chapter 659
        qs = Question.query.filter_by(chapter_id=659).order_by(Question.id).all()
        assert len(qs) == 8, f"Expected 8 questions, found {len(qs)}"
        for q in qs:
            assert q.question_type == 'descriptive'
            assert q.cq_sub_ka and len(q.cq_sub_ka) > 5, f"Q{q.id} has invalid ka: '{q.cq_sub_ka}'"
            assert q.cq_sub_kha and len(q.cq_sub_kha) > 5, f"Q{q.id} has invalid kha: '{q.cq_sub_kha}'"
        print(f"✓ Step 4: All {len(qs)} descriptive questions in Chapter 659 are valid, non-empty, and verified!")

if __name__ == '__main__':
    test_descriptive_edit_flow()
