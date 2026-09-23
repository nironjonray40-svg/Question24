# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Topic
from kabuler_shesh_prohor_cqs import cqs

def execute_update():
    print("=== EXECUTING KABUL DESCRIPTIVE QUESTIONS UPDATE ===")
    with app.app_context():
        chapter = Chapter.query.get(659)
        if not chapter:
            print("ERROR: Chapter 659 not found!")
            return

        print(f"Target Chapter: ID {chapter.id} - '{chapter.title}'")

        # 1. Topic for descriptive questions
        topic = Topic.query.filter(
            Topic.chapter_id == 659,
            Topic.title.like('%বর্ণনামূলক%') | Topic.title.like('%সৃজনশীল%')
        ).first()
        topic_id = topic.id if topic else None
        print(f"Assigned Topic: ID {topic_id} - '{topic.title if topic else 'None'}'")

        # 2. Delete the 16 redundant short questions in chapter 659
        deleted_shorts = Question.query.filter_by(chapter_id=659, question_type='short').delete()
        print(f"Deleted {deleted_shorts} redundant short questions.")

        # 3. Clean and format the 8 descriptive questions
        # First check existing CQs in chapter 659
        existing_cqs = Question.query.filter_by(chapter_id=659).order_by(Question.id).all()
        print(f"Found {len(existing_cqs)} existing questions in chapter 659.")

        if len(existing_cqs) == 8:
            # Update existing 8 questions in place
            for idx, q_obj in enumerate(existing_cqs):
                data = cqs[idx]
                q_obj.question_type = 'descriptive'
                q_obj.topic_id = topic_id
                q_obj.marks = 10.0
                q_obj.difficulty = 'medium'
                q_obj.cq_stem = None
                q_obj.cq_sub_ka = data['ka'].strip()
                # Attach school tag to kha so extractSourceInfo detects it and cleanQuestionText strips it on display
                kha_text = data['kha'].strip()
                if '[ক্রিয়েটিভ মডেল স্কুল]' not in kha_text:
                    kha_text += ' [ক্রিয়েটিভ মডেল স্কুল]'
                q_obj.cq_sub_kha = kha_text
                q_obj.cq_sub_ga = None
                q_obj.cq_sub_gha = None
                q_obj.cq_solution = data['solution'].strip()
                print(f"  Updated Q{idx+1} (ID: {q_obj.id}) -> Type: descriptive, Marks: 10.0")
        else:
            # Delete all and recreate 8 descriptive questions cleanly
            Question.query.filter_by(chapter_id=659).delete()
            for idx, data in enumerate(cqs, 1):
                kha_text = data['kha'].strip()
                if '[ক্রিয়েটিভ মডেল স্কুল]' not in kha_text:
                    kha_text += ' [ক্রিয়েটিভ মডেল স্কুল]'
                new_q = Question(
                    class_id=3,
                    subject_id=47,
                    chapter_id=659,
                    topic_id=topic_id,
                    question_type='descriptive',
                    difficulty='medium',
                    marks=10.0,
                    cq_stem=None,
                    cq_sub_ka=data['ka'].strip(),
                    cq_sub_kha=kha_text,
                    cq_sub_ga=None,
                    cq_sub_gha=None,
                    cq_solution=data['solution'].strip()
                )
                db.session.add(new_q)
                print(f"  Inserted Q{idx} -> Type: descriptive, Marks: 10.0")

        db.session.commit()
        print("\n=== DATABASE COMMIT SUCCESSFUL ===")

        # Verification
        final_qs = Question.query.filter_by(chapter_id=659).order_by(Question.id).all()
        print(f"Final questions count in chapter 659: {len(final_qs)}")
        assert len(final_qs) == 8, f"Expected exactly 8 questions, found {len(final_qs)}"

        for i, q in enumerate(final_qs, 1):
            print(f"\n--- {i} নং প্রশ্ন (ID: {q.id}) ---")
            print(f"  ধরণ: {q.question_type}")
            print(f"  পূর্ণমান: {q.marks}")
            print(f"  ক: {q.cq_sub_ka[:60]}...")
            print(f"  খ: {q.cq_sub_kha[:60]}...")
            print(f"  উত্তর দৈর্ঘ্য: {len(q.cq_solution)} অক্ষর")
            assert q.question_type == 'descriptive'
            assert q.marks == 10.0
            assert q.cq_sub_ka is not None
            assert q.cq_sub_kha is not None
            assert q.cq_solution is not None

        print("\n✓ ALL 8 DESCRIPTIVE QUESTIONS VERIFIED PERFECTLY!")

if __name__ == '__main__':
    execute_update()
