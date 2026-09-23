import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
from app import app

with app.test_client() as client:
    res = client.get('/constructive')
    assert res.status_code == 200, f'Status {res.status_code}'
    html = res.get_data(as_text=True)
    assert 'id="importClass"' in html
    assert 'id="importSubject"' in html
    assert 'id="importChapter"' in html
    assert 'id="importTopic"' in html
    assert 'loadSubjectsForClass' in html
    assert 'loadChaptersForSubject' in html
    assert 'loadTopicsForChapter' in html
    print('SUCCESS: /constructive template rendered with status 200 and all fixed functions!')

    # Test Class 3 (৮ম শ্রেণি)
    res_sub = client.get('/api/subjects/3')
    assert res_sub.status_code == 200
    subs = res_sub.get_json()
    print(f'SUCCESS: /api/subjects/3 returned {len(subs)} subjects.')
    assert len(subs) > 0

    first_sub = subs[0]
    res_chap = client.get(f'/api/chapters/{first_sub["id"]}')
    assert res_chap.status_code == 200
    chaps = res_chap.get_json()
    print(f'SUCCESS: /api/chapters/{first_sub["id"]} ({first_sub["name"]}) returned {len(chaps)} chapters.')

    if len(chaps) > 0:
        first_chap = chaps[0]
        res_top = client.get(f'/api/topics/{first_chap["id"]}')
        assert res_top.status_code == 200
        topics = res_top.get_json()
        print(f'SUCCESS: /api/topics/{first_chap["id"]} returned {len(topics)} topics.')
