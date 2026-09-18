import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
import app

with app.app.app_context():
    shorts = app.Question.query.filter_by(chapter_id=1, question_type='short').order_by(app.Question.id).all()
    print(f"Total Short Questions: {len(shorts)}")
    for i, s in enumerate(shorts):
        print(f"[{i+1}] (ID={s.id}) {s.short_question}")
        print(f"     Ans: {s.short_answer[:70]}...\n")
