import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db, Chapter, Question

with app.app_context():
    print("Database URI:", app.config['SQLALCHEMY_DATABASE_URI'])
    for ch_id in [644, 220, 645, 646]:
        ch = Chapter.query.get(ch_id)
        if ch:
            print(f"Chapter {ch.id} ({ch.chapter_no}: {ch.title}):")
            print(f"  len(ch.questions): {len(ch.questions)}")
            print(f"  Direct query count: {Question.query.filter_by(chapter_id=ch.id).count()}")
        else:
            print(f"Chapter {ch_id} not found!")
