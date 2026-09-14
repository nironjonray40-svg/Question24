import sys
import os
import urllib.request
import re

sys.stdout.reconfigure(encoding='utf-8')

try:
    with urllib.request.urlopen('http://127.0.0.1:5000/exam/2/view') as response:
        html = response.read().decode('utf-8')
        status = response.status
except Exception as e:
    print('Failed to request URL:', e)
    sys.exit(1)

print('HTTP Status:', status)

checks = [
    ('id="toggleSourceBtn"', 'Toggle Source Button'),
    ('id="toggleAnswerBtn"', 'Toggle Answer Button'),
    ('id="sourceBadge"', 'Source Status Badge'),
    ('id="answerBadge"', 'Answer Status Badge'),
    ('id="answerSheetSection"', 'Answer Sheet Section'),
    ('hide-school-tags', 'Hide School Tags CSS Class'),
    ('show-answers', 'Show Answers CSS Class'),
    ('function toggleSourceTags()', 'Toggle Source Tags JS Function'),
    ('function toggleAnswerSheet()', 'Toggle Answer Sheet JS Function'),
    ('function wrapAllSourceTags()', 'Wrap All Source Tags JS Function'),
    ('question-stem', 'MCQ Question Stem Class'),
    ('short-question-text', 'Short Question Class'),
    ('cq-stem-text', 'CQ Stem Class'),
    ('cq-sub-text', 'CQ Sub-question Class')
]

all_passed = True
for term, name in checks:
    if term in html:
        print(f'[PASS] {name}')
    else:
        print(f'[FAIL] {name}')
        all_passed = False

if all_passed:
    print('\n>>> ALL VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<')
else:
    print('\n>>> SOME CHECKS FAILED! <<<')
    sys.exit(1)
