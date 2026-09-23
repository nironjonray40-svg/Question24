# -*- coding: utf-8 -*-
import sys
import io

import os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, Chapter, Topic, User

with app.app_context():
    # 1. Test chapter 659 questions
    qs = Question.query.filter_by(chapter_id=659).order_by(Question.id).all()
    print(f'Total questions in Chapter 659: {len(qs)}')
    assert len(qs) == 8, f'Expected 8, got {len(qs)}'
    for i, q in enumerate(qs, 1):
        print(f'{i}. [{q.question_type}] Ka: {q.cq_sub_ka[:40]}... | Kha: {q.cq_sub_kha[:40]}... | Marks: {q.marks}')
        assert q.question_type == 'descriptive'
        assert q.marks == 10.0
        assert q.cq_sub_ka
        assert q.cq_sub_kha
        assert q.cq_solution

    # 2. Test API client
    client = app.test_client()
    u = User.query.filter_by(mobile='01794918384').first() or User.query.first()
    with client.session_transaction() as sess:
        sess['user'] = u.to_dict()

    res = client.get('/api/questions?chapter_id=659&question_type=descriptive')
    assert res.status_code == 200, f'Status code {res.status_code}'
    data = res.get_json()
    items = data.get('questions', data) if isinstance(data, dict) else data
    print(f'API /api/questions?chapter_id=659&question_type=descriptive returned {len(items)} items')
    assert len(items) == 8

    # 3. Test questions page
    res_page = client.get('/questions')
    assert res_page.status_code == 200
    page_html = res_page.get_data(as_text=True)
    assert 'বর্ণনামূলক' in page_html
    assert 'data-type="descriptive"' in page_html
    print('✓ /questions renders with বর্ণনামূলক successfully')

    # 4. Test exam builder page
    res_builder = client.get('/exam-builder')
    assert res_builder.status_code == 200
    html_b = res_builder.get_data(as_text=True)
    assert 'data-type="descriptive"' in html_b
    assert 'typeCount-descriptive' in html_b
    print('✓ /exam/builder renders with descriptive filter card button and count successfully')

    # 5. Test dashboard page
    res_dash = client.get('/dashboard')
    assert res_dash.status_code == 200
    print('✓ /dashboard renders successfully')

print('\nALL VERIFICATIONS PASSED 100% SUCCESSFULLY!')
