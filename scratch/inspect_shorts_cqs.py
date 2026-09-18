import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
import app

with app.app.app_context():
    shorts = app.Question.query.filter_by(chapter_id=1, question_type='short').order_by(app.Question.id).all()
    cqs = app.Question.query.filter_by(chapter_id=1, question_type='cq').order_by(app.Question.id).all()
    print(f"Existing Short questions count: {len(shorts)}")
    print(f"Existing CQ count: {len(cqs)}")
    
    print("\n--- Short Questions sample ---")
    for i, s in enumerate(shorts[:5]):
        print(f"[{i+1}] Q: {s.short_question}")
        print(f"     A: {s.short_answer[:80]}...\n")
        
    print("\n--- CQs sample ---")
    for i, c in enumerate(cqs[:5]):
        print(f"[{i+1}] Stem: {c.cq_stem[:80]}...")
        print(f"     ক: {c.cq_sub_ka}")
        print(f"     খ: {c.cq_sub_kha}")
        print(f"     গ: {c.cq_sub_ga}")
        print(f"     ঘ: {c.cq_sub_gha}\n")
