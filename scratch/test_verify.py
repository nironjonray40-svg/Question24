import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
import app

client = app.app.test_client()
res = client.get('/exam-builder?class_id=4&subject_ids=1')
assert res.status_code == 200
html = res.get_data(as_text=True)

assert 'rightPreviousExamsCard' in html
assert 'rightPreviousExamsContainer' in html
assert 'previousExamsSubtext' in html
assert 'loadRightPreviousExamsCard' in html
assert 'renderRightPreviousExamsCard' in html
assert 'setExamFilter' in html
assert 'activeExamBadgeWrapper' in html

pos_type = html.find('id="rightTypeFilterCard"')
pos_prev_exam = html.find('id="rightPreviousExamsCard"')
pos_chap = html.find('id="rightChapterFilterCard"')

assert pos_type != -1 and pos_prev_exam != -1 and pos_chap != -1
assert pos_type < pos_prev_exam < pos_chap, f'Ordering mismatch: pos_type={pos_type}, pos_prev_exam={pos_prev_exam}, pos_chap={pos_chap}'

print('All backend and frontend assertions PASSED flawlessly!')
