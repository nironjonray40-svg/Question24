# -*- coding: utf-8 -*-
"""
Import script for:
1. কবিতা ২ : বঙ্গভূমির প্রতি (মাইকেল মধুসূদন দত্ত) [Chapter ID: 217]
   - 136 MCQs -> Topic ID: 1402
   - 11 Short Questions -> Topic ID: 1401
   - 15 Creative Questions -> Topic ID: 1401
   Total: 162 questions

2. কবিতা ১ : মানব ধর্ম (লালন শাহ) [Chapter ID: 216]
   - 122 MCQs -> Topic ID: 1395
   - 18 Short Questions -> Topic ID: 1394
   - 17 Creative Questions -> Topic ID: 1394
   Total: 157 questions

Combined Total: 319 questions
Syncs to both instance/question_bank.db and root question_bank.db
"""

import sys
import io
import os
import shutil

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from bongobhumir_mcqs_part1 import bongobhumir_mcqs
from bongobhumir_mcqs_part2 import bongobhumir_mcqs_part2
from bongobhumir_short_cqs import bongobhumir_shorts, bongobhumir_cqs

from manobdhormo_mcqs_part1 import manobdhormo_mcqs_part1
from manobdhormo_mcqs_part2 import manobdhormo_mcqs_part2
from manobdhormo_short_cqs import manobdhormo_shorts, manobdhormo_cqs

all_bongobhumir_mcqs = bongobhumir_mcqs + bongobhumir_mcqs_part2
all_manobdhormo_mcqs = manobdhormo_mcqs_part1 + manobdhormo_mcqs_part2

