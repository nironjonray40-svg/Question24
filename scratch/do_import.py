# -*- coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Question, ClassLevel, Subject, Chapter
from scratch.mcq_part1 import MCQS_PART_1
from scratch.mcq_part2 import MCQS_PART_2
from scratch.mcq_part3 import MCQS_PART_3
from scratch.short_data import SHORTS_DATA
from scratch.cq_part1 import CQS_PART_1
from scratch.cq_part2 import CQS_PART_2
from scratch.cq_part3 import CQS_PART_3

all_mcqs = MCQS_PART_1 + MCQS_PART_2 + MCQS_PART_3
all_shorts = SHORTS_DATA
all_cqs = CQS_PART_1 + CQS_PART_2 + CQS_PART_3

print(f"Total MCQs prepared: {len(all_mcqs)}")
print(f"Total Short questions prepared: {len(all_shorts)}")
print(f"Total CQ questions prepared: {len(all_cqs)}")
print(f"Grand Total questions: {len(all_mcqs) + len(all_shorts) + len(all_cqs)}")

with app.app_context():
    cls = ClassLevel.query.filter(ClassLevel.name.like('%৮%')).first()
    sub = Subject.query.filter_by(class_id=cls.id).filter(Subject.name.like('%বাংলা ১ম%')).first()
    chap = Chapter.query.filter_by(subject_id=sub.id).filter(Chapter.title.like('%পড়ে পাওয়া%')).first()

    print(f"Target Hierarchy: Class ID={cls.id} ({cls.name}), Subject ID={sub.id} ({sub.name}), Chapter ID={chap.id} ({chap.chapter_no}: {chap.title})")

    # Clean existing questions under this chapter if any
    existing_count = Question.query.filter_by(chapter_id=chap.id).count()
    if existing_count > 0:
        print(f"Removing {existing_count} existing questions under chapter {chap.id} before fresh import...")
        Question.query.filter_by(chapter_id=chap.id).delete()
        db.session.commit()

    # 1. Insert MCQs
    print("Inserting 152 MCQs...")
    for idx, item in enumerate(all_mcqs, start=1):
        q = Question(
            class_id=cls.id,
            subject_id=sub.id,
            chapter_id=chap.id,
            topic_id=None,
            question_type='mcq',
            difficulty='medium',
            marks=1.0,
            mcq_stem=item['stem'].strip(),
            option_a=item['a'].strip(),
            option_b=item['b'].strip(),
            option_c=item['c'].strip(),
            option_d=item['d'].strip(),
            correct_option=item['ans'].strip(),
            explanation=item.get('exp', '').strip() or None
        )
        db.session.add(q)

    # 2. Insert Short Questions
    print("Inserting 22 Short Questions...")
    for idx, item in enumerate(all_shorts, start=1):
        q = Question(
            class_id=cls.id,
            subject_id=sub.id,
            chapter_id=chap.id,
            topic_id=None,
            question_type='short',
            difficulty='medium',
            marks=2.0,
            short_question=item['q'].strip(),
            short_answer=item['a'].strip()
        )
        db.session.add(q)

    # 3. Insert CQ Questions
    print("Inserting 21 CQ Questions...")
    for idx, item in enumerate(all_cqs, start=1):
        q = Question(
            class_id=cls.id,
            subject_id=sub.id,
            chapter_id=chap.id,
            topic_id=None,
            question_type='cq',
            difficulty='medium',
            marks=10.0,
            cq_stem=item['stem'].strip(),
            cq_sub_ka=item['ka'].strip(),
            cq_sub_kha=item['kha'].strip(),
            cq_sub_ga=item['ga'].strip(),
            cq_sub_gha=item['gha'].strip(),
            cq_solution=item['sol'].strip()
        )
        db.session.add(q)

    db.session.commit()
    print("DATABASE COMMIT SUCCESSFUL!")

    # Verify counts in database
    mcq_count = Question.query.filter_by(chapter_id=chap.id, question_type='mcq').count()
    short_count = Question.query.filter_by(chapter_id=chap.id, question_type='short').count()
    cq_count = Question.query.filter_by(chapter_id=chap.id, question_type='cq').count()
    total_count = Question.query.filter_by(chapter_id=chap.id).count()

    print(f"\nVerification in Database:")
    print(f"  MCQ count: {mcq_count} (Expected 152)")
    print(f"  Short count: {short_count} (Expected 22)")
    print(f"  CQ count: {cq_count} (Expected 21)")
    print(f"  Total count: {total_count} (Expected 195)")

    assert mcq_count == 152, f"MCQ count mismatch: {mcq_count}"
    assert short_count == 22, f"Short count mismatch: {short_count}"
    assert cq_count == 21, f"CQ count mismatch: {cq_count}"
    assert total_count == 195, f"Total count mismatch: {total_count}"
    print("\nALL 195 QUESTIONS VERIFIED SUCCESSFULLY IN DATABASE!")
