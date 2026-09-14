import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.stdout.reconfigure(encoding='utf-8')
from app import app, db
from models import ClassLevel, Subject, Chapter, Question

with app.app_context():
    chapters = Chapter.query.filter(Chapter.title.like('%সুভা%')).all()
    print('Found chapters:', len(chapters))
    for ch in chapters:
        sub = Subject.query.get(ch.subject_id)
        cl = ClassLevel.query.get(sub.class_id) if sub else None
        print(f"Chapter ID: {ch.id}, Title: {ch.title}, Subject: {sub.name if sub else ''}, Class: {cl.name if cl else ''}")
        
        mcqs = Question.query.filter_by(chapter_id=ch.id, question_type='mcq').count()
        shorts = Question.query.filter_by(chapter_id=ch.id, question_type='short').all()
        cqs = Question.query.filter_by(chapter_id=ch.id, question_type='cq').all()
        print(f"  MCQ: {mcqs}, Short: {len(shorts)}, CQ: {len(cqs)}")
        print("\n--- SHORT QUESTIONS ---")
        for i, s in enumerate(shorts, 1):
            print(f"  [{i}] ID: {s.id}")
            print(f"      Q: {s.short_question}")
            print(f"      A: {s.short_answer}")
        print("\n--- CREATIVE QUESTIONS (CQ) ---")
        for i, c in enumerate(cqs, 1):
            print(f"  [{i}] ID: {c.id}")
            print(f"      Stem: {c.cq_stem[:80] if c.cq_stem else ''}...")
            print(f"      ক: {c.cq_sub_ka}")
            print(f"      খ: {c.cq_sub_kha}")
            print(f"      গ: {c.cq_sub_ga}")
            print(f"      ঘ: {c.cq_sub_gha}")
            print(f"      Solution:\n{c.cq_solution}\n")
