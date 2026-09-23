# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from library_mcqs_part1 import mcqs_part1
from library_mcqs_part2 import mcqs_part2
from library_short import short_questions
from library_cq_part1 import cqs_part1
from library_cq_part2 import cqs_part2

all_mcqs = mcqs_part1 + mcqs_part2
all_cqs = cqs_part1 + cqs_part2

CURRICULUM_TOPICS = [
    "পাঠ ১: লাইব্রেরির গুরুত্ব, প্রয়োজনীয়তা ও বিষয়বস্তু বিশ্লেষণ",
    "পাঠ ২: লাইব্রেরির প্রকারভেদ (ব্যক্তিগত, পারিবারিক ও সাধারণ) ও বিষয়বস্তু বিশ্লেষণ",
    "পাঠ ৩: জ্ঞানচর্চা, বুদ্ধির মুক্তি ও জাতীয় জীবনে লাইব্রেরির ভূমিকা ও বিষয়বস্তু বিশ্লেষণ",
    "পাঠ ৪: অন্তর্নিহিত ভাবার্থ, চরিত্র বিশ্লেষণ ও জীবনবোধের প্রকাশ",
    "পাঠ ৫: সমাজবাস্তবতা, মানবিক মূল্যবোধ ও সমকালীন প্রাসঙ্গিকতা",
    "পাঠ ৬: সৃজনশীল উদ্দীপক (CQ) ও অনুধাবনমূলক প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: পাঠ্যবইভিত্তিক বহুনির্বাচনি (MCQ) ও মূল্যায়ন"
]

def run_import():
    print("=== STARTING IMPORT FOR 'লাইব্রেরি (মোতাহের হোসেন চৌধুরী)' ===")
    print(f"Loaded MCQs count           : {len(all_mcqs)}")
    print(f"Loaded Short Questions count: {len(short_questions)}")
    print(f"Loaded CQ Questions count   : {len(all_cqs)}")
    print(f"Total questions to import   : {len(all_mcqs) + len(short_questions) + len(all_cqs)}")
    
    assert len(all_mcqs) == 139, f"Expected 139 MCQs, got {len(all_mcqs)}"
    assert len(short_questions) == 13, f"Expected 13 Short questions, got {len(short_questions)}"
    assert len(all_cqs) == 20, f"Expected 20 CQs, got {len(all_cqs)}"

    with app.app_context():
        # 1. Resolve Class, Subject, Chapter
        class_obj = ClassLevel.query.filter(ClassLevel.name.like('%৮ম%')).first()
        if not class_obj:
            print("ERROR: Class 8 not found!")
            return
        
        subject_obj = Subject.query.filter(Subject.class_id == class_obj.id, Subject.name.like('%বাংলা ১ম%')).first()
        if not subject_obj:
            print("ERROR: Subject 'বাংলা ১ম পত্র' not found in Class 8!")
            return
            
        chapter_obj = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%লাইব্রেরি%')).first()
        if not chapter_obj:
            print("ERROR: Chapter 'লাইব্রেরি' not found in Subject 'বাংলা ১ম পত্র'!")
            return
            
        print(f"\nTarget Hierarchy:")
        print(f"  Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"  Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"  Chapter: ID {chapter_obj.id} - '{chapter_obj.chapter_no}: {chapter_obj.title}'")

        # 2. Ensure Topics exist for Chapter 636
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
        print(f"Total Topics in Chapter: {len(topics)}")

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

        print(f"  MCQ Topic : ID {mcq_topic.id if mcq_topic else None} - '{mcq_topic.title if mcq_topic else None}'")
        print(f"  CQ Topic  : ID {cq_topic.id if cq_topic else None} - '{cq_topic.title if cq_topic else None}'")

        # 3. Check existing questions in this chapter
        existing_q_count = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        print(f"\nExisting questions count in chapter before import: {existing_q_count}")
        if existing_q_count > 0:
            print("WARNING: Questions already exist in this chapter. Aborting to avoid duplicates.")
            return

        # 4. Insert 139 MCQs
        mcq_count = 0
        for item in all_mcqs:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=mcq_topic.id if mcq_topic else None,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=item['stem'],
                option_a=item['option_a'],
                option_b=item['option_b'],
                option_c=item['option_c'],
                option_d=item['option_d'],
                correct_option=item['correct_option'],
                explanation=item['explanation']
            )
            db.session.add(q)
            mcq_count += 1
        print(f"Added {mcq_count} MCQ questions.")

        # 5. Insert 13 Short Questions
        short_count = 0
        for item in short_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=chapter_obj.id,
                topic_id=cq_topic.id if cq_topic else None,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['q'],
                short_answer=item['ans']
            )
            db.session.add(q)
            short_count += 1
        print(f"Added {short_count} Short questions.")

        # 6. Insert 20 Creative Questions (CQ)
        cq_count = 0
        for item in all_cqs:
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
                cq_sub_ga=item['ga'],
                cq_sub_gha=item['gha'],
                cq_solution=item['solution']
            )
            db.session.add(q)
            cq_count += 1
        print(f"Added {cq_count} CQ questions.")

        # Commit to database
        db.session.commit()
        print("\n=== COMMIT SUCCESSFUL ===")
        print(f"● MCQs inserted    : {mcq_count}")
        print(f"● Short questions  : {short_count}")
        print(f"● CQ questions     : {cq_count}")
        print(f"● Total inserted   : {mcq_count + short_count + cq_count}")

        # Final Verification
        final_total = Question.query.filter_by(chapter_id=chapter_obj.id).count()
        final_mcq = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='mcq').count()
        final_short = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='short').count()
        final_cq = Question.query.filter_by(chapter_id=chapter_obj.id, question_type='cq').count()

        print("\nDatabase Verification Query Results:")
        print(f"  Total in Chapter: {final_total}")
        print(f"  MCQs            : {final_mcq}")
        print(f"  Short Questions : {final_short}")
        print(f"  CQs             : {final_cq}")

if __name__ == '__main__':
    run_import()
