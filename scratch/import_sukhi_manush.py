# -*- coding: utf-8 -*-
"""
Ingestion script for:
Class: ৮ ম শ্রেণি (ClassLevel ID: 3)
Subject: বাংলা ১ম পত্র (Subject ID: 47)
Chapter: গদ্য ৭ - সুখী মানুষ (মমতাজউদদীন আহমদ) (Chapter ID: 637)

Imports:
- 158 MCQs (linked to Topic 7)
- 17 Short Questions (linked to Topic 6)
- 21 Creative Questions (linked to Topic 6)
Total: 196 Questions
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from sukhi_manush_mcqs_part1 import mcqs_part1
from sukhi_manush_mcqs_part2 import mcqs_part2
from sukhi_manush_short import short_questions
from sukhi_manush_cq_part1 import cqs_part1
from sukhi_manush_cq_part2 import cqs_part2

all_mcqs = mcqs_part1 + mcqs_part2
all_cqs = cqs_part1 + cqs_part2

TOPICS = [
    "পাঠ ১: 'সুখী মানুষ' নাটিকার প্রেক্ষাপট, চরিত্রসমূহ ও মূল বিষয়বস্তু বিশ্লেষণ",
    "পাঠ ২: মোড়লের অশান্তি, হাড় মড়মড় রোগ ও অনৈতিক উপার্জনের পরিণতি বিশ্লেষণ",
    "পাঠ ৩: নির্লোভ সুখী মানুষের জীবনদর্শন, সন্তুষ্টি ও প্রকৃত সুখের স্বরূপ বিশ্লেষণ",
    "পাঠ ৪: অন্তর্নিহিত ভাবার্থ, ব্যঙ্গাত্মক রূপ ও জীবনবোধের প্রকাশ",
    "পাঠ ৫: সমাজবাস্তবতা, লোভ-লালসার কুফল ও নৈতিক মূল্যবোধ",
    "পাঠ ৬: সৃজনশীল উদ্দীপক (CQ) ও অনুধাবনমূলক প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: পাঠ্যবইভিত্তিক বহুনির্বাচনি (MCQ) ও মূল্যায়ন"
]

def run_import():
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

        chapter_obj = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%সুখী মানুষ%')).first()
        if not chapter_obj:
            print("ERROR: Chapter 'সুখী মানুষ' not found in Subject 'বাংলা ১ম পত্র'!")
            return

        print("Target Hierarchy:")
        print(f"  Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"  Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"  Chapter: ID {chapter_obj.id} - '{chapter_obj.chapter_no}: {chapter_obj.title}'")

        # 2. Check and Create Topics
        existing_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=chapter_obj.id).all()}
        for idx, t_title in enumerate(TOPICS, 1):
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

        mcq_topic = None
        cq_topic = None
        for t in topics:
            if "MCQ" in t.title or "বহুনির্বাচনি" in t.title:
                mcq_topic = t
            elif "(CQ)" in t.title or "সৃজনশীল" in t.title:
                cq_topic = t

        if not mcq_topic and topics:
            mcq_topic = topics[-1]
        if not cq_topic and topics:
            cq_topic = topics[-2] if len(topics) >= 2 else topics[0]

        print(f"  MCQ Topic : ID {mcq_topic.id} - '{mcq_topic.title}'")
        print(f"  CQ Topic  : ID {cq_topic.id} - '{cq_topic.title}'")

        # 3. Clean up any existing questions in this chapter if any (to avoid duplicates)
        existing_q_count = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        if existing_q_count > 0:
            print(f"\nWarning: Found {existing_q_count} existing questions in chapter {chapter_obj.id}. Deleting before re-import...")
            Question.query.filter_by(chapter_id=chapter_obj.id).delete()
            db.session.commit()
            print("Existing questions deleted.")

        # 4. Insert 158 MCQs
        mcq_count = 0
        for item in all_mcqs:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=mcq_topic.id,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=item['stem'],
                option_a=item['option_a'],
                option_b=item['option_b'],
                option_c=item['option_c'],
                option_d=item['option_d'],
                correct_option=item['correct_option'],
                explanation=item.get('explanation')
            )
            db.session.add(q)
            mcq_count += 1
        print(f"Prepared {mcq_count} MCQ questions.")

        # 5. Insert 17 Short Questions
        short_count = 0
        for item in short_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=cq_topic.id,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['q'],
                short_answer=item['ans']
            )
            db.session.add(q)
            short_count += 1
        print(f"Prepared {short_count} Short questions.")

        # 6. Insert 21 Creative Questions (CQs)
        cq_count = 0
        for item in all_cqs:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=cq_topic.id,
                question_type='cq',
                difficulty='medium',
                marks=10.0,
                cq_stem=item['stem'],
                cq_sub_ka=item['ka'],
                cq_sub_kha=item['kha'],
                cq_sub_ga=item['ga'],
                cq_sub_gha=item['gha'],
                cq_solution=item['solution']
            )
            db.session.add(q)
            cq_count += 1
        print(f"Prepared {cq_count} CQ questions.")

        # Commit to database
        db.session.commit()
        print("\n=== SUCCESS ===")
        print("Successfully committed all questions to database!")
        print(f"● MCQs inserted    : {mcq_count}")
        print(f"● Short questions  : {short_count}")
        print(f"● CQ questions     : {cq_count}")
        print(f"● Total inserted   : {mcq_count + short_count + cq_count}")

        # Final Verification
        final_total = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        final_mcq = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='mcq').count()
        final_short = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='short').count()
        final_cq = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='cq').count()

        print("\nVerification from database query:")
        print(f"  Total in Chapter: {final_total}")
        print(f"  MCQs            : {final_mcq}")
        print(f"  Short Questions : {final_short}")
        print(f"  CQs             : {final_cq}")
        
        assert final_total == 196
        assert final_mcq == 158
        assert final_short == 17
        assert final_cq == 21
        print("\n✓ ALL ASSERTIONS PASSED!")

if __name__ == '__main__':
    run_import()
