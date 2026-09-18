import sys
import os
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
from app import app
from models import ClassLevel, Subject, Chapter, Topic

with app.app_context():
    c = ClassLevel.query.filter(ClassLevel.name.like('%৯ম-১০ম%')).first()
    print(f"Class: {c.id} - {c.name}")
    for s in c.subjects:
        if 'বাংলা' in s.name:
            print(f"  Subject: {s.id} - {s.name}")
            for ch in s.chapters:
                print(f"    Chapter: {ch.id} - {ch.chapter_no} - {ch.title}")
