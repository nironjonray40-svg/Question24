# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, Chapter, Topic, User

with app.app_context():
    client = app.test_client()
    u = User.query.filter_by(mobile='01794918384').first() or User.query.first()
    with client.session_transaction() as sess:
        sess['user'] = u.to_dict()

    print("=== 1. Testing /api/chapter/659/next-serial ===")
    res_serial = client.get('/api/chapter/659/next-serial?type=descriptive')
    assert res_serial.status_code == 200, f"Status: {res_serial.status_code}"
    serial_data = res_serial.get_json()
    print("Serial API response:", serial_data)
    assert serial_data['success'] is True
    assert serial_data['chapter_id'] == 659
    assert serial_data['type_count'] == 8
    assert serial_data['next_serial'] == 9
    assert serial_data['next_serial_bn'] == '৯'
    assert serial_data['next_serial_label'] == '৯ নং প্রশ্ন'
    print("✓ /api/chapter/<id>/next-serial passed!")

    print("\n=== 2. Testing /questions/add Form Render ===")
    res_add_page = client.get('/questions/add')
    assert res_add_page.status_code == 200
    html = res_add_page.get_data(as_text=True)
    assert 'id="descriptiveSection"' in html
    assert 'id="descriptiveSerialBadge"' in html
    assert 'id="descriptiveSubKaBox"' in html
    assert 'id="descriptiveSubKhaBox"' in html
    assert 'id="descriptiveAnsKa"' in html
    assert 'id="descriptiveAnsKha"' in html
    assert 'id="descriptiveSubGaBox"' in html
    assert 'id="descriptiveSubGhaBox"' in html
    assert 'id="btnAddDescriptiveSub"' in html
    assert '৩ মার্ক' in html
    assert '৭ মার্ক' in html
    print("✓ /questions/add renders all descriptive form fields perfectly!")

    print("\n=== 3. Testing POST /questions/add with descriptive question and answers ===")
    post_data = {
        'class_id': 3,
        'subject_id': 47,
        'chapter_id': 659, # Kabuler Shesh Prohor
        'question_type': 'descriptive',
        'marks': '10.0',
        'difficulty': 'medium',
        'cq_stem': 'টেস্ট বর্ণনামূলক উদ্দীপক',
        'cq_sub_ka': 'টেস্ট প্রশ্ন ক',
        'descriptive_ans_ka': 'টেস্ট উত্তর ক এর বিশদ সমাধান',
        'cq_sub_kha': 'টেস্ট প্রশ্ন খ',
        'descriptive_ans_kha': 'টেস্ট উত্তর খ এর বিশদ সমাধান'
    }
    res_post = client.post('/questions/add', data=post_data, follow_redirects=True)
    assert res_post.status_code == 200

    # Verify in DB
    created_q = Question.query.filter_by(chapter_id=659, cq_sub_ka='টেস্ট প্রশ্ন ক').first()
    assert created_q is not None, "Question was not saved!"
    print(f"Created Question ID: {created_q.id}")
    assert created_q.question_type == 'descriptive'
    assert created_q.cq_sub_ka == 'টেস্ট প্রশ্ন ক'
    assert created_q.cq_sub_kha == 'টেস্ট প্রশ্ন খ'
    assert created_q.marks == 10.0
    print("cq_solution:\n", created_q.cq_solution)
    assert 'ক) টেস্ট উত্তর ক এর বিশদ সমাধান' in created_q.cq_solution
    assert 'খ) টেস্ট উত্তর খ এর বিশদ সমাধান' in created_q.cq_solution

    # Delete test question
    db.session.delete(created_q)
    db.session.commit()
    print("✓ POST /questions/add passed and test question cleaned up!")

    print("\n=== 4. Testing Fast Save with (গ) sub-question and answer ===")
    fast_post_data = {
        'class_id': 3,
        'subject_id': 47,
        'chapter_id': 659,
        'question_type': 'descriptive',
        'marks': '15.0',
        'difficulty': 'medium',
        'cq_sub_ka': 'টেস্ট প্রশ্ন ক ফাস্ট',
        'descriptive_ans_ka': 'উত্তর ক ফাস্ট',
        'cq_sub_kha': 'টেস্ট প্রশ্ন খ ফাস্ট',
        'descriptive_ans_kha': 'উত্তর খ ফাস্ট',
        'cq_sub_ga': 'টেস্ট প্রশ্ন গ ফাস্ট',
        'descriptive_ans_ga': 'উত্তর গ ফাস্ট'
    }
    res_fast = client.post('/api/v1/fast-save', data=fast_post_data)
    assert res_fast.status_code == 200
    fast_json = res_fast.get_json()
    assert fast_json['success'] is True
    
    fast_q = Question.query.filter_by(chapter_id=659, cq_sub_ka='টেস্ট প্রশ্ন ক ফাস্ট').first()
    assert fast_q is not None
    assert fast_q.cq_sub_ga == 'টেস্ট প্রশ্ন গ ফাস্ট'
    print("Fast save cq_solution:\n", fast_q.cq_solution)
    assert 'ক) উত্তর ক ফাস্ট' in fast_q.cq_solution
    assert 'খ) উত্তর খ ফাস্ট' in fast_q.cq_solution
    assert 'গ) উত্তর গ ফাস্ট' in fast_q.cq_solution

    db.session.delete(fast_q)
    db.session.commit()
    print("✓ Fast Save with (গ) sub-question passed and test question cleaned up!")

    # Verify chapter 659 question count is exactly 8
    final_count = Question.query.filter_by(chapter_id=659).count()
    print(f"\nFinal question count in Chapter 659: {final_count}")
    assert final_count == 8, f"Expected 8, got {final_count}"

print("\nALL DESCRIPTIVE FORM TESTS PASSED 100% SUCCESSFULLY!")
