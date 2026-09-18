import os, sys, re
from collections import defaultdict
sys.path.insert(0, os.path.abspath('.'))
from app import app, db
from models import Question

def normalize(text):
    if not text: return ''
    cleaned = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', text, flags=re.I)
    cleaned = re.sub(r'\(\s*[^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি)[^\)]*\)', '', cleaned, flags=re.I)
    cleaned = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-]+', ' ', cleaned).strip().lower()
    return cleaned

import time
import time
with app.app_context():
    t0 = time.time()
    all_questions = Question.query.with_entities(
        Question.id, Question.question_type, Question.mcq_stem, 
        Question.short_question, Question.cq_stem, Question.cq_sub_ka, Question.cq_sub_kha
    ).all()
    key_map = defaultdict(list)
    for q_id, q_type, mcq_stem, short_q, cq_stem, cq_ka, cq_kha in all_questions:
        if q_type == 'mcq':
            cleaned = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', mcq_stem or '', flags=re.I)
            cleaned = re.sub(r'\(\s*[^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি)[^\)]*\)', '', cleaned, flags=re.I)
            norm = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', cleaned).strip().lower()
            key = ('mcq', norm)
        elif q_type == 'short':
            cleaned = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', short_q or '', flags=re.I)
            cleaned = re.sub(r'\(\s*[^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি)[^\)]*\)', '', cleaned, flags=re.I)
            norm = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', cleaned).strip().lower()
            key = ('short', norm)
        elif q_type == 'cq':
            c_stem = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_stem or '', flags=re.I)
            c_stem = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_stem).strip().lower()
            c_ka = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_ka or '', flags=re.I)
            c_ka = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_ka).strip().lower()
            c_kha = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_kha or '', flags=re.I)
            c_kha = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_kha).strip().lower()
            key = ('cq', c_stem, c_ka, c_kha)
        else:
            key = (q_type, '')
        
        if key[1]:
            key_map[key].append(q_id)
            
    dup_ids = set()
    for k, ids in key_map.items():
        if len(ids) > 1:
            dup_ids.update(ids)
    t1 = time.time()
    print(f"Entities query: Total {len(dup_ids)} duplicates in {(t1-t0)*1000:.2f} ms")
