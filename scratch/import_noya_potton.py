# -*- coding: utf-8 -*-
"""
Ingestion script for:
Class: ৮ম শ্রেণি (ClassLevel ID: 3)
Subject: বাংলা ১ম পত্র (Subject ID: 47)
Chapter: আনন্দপাঠ - নয়া পত্তন (জহির রায়হান) (Chapter ID: 652)
Total Questions: 10
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic
from noya_potton_questions import noya_potton_questions

TOPICS_NOYA_POTTON = [
    "পাঠ ১: 'নয়া পত্তন' গল্পের প্রেক্ষাপট, গ্রামীণ বাস্তবতা ও শনু পণ্ডিতের মহৎ স্বপ্ন",
    "পাঠ ২: গ্রামের একমাত্র স্কুল প্রতিষ্ঠা, জমিদারের ভূমিকা ও শনু পণ্ডিতের আত্মত্যাগ",
    "পাঠ ৩: আকস্মিক ঝড়ে স্কুল ধ্বংস ও সরকারি দপ্তর ও জমিদারের অসহযোগিতা",
    "পাঠ ৪: গ্রামবাসীর ঐক্যবদ্ধ উদ্যোগ, ছনের স্কুল পুনর্নির্মাণ ও 'শনু পণ্ডিতের ইস্কুল' নামকরণ",
    "পাঠ ৫: কথাসাহিত্যিক ও চলচ্চিত্রকার জহির রায়হানের সাহিত্যকর্ম ও সমাজসচেতনতা",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

def run_import():
    print("======================================================================")
    print("IMPORTING QUESTIONS FOR: নয়া পত্তন (জহির রায়হান) (CLASS 8, BANGLA 1ST)")
    print("======================================================================")

    with app.app_context():
        # 1. Resolve Class & Subject
        class_obj = ClassLevel.query.filter(ClassLevel.name.like('%৮ম%')).first()
        if not class_obj:
            print("ERROR: Class '৮ম শ্রেণি' not found!")
            return

        subject_obj = Subject.query.filter(Subject.class_id == class_obj.id, Subject.name.like('%বাংলা ১ম%')).first()
        if not subject_obj:
            print("ERROR: Subject 'বাংলা ১ম পত্র' not found in Class 8!")
            return

        ch_obj = Chapter.query.filter_by(id=652, subject_id=subject_obj.id).first()
        if not ch_obj:
            ch_obj = Chapter.query.filter(
                Chapter.subject_id == subject_obj.id,
                Chapter.title.like('%নয়া পত্তন%')
            ).first()

        if not ch_obj:
            print("ERROR: Chapter 'নয়া পত্তন' not found!")
            return

        print(f"Target Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"Target Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"Target Chapter: ID {ch_obj.id} - '{ch_obj.chapter_no}: {ch_obj.title}'\n")

        # 2. Setup Topics
        existing_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=ch_obj.id).all()}
        for idx, t_title in enumerate(TOPICS_NOYA_POTTON, 1):
            if t_title not in existing_topics:
                new_topic = Topic(chapter_id=ch_obj.id, title=t_title, order_num=idx)
                db.session.add(new_topic)
                print(f"  + Added Topic {idx}: {t_title}")
            else:
                existing_topics[t_title].order_num = idx
        db.session.commit()

        # Find descriptive topic (Topic 6)
        desc_topic = Topic.query.filter(
            Topic.chapter_id == ch_obj.id,
            Topic.title.like('%বর্ণনামূলক%') | Topic.title.like('%সৃজনশীল%')
        ).first()

        # Clean previous questions in this chapter if any
        del_count = Question.query.filter_by(chapter_id=ch_obj.id).delete()
        if del_count > 0:
            print(f"  Cleared {del_count} previous questions from chapter {ch_obj.id}.")

        # 3. Insert 10 questions
        for item in noya_potton_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=ch_obj.id,
                topic_id=desc_topic.id if desc_topic else None,
                question_type='descriptive',
                difficulty='medium',
                marks=10.0,
                cq_stem=None,
                cq_sub_ka=item['ka'].strip(),
                cq_sub_kha=item['kha'].strip(),
                cq_sub_ga=None,
                cq_sub_gha=None,
                cq_solution=item['solution'].strip()
            )
            db.session.add(q)
            print(f"  + Q{item['sl']:02d} -> ক: {item['ka'][:30]}... | খ: {item['kha'][:35]}...")

        db.session.commit()
        count = Question.query.filter_by(chapter_id=ch_obj.id).count()
        print(f"\nSuccessfully saved {count} questions for '{ch_obj.title}'.")

        # 4. Assertions & Verification
        assert count == 10, f"Expected 10 questions, found {count}"

        q10 = Question.query.filter_by(chapter_id=ch_obj.id).order_by(Question.id).all()[-1]
        print(f"\nChecking Q10 (ID: {q10.id}):")
        print(f"  ক: {q10.cq_sub_ka}")
        print(f"  খ: {q10.cq_sub_kha}")
        assert "আদমজী ক্যান্টনমেন্ট পাবলিক স্কুল" in q10.cq_sub_kha
        assert "জামালপুর জিলা স্কুল" in q10.cq_sub_kha
        assert "ভিকারুননিসা নূন স্কুল এন্ড কলেজ" in q10.cq_sub_kha

        print("\n✓ ALL ASSERTIONS AND SCHOOL TAG VERIFICATIONS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    run_import()
