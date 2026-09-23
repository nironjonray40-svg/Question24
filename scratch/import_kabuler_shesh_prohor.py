# -*- coding: utf-8 -*-
"""
Ingestion script for:
Class: ৮ ম শ্রেণি (ClassLevel ID: 3)
Subject: বাংলা ১ম পত্র (Subject ID: 47)
Chapter: আনন্দপাঠ - ভ্রমণ-কাহিনি : কাবুলের শেষ প্রহর (সৈয়দ মুজতবা আলী) (Chapter ID: 659)

Imports:
- 8 Creative / Descriptive Questions (CQ, 10 marks each) from ক্রিয়েটিভ মডেল স্কুল
- 16 Short / Analytical Questions (Short, 2 marks each) from ক্রিয়েটিভ মডেল স্কুল
Total: 24 Questions
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from kabuler_shesh_prohor_cqs import cqs
from kabuler_shesh_prohor_short import short_questions

CURRICULUM_TOPICS = [
    "পাঠ ১: 'কাবুলের শেষ প্রহর' ভ্রমণকাহিনির প্রেক্ষাপট ও মূল বিষয়বস্তু বিশ্লেষণ",
    "পাঠ ২: আবদুর রহমানের চারিত্রিক বৈশিষ্ট্য, বিশ্বস্ততা ও মানবতাবোধ",
    "পাঠ ৩: লেখক ও আবদুর রহমানের মানবিক সম্পর্ক ও সৌহার্দ্য",
    "পাঠ ৪: বিদায়লগ্নের আবেগঘন মুহূর্ত, অনুভূতি ও 'খণ্ড-মৃত্যু' উপলব্ধি",
    "পাঠ ৫: লেখক পরিচিতি (সৈয়দ মুজতবা আলী) ও ভ্রমণকাহিনি বিশ্লেষণ",
    "পাঠ ৬: সৃজনশীল ও বর্ণনামূলক প্রশ্নোত্তর (CQ) অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও জ্ঞানমূলক প্রশ্নোত্তর অনুশীলন"
]

def run_import():
    print("=== STARTING IMPORT FOR 'ভ্রমণ-কাহিনি : কাবুলের শেষ প্রহর (সৈয়দ মুজতবা আলী)' ===")
    print(f"Loaded CQ Questions count   : {len(cqs)}")
    print(f"Loaded Short Questions count: {len(short_questions)}")
    print(f"Total questions to import   : {len(cqs) + len(short_questions)}")
    
    assert len(cqs) == 8, f"Expected 8 CQs, got {len(cqs)}"
    assert len(short_questions) == 16, f"Expected 16 Short questions, got {len(short_questions)}"

    with app.app_context():
        # 1. Resolve Class, Subject, Chapter
        class_obj = ClassLevel.query.filter(ClassLevel.name.like('%৮ম%')).first()
        if not class_obj:
            print("ERROR: Class '৮ম শ্রেণি' not found!")
            return

        subject_obj = Subject.query.filter(Subject.class_id == class_obj.id, Subject.name.like('%বাংলা ১ম%')).first()
        if not subject_obj:
            print("ERROR: Subject 'বাংলা ১ম পত্র' not found in Class 8!")
            return

        chapter_obj = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%কাবুল%')).first()
        if not chapter_obj:
            print("ERROR: Chapter 'কাবুলের শেষ প্রহর' not found in Subject 'বাংলা ১ম পত্র'!")
            return

        print("\nTarget Hierarchy:")
        print(f"  Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"  Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"  Chapter: ID {chapter_obj.id} - '{chapter_obj.chapter_no}: {chapter_obj.title}'")

        # 2. Check and Create Topics
        existing_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=chapter_obj.id).all()}
        for idx, t_title in enumerate(CURRICULUM_TOPICS, 1):
            if t_title not in existing_topics:
                new_topic = Topic(chapter_id=chapter_obj.id, title=t_title, order_num=idx)
                db.session.add(new_topic)
                print(f"  + Added Topic: {t_title}")
            else:
                existing_topics[t_title].order_num = idx
        db.session.commit()

        # Re-fetch topics
        topics = Topic.query.filter_by(chapter_id=chapter_obj.id).order_by(Topic.order_num).all()
        print(f"\nTotal Topics in Chapter {chapter_obj.id}: {len(topics)}")

        cq_topic = None
        short_topic = None
        for t in topics:
            if "(CQ)" in t.title or "সৃজনশীল" in t.title:
                cq_topic = t
            elif "সংক্ষিপ্ত" in t.title:
                short_topic = t

        if not cq_topic and topics:
            cq_topic = topics[-2] if len(topics) >= 2 else topics[0]
        if not short_topic and topics:
            short_topic = topics[-1]

        print(f"  CQ Topic   : ID {cq_topic.id if cq_topic else None} - '{cq_topic.title if cq_topic else None}'")
        print(f"  Short Topic: ID {short_topic.id if short_topic else None} - '{short_topic.title if short_topic else None}'")

        # 3. Clean up any existing questions in this chapter if any (to avoid duplicates)
        existing_q_count = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        if existing_q_count > 0:
            print(f"\nWarning: Found {existing_q_count} existing questions in chapter {chapter_obj.id}. Deleting before re-import...")
            Question.query.filter_by(chapter_id=chapter_obj.id).delete()
            db.session.commit()
            print("Existing questions deleted.")

        # 4. Insert 8 CQ Questions
        cq_count = 0
        for item in cqs:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=cq_topic.id if cq_topic else None,
                question_type='cq',
                difficulty='medium',
                marks=10.0,
                cq_stem=item['stem'],
                cq_sub_ka=item['ka'],
                cq_sub_kha=item['kha'],
                cq_sub_ga=item.get('ga'),
                cq_sub_gha=item.get('gha'),
                cq_solution=item['solution']
            )
            db.session.add(q)
            cq_count += 1
        print(f"Prepared {cq_count} CQ questions.")

        # 5. Insert 16 Short Questions
        short_count = 0
        for item in short_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=short_topic.id if short_topic else None,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['q'],
                short_answer=item['ans']
            )
            db.session.add(q)
            short_count += 1
        print(f"Prepared {short_count} Short questions.")

        # Commit to database
        db.session.commit()
        print("\n=== SUCCESS ===")
        print("Successfully committed all questions to database!")
        print(f"● CQ questions     : {cq_count}")
        print(f"● Short questions  : {short_count}")
        print(f"● Total inserted   : {cq_count + short_count}")

        # Final Verification
        final_total = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        final_cq = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='cq').count()
        final_short = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='short').count()

        print("\nVerification from database query:")
        print(f"  Total in Chapter: {final_total}")
        print(f"  CQs             : {final_cq}")
        print(f"  Short Questions : {final_short}")
        
        assert final_total == 24
        assert final_cq == 8
        assert final_short == 16
        print("\n✓ ALL ASSERTIONS PASSED!")

if __name__ == '__main__':
    run_import()