def run_import():
    print("==================================================")
    print("STARTING IMPORT FOR BANGLA 1ST PAPER POETRY")
    print("==================================================")
    print(f"Bongobhumir Proti - MCQs: {len(all_bongobhumir_mcqs)}, Shorts: {len(bongobhumir_shorts)}, CQs: {len(bongobhumir_cqs)}")
    print(f"Manobdhormo       - MCQs: {len(all_manobdhormo_mcqs)}, Shorts: {len(manobdhormo_shorts)}, CQs: {len(manobdhormo_cqs)}")
    print(f"Grand Total Questions to Insert: {len(all_bongobhumir_mcqs) + len(bongobhumir_shorts) + len(bongobhumir_cqs) + len(all_manobdhormo_mcqs) + len(manobdhormo_shorts) + len(manobdhormo_cqs)}")

    with app.app_context():
        # Clean any existing questions in Chapter 216 and 217 if any
        deleted_216 = Question.query.filter_by(chapter_id=216).delete()
        deleted_217 = Question.query.filter_by(chapter_id=217).delete()
        db.session.commit()
        print(f"Cleaned previous questions: Ch 216: {deleted_216}, Ch 217: {deleted_217}")

        # -----------------------------------------------------------------
        # 1. Import Chapter 217: বঙ্গভূমির প্রতি
        # -----------------------------------------------------------------
        ch217 = Chapter.query.get(217)
        assert ch217 is not None, "Chapter 217 not found!"
        class_id = ch217.subject.class_id
        subject_id = ch217.subject_id

        # Topics for 217
        topic_mcq_217 = Topic.query.filter_by(chapter_id=217, order_num=7).first()
        topic_cq_217 = Topic.query.filter_by(chapter_id=217, order_num=6).first()
        assert topic_mcq_217 is not None, "Topic 7 for 217 not found!"
        assert topic_cq_217 is not None, "Topic 6 for 217 not found!"

        # Insert 136 MCQs for 217
        for item in all_bongobhumir_mcqs:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=217,
                topic_id=topic_mcq_217.id,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=item['stem'],
                option_a=item['a'],
                option_b=item['b'],
                option_c=item['c'],
                option_d=item['d'],
                correct_option=item['ans'],
                explanation=item['exp']
            )
            db.session.add(q)

        # Insert 11 Shorts for 217
        for item in bongobhumir_shorts:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=217,
                topic_id=topic_cq_217.id,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['q'],
                short_answer=item['ans']
            )
            db.session.add(q)

        # Insert 15 CQs for 217
        for item in bongobhumir_cqs:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=217,
                topic_id=topic_cq_217.id,
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

        db.session.commit()
        print("✓ Successfully inserted all questions for Chapter 217 (বঙ্গভূমির প্রতি)")

        # -----------------------------------------------------------------
        # 2. Import Chapter 216: মানব ধর্ম
        # -----------------------------------------------------------------
        ch216 = Chapter.query.get(216)
        assert ch216 is not None, "Chapter 216 not found!"

        # Topics for 216
        topic_mcq_216 = Topic.query.filter_by(chapter_id=216, order_num=7).first()
        topic_cq_216 = Topic.query.filter_by(chapter_id=216, order_num=6).first()
        assert topic_mcq_216 is not None, "Topic 7 for 216 not found!"
        assert topic_cq_216 is not None, "Topic 6 for 216 not found!"

        # Insert 122 MCQs for 216
        for item in all_manobdhormo_mcqs:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=216,
                topic_id=topic_mcq_216.id,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=item['stem'],
                option_a=item['a'],
                option_b=item['b'],
                option_c=item['c'],
                option_d=item['d'],
                correct_option=item['ans'],
                explanation=item['exp']
            )
            db.session.add(q)

        # Insert 18 Shorts for 216
        for item in manobdhormo_shorts:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=216,
                topic_id=topic_cq_216.id,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['q'],
                short_answer=item['ans']
            )
            db.session.add(q)

        # Insert 17 CQs for 216
        for item in manobdhormo_cqs:
            q = Question(
                class_id=class_id,
                subject_id=subject_id,
                chapter_id=216,
                topic_id=topic_cq_216.id,
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

        db.session.commit()
        print("✓ Successfully inserted all questions for Chapter 216 (মানব ধর্ম)")

        # Sync to root question_bank.db
        src_db = 'instance/question_bank.db'
        dst_db = 'question_bank.db'
        if os.path.exists(src_db):
            shutil.copy2(src_db, dst_db)
            print(f"✓ Synchronized {src_db} -> {dst_db}")

        # Verification
        print("\n--- FINAL VERIFICATION ---")
        q217_total = Question.query.filter_by(chapter_id=217).count()
        q217_mcq = Question.query.filter_by(chapter_id=217, question_type='mcq').count()
        q217_short = Question.query.filter_by(chapter_id=217, question_type='short').count()
        q217_cq = Question.query.filter_by(chapter_id=217, question_type='cq').count()

        print(f"Chapter 217 (বঙ্গভূমির প্রতি): Total={q217_total} (MCQs={q217_mcq}, Shorts={q217_short}, CQs={q217_cq})")
        assert q217_total == 162, f"Expected 162, got {q217_total}"
        assert q217_mcq == 136, f"Expected 136, got {q217_mcq}"
        assert q217_short == 11, f"Expected 11, got {q217_short}"
        assert q217_cq == 15, f"Expected 15, got {q217_cq}"

        q216_total = Question.query.filter_by(chapter_id=216).count()
        q216_mcq = Question.query.filter_by(chapter_id=216, question_type='mcq').count()
        q216_short = Question.query.filter_by(chapter_id=216, question_type='short').count()
        q216_cq = Question.query.filter_by(chapter_id=216, question_type='cq').count()

        print(f"Chapter 216 (মানব ধর্ম): Total={q216_total} (MCQs={q216_mcq}, Shorts={q216_short}, CQs={q216_cq})")
        assert q216_total == 157, f"Expected 157, got {q216_total}"
        assert q216_mcq == 122, f"Expected 122, got {q216_mcq}"
        assert q216_short == 18, f"Expected 18, got {q216_short}"
        assert q216_cq == 17, f"Expected 17, got {q216_cq}"

        # Check for forbidden tag
        forbidden_tags = Question.query.filter(
            Question.chapter_id.in_([216, 217]),
            (Question.mcq_stem.like('%ক্রিয়েটিভ মডেল স্কুল%') |
             Question.cq_stem.like('%ক্রিয়েটিভ মডেল স্কুল%') |
             Question.short_question.like('%ক্রিয়েটিভ মডেল স্কুল%'))
        ).count()
        print(f"Check for forbidden [ক্রিয়েটিভ মডেল স্কুল] tag: {forbidden_tags} found (must be 0)")
        assert forbidden_tags == 0, f"Found {forbidden_tags} questions with [ক্রিয়েটিভ মডেল স্কুল] tag!"

        print("\nALL VERIFICATIONS PASSED 100%!")

if __name__ == '__main__':
    run_import()
