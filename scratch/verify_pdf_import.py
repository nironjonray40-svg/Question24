# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import Flask app and models
from app import app, db
from models import ClassLevel, Subject, Chapter, Question

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdf_path = os.path.join(os.path.dirname(__file__), 'sample_test_questions.pdf')

# Check if a Bengali font exists in Windows Fonts
font_name = 'Helvetica'
bangla_font_path = r'C:\Windows\Fonts\kalpurush.ttf'
if not os.path.exists(bangla_font_path):
    bangla_font_path = r'C:\Windows\Fonts\SolaimanLipi.ttf'
if not os.path.exists(bangla_font_path):
    bangla_font_path = r'C:\Windows\Fonts\vrinda.ttf'
if not os.path.exists(bangla_font_path):
    bangla_font_path = r'C:\Windows\Fonts\Nirmala.ttf'

if os.path.exists(bangla_font_path):
    try:
        pdfmetrics.registerFont(TTFont('BanglaFont', bangla_font_path))
        font_name = 'BanglaFont'
        print(f"Registered Windows Bengali font from: {bangla_font_path}")
    except Exception as e:
        print(f"Could not register font {bangla_font_path}: {e}")

c = canvas.Canvas(pdf_path, pagesize=letter)
c.setFont(font_name, 12)

lines = [
    "[সৃজনশীল ১]",
    "১। নিচের অনুচ্ছেদটি পড়ে সংশ্লিষ্ট প্রশ্নগুলোর উত্তর দাও:",
    "দশম শ্রেণির ছাত্রী মিতু চোখে দেখে না। কিন্তু তার স্মৃতিশক্তি প্রখর।",
    "(ক) সুভার পিতার নাম কী? [১]",
    "(খ) ‘সুভার একটি বিশেষ সুবিধা ছিল’—কথাটি দ্বারা কী বোঝানো হয়েছে? [২]",
    "(গ) উদ্দীপকের মিতুর পারিবারিক পরিবেশ সুভা গল্পের কোন দিকটি উন্মোচন করে? [৩]",
    "(ঘ) মিতু অনুকূল পরিবেশ পেলেও সুভা তা থেকে বঞ্চিত ছিল—মন্তব্যটি বিশ্লেষণ কর। [৪]",
    "উত্তর: ক) বাণীকণ্ঠ। খ) বাকপ্রতিবন্ধী হওয়ায় সাধারণ মানুষের চেয়ে প্রকৃতির সাথে নিবিড় সখ্য।",
    "",
    "২. নিচের কোন রচনাটি আলাদা শ্রেণির?",
    "(ক) বই পড়া (খ) মমতাদি (গ) নিমগাছ (ঘ) সুভা",
    "সঠিক উত্তর: ক",
    "ব্যাখ্যা: বই পড়া একটি প্রবন্ধ।",
    "",
    "৩. বাংলা ভাষার জন্ম কোন প্রাকৃত থেকে?",
    "ক) মাগধী",
    "খ) শৌরসেনী",
    "গ) মহারাষ্ট্রী",
    "ঘ) পৈশাচী",
    "উত্তর: ক",
    "",
    "৪. সুভার মা কেন সুভাকে নিজের গর্ভের কলঙ্ক মনে করতেন?",
    "উত্তর: সুভা বাকপ্রতিবন্ধী হওয়ায় মা তাকে নিজের দুর্ভাগ্যের প্রতীক মনে করতেন।"
]

y = 750
for line in lines:
    c.drawString(50, y, line)
    y -= 22

c.save()
print(f"Generated test PDF: {pdf_path} (size: {os.path.getsize(pdf_path)} bytes)")

# Run Flask test client verification
with app.app_context():
    client = app.test_client()

    print("\n=== 1. TESTING /api/parse-pdf ===")
    with open(pdf_path, 'rb') as f:
        data = {
            'file': (io.BytesIO(f.read()), 'sample_test_questions.pdf', 'application/pdf')
        }
        res = client.post('/api/parse-pdf', data=data, content_type='multipart/form-data')

    print(f"Status Code: {res.status_code}")
    res_json = res.get_json()
    print("Success:", res_json.get('success'))
    print("Count:", res_json.get('count'))
    print("Message:", res_json.get('message'))
    print("Raw text length:", len(res_json.get('raw_text', '')))

    questions = res_json.get('questions', [])
    for idx, q in enumerate(questions):
        print(f"  Q{idx+1} Type: {q.get('question_type')} | Marks: {q.get('marks')}")
        if q.get('question_type') == 'cq':
            print(f"    Ka: {q.get('cq_sub_ka')} | Kha: {q.get('cq_sub_kha')}")
        elif q.get('question_type') == 'mcq':
            print(f"    Stem: {q.get('mcq_stem')[:40]} | Ans: {q.get('correct_option')} | Opt A: {q.get('option_a')}")
        else:
            print(f"    Short Q: {q.get('short_question')[:40]}")

    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    assert res_json.get('success') is True, "Expected success to be True"
    assert len(questions) >= 3, f"Expected at least 3 questions, got {len(questions)}"
    print(">>> /api/parse-pdf TEST PASSED! <<<")

    print("\n=== 2. TESTING /api/v1/fast-save with .pdf ===")
    # Find a class, subject, chapter
    cls = ClassLevel.query.first()
    sub = Subject.query.filter_by(class_id=cls.id).first() if cls else None
    ch = Chapter.query.filter_by(subject_id=sub.id).first() if sub else None

    if cls and sub and ch:
        with open(pdf_path, 'rb') as f:
            data = {
                'class_id': cls.id,
                'subject_id': sub.id,
                'chapter_id': ch.id,
                'file': (io.BytesIO(f.read()), 'sample_test_questions.pdf', 'application/pdf')
            }
            res_save = client.post('/api/v1/fast-save', data=data, content_type='multipart/form-data')

        print(f"Fast Save Status: {res_save.status_code}")
        save_json = res_save.get_json()
        print("Save Success:", save_json.get('success'))
        print("Saved count:", save_json.get('count'))
        print("Speed:", save_json.get('speed_items_per_sec'), "items/sec")
        print("Message:", save_json.get('message'))
        assert res_save.status_code == 200, f"Expected 200, got {res_save.status_code}"
        assert save_json.get('success') is True, "Fast save failed"
        print(">>> /api/v1/fast-save with .pdf TEST PASSED! <<<")
    else:
        print("Skipping DB save test as default curriculum not found.")

print("\nALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
