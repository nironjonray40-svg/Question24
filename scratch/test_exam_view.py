import sys
import os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

import app

with app.app.test_client() as client:
    res = client.get('/exam/2/view')
    html = res.data.decode('utf-8')
    
    # Check MCQ Answer table
    print('MCQ Answer Key in HTML:', '‘ক’ বিভাগ: বহুনির্বাচনি প্রশ্নের উত্তরমালা' in html)
    print('Short Answer in HTML:', '‘খ’ বিভাগ: সংক্ষিপ্ত প্রশ্নের আদর্শ উত্তর' in html)
    print('CQ Solutions in HTML:', '‘গ’ বিভাগ: সৃজনশীল প্রশ্নের সমাধান ও মূল্যায়ন নির্দেশনা' in html)
    
    # Check correct bubbles
    print('Correct bubble count:', html.count('is-correct-bubble'))
