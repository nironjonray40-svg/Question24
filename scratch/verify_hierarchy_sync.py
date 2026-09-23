# -*- coding: utf-8 -*-
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ClassLevel, Subject, Chapter, Topic

with app.app_context():
    client = app.test_client()

    print("=== Testing /constructive HTML render ===")
    res = client.get('/constructive')
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    html = res.get_data(as_text=True)
    assert 'ফিল্টার ও টপিক অপশন' in html, "Filter header missing"
    assert 'syncSettingsBtn' in html, "syncSettingsBtn missing"
    assert 'syncHierarchyFromSettings' in html, "syncHierarchyFromSettings JS missing"
    print(">>> /constructive HTML render OK! <<<")

    print("\n=== Testing API Hierarchy Endpoints ===")
    res_classes = client.get('/api/classes')
    assert res_classes.status_code == 200
    classes = res_classes.get_json()
    print(f"Total Classes in DB: {len(classes)}")
    assert len(classes) > 0, "No classes found"

    first_class_id = classes[0]['id']
    res_subjects = client.get(f'/api/subjects/{first_class_id}')
    assert res_subjects.status_code == 200
    subjects = res_subjects.get_json()
    print(f"Subjects for class {classes[0]['name']}: {len(subjects)}")

    if subjects:
        first_sub_id = subjects[0]['id']
        res_chapters = client.get(f'/api/chapters/{first_sub_id}')
        assert res_chapters.status_code == 200
        chapters = res_chapters.get_json()
        print(f"Chapters for subject {subjects[0]['name']}: {len(chapters)}")

        if chapters:
            first_ch_id = chapters[0]['id']
            res_topics = client.get(f'/api/topics/{first_ch_id}')
            assert res_topics.status_code == 200
            topics = res_topics.get_json()
            print(f"Topics for chapter {chapters[0]['title']}: {len(topics)}")

    print("\nALL HIERARCHY API ENDPOINTS FUNCTIONING PERFECTLY!")
