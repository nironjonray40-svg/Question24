# -*- coding: utf-8 -*-
"""
Database insertion script for '৮ম শ্রেণি' -> 'বাংলা ১ম পত্র' -> 'গদ্য ১' -> 'অতিথির স্মৃতি (শরৎচন্দ্র চট্টোপাধ্যায়)'
Imports:
- 145 MCQ Questions
- 22 Short Questions
- 26 Creative Questions (CQ)
Total: 193 Questions
"""
import sys
import os

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, db
from models import ClassLevel, Subject, Chapter, Topic, Question

# Import question chunks
from scratch.questions_mcq_part1 import MCQ_PART_1
from scratch.questions_mcq_part2 import MCQ_PART_2
from scratch.questions_mcq_part3 import MCQ_PART_3
from scratch.questions_short import SHORT_QUESTIONS
from scratch.questions_cq_part1 import CQ_PART_1
from scratch.questions_cq_part2 import CQ_PART_2


def run_insertion():
    with app.app_context():
        print("=" * 60)
        print("DATABASE QUESTION INSERTION FOR 'অতিথির স্মৃতি'")
        print("=" * 60)

        # 1. Verify ClassLevel ('৮ম শ্রেণি')
        cls = ClassLevel.query.filter(ClassLevel.name.like('%৮ম শ্রেণি%')).first()
        if not cls:
            cls = ClassLevel.query.filter(ClassLevel.name.like('%৮ম%')).first()
        if not cls:
            print("[ERROR] '৮ম শ্রেণি' not found in database!")
            return

        print(f"[✓] Class: id={cls.id}, name={cls.name}")

        # 2. Verify Subject ('বাংলা ১ম পত্র')
        subject = Subject.query.filter(Subject.class_id == cls.id, Subject.name.like('%বাংলা ১ম পত্র%')).first()
        if not subject:
            subject = Subject.query.filter(Subject.class_id == cls.id, Subject.name.like('%বাংলা%')).first()
        if not subject:
            print("[ERROR] 'বাংলা ১ম পত্র' not found in database!")
            return

        print(f"[✓] Subject: id={subject.id}, name={subject.name}")

        # 3. Verify Chapter ('গদ্য ১' / 'অতিথির স্মৃতি')
        chapter = Chapter.query.filter(
            Chapter.subject_id == subject.id,
            (Chapter.title.like('%অতিথির স্মৃতি%') | Chapter.chapter_no.like('%গদ্য ১%'))
        ).first()
        if not chapter:
            chapter = Chapter(
                subject_id=subject.id,
                chapter_no="গদ্য ১",
                title="অতিথির স্মৃতি (শরৎচন্দ্র চট্টোপাধ্যায়)",
                order_num=1
            )
            db.session.add(chapter)
            db.session.commit()
            print(f"[✓] Created Chapter: id={chapter.id}")
        else:
            print(f"[✓] Chapter: id={chapter.id}, chapter_no={chapter.chapter_no}, title={chapter.title}")

        # 4. Verify or Create Topic ('অতিথির স্মৃতি (শরৎচন্দ্র চট্টোপাধ্যায়)')
        topic = Topic.query.filter(
            Topic.chapter_id == chapter.id,
            Topic.title.like('%অতিথির স্মৃতি%')
        ).first()
        if not topic:
            topic = Topic(
                chapter_id=chapter.id,
                title="পাঠ ১: অতিথির স্মৃতি (শরৎচন্দ্র চট্টোপাধ্যায়)",
                order_num=1
            )
            db.session.add(topic)
            db.session.commit()
            print(f"[✓] Created Topic: id={topic.id}, title={topic.title}")
        else:
            print(f"[✓] Topic: id={topic.id}, title={topic.title}")

        # 5. Clean up any previous questions for this chapter to ensure clean idempotency
        deleted_count = Question.query.filter_by(chapter_id=chapter.id).delete()
        db.session.commit()
        if deleted_count > 0:
            print(f"[i] Cleared {deleted_count} existing questions in Chapter {chapter.id} for clean insertion.")

        # Combine MCQs
        all_mcqs = MCQ_PART_1 + MCQ_PART_2 + MCQ_PART_3
        print(f"[i] Total MCQs to insert: {len(all_mcqs)}")

        mcq_added = 0
        for item in all_mcqs:
            q = Question(
                class_id=cls.id,
                subject_id=subject.id,
                chapter_id=chapter.id,
                topic_id=topic.id,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=item['stem'],
                option_a=item['options'].get('ক', ''),
                option_b=item['options'].get('খ', ''),
                option_c=item['options'].get('গ', ''),
                option_d=item['options'].get('ঘ', ''),
                correct_option=item['correct'],
                explanation=item.get('explanation', '')
            )
            db.session.add(q)
            mcq_added += 1

        db.session.commit()
        print(f"[✓] Successfully inserted {mcq_added} MCQ questions.")

        # 6. Insert Short Questions
        short_added = 0
        for item in SHORT_QUESTIONS:
            q = Question(
                class_id=cls.id,
                subject_id=subject.id,
                chapter_id=chapter.id,
                topic_id=topic.id,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=item['question'],
                short_answer=item['answer']
            )
            db.session.add(q)
            short_added += 1

        db.session.commit()
        print(f"[✓] Successfully inserted {short_added} Short questions.")

        # 7. Insert Creative Questions (CQ)
        all_cqs = CQ_PART_1 + CQ_PART_2
        print(f"[i] Total CQs to insert: {len(all_cqs)}")

        cq_added = 0
        for item in all_cqs:
            q = Question(
                class_id=cls.id,
                subject_id=subject.id,
                chapter_id=chapter.id,
                topic_id=topic.id,
                question_type='cq',
                difficulty='medium',
                marks=10.0,
                cq_stem=item['cq_stem'],
                cq_sub_ka=item['cq_sub_ka'],
                cq_sub_kha=item['cq_sub_kha'],
                cq_sub_ga=item['cq_sub_ga'],
                cq_sub_gha=item['cq_sub_gha'],
                cq_solution=item['cq_solution']
            )
            db.session.add(q)
            cq_added += 1

        db.session.commit()
        print(f"[✓] Successfully inserted {cq_added} Creative Questions (CQ).")

        # 8. Summary Verification
        total_in_chapter = Question.query.filter_by(chapter_id=chapter.id).count()
        total_in_db = Question.query.count()
        total_mcq = Question.query.filter_by(chapter_id=chapter.id, question_type='mcq').count()
        total_short = Question.query.filter_by(chapter_id=chapter.id, question_type='short').count()
        total_cq = Question.query.filter_by(chapter_id=chapter.id, question_type='cq').count()

        print("=" * 60)
        print("VERIFICATION SUMMARY:")
        print(f"  ● Class              : {cls.name}")
        print(f"  ● Subject            : {subject.name}")
        print(f"  ● Chapter            : {chapter.chapter_no} - {chapter.title}")
        print(f"  ● Topic              : {topic.title}")
        print(f"  ● বহুনির্বাচনি (MCQ) : {total_mcq} টি")
        print(f"  ● সংক্ষিপ্ত প্রশ্ন     : {total_short} টি")
        print(f"  ● সৃজনশীল প্রশ্ন (CQ) : {total_cq} টি")
        print(f"  ● সর্বমোট প্রশ্ন      : {total_in_chapter} টি (ডাটাবেজে মোট: {total_in_db} টি)")
        print("=" * 60)


if __name__ == '__main__':
    run_insertion()
