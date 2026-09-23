# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from ebaresongram_mcqs_part1 import mcqs_part1
from ebaresongram_mcqs_part2 import mcqs_part2
from ebaresongram_short import short_questions
from ebaresongram_cq_part1 import cqs_part1
from ebaresongram_cq_part2 import cqs_part2

all_mcqs = mcqs_part1 + mcqs_part2
all_cqs = cqs_part1 + cqs_part2

def run_import():
    print("=== STARTING IMPORT FOR 'এবারের সংগ্রাম স্বাধীনতার সংগ্রাম (বঙ্গবন্ধু শেখ মুজিবুর রহমান)' ===")
    print(f"Loaded MCQs count           : {len(all_mcqs)}")
    print(f"Loaded Short Questions count: {len(short_questions)}")
    print(f"Loaded CQ Questions count   : {len(all_cqs)}")
    print(f"Total questions to import   : {len(all_mcqs) + len(short_questions) + len(all_cqs)}")
    
    assert len(all_mcqs) == 97, f"Expected 97 MCQs, got {len(all_mcqs)}"
    assert len(short_questions) == 5, f"Expected 5 Short questions, got {len(short_questions)}"
    assert len(all_cqs) == 10, f"Expected 10 CQs, got {len(all_cqs)}"

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
            
        chapter_obj = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%এবারের সংগ্রাম%')).first()
        if not chapter_obj:
            print("ERROR: Chapter 'এবারের সংগ্রাম' not found in Subject 'বাংলা ১ম পত্র'!")
            return
            
        print(f"\nTarget Hierarchy:")
        print(f"  Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"  Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"  Chapter: ID {chapter_obj.id} - '{chapter_obj.chapter_no}: {chapter_obj.title}'")

        # 2. Resolve Topics
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

        # 4. Insert 97 MCQs
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

        # 5. Insert 5 Short Questions
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

        # 6. Insert 10 Creative Questions (CQ)
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
