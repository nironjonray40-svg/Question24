# -*- coding: utf-8 -*-
"""
Ingestion script for:
Class: ৮ম শ্রেণি (ClassLevel ID: 3)
Subject: বাংলা ১ম পত্র (Subject ID: 47)

Chapters:
1. আনন্দপাঠ - নাটক : মানসিংহ ও ঈশা খাঁ (ইব্রাহীম খাঁ) (Chapter ID: 658)
   - 10 Descriptive Questions (1-10)
   - Includes school tags (e.g., [গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা], [ক্রিয়েটিভ মডেল স্কুল])

2. আনন্দপাঠ - তিরন্দাজ (যোগীন্দ্রনাথ সরকার) (Chapter ID: 657)
   - 9 Descriptive Questions (11-19)
   - Includes school tags (e.g., [গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা], [ক্রিয়েটিভ মডেল স্কুল])

Total: 19 Questions (19 x 10 = 190 marks)
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic
from mansingho_esha_kha_questions import mansingho_questions
from tirondaj_questions import tirondaj_questions

TOPICS_MANSINGHO = [
    "পাঠ ১: 'মানসিংহ ও ঈশা খাঁ' নাটকের প্রেক্ষাপট, ঐতিহাসিক পটভূমি ও মূল বিষয়বস্তু",
    "পাঠ ২: পাঠান সর্দার ঈশা খাঁ ও রাজপুত বীর মানসিংহের দ্বন্দ্ব ও বীরত্বগাথা",
    "পাঠ ৩: ঈশা খাঁর মহানুভবতা, ঔদার্য ও মানসিংহের হৃদয় পরিবর্তন",
    "পাঠ ৪: মোগল-পাঠান মৈত্রী, হিন্দু-মুসলমান সম্প্রীতি ও দেশপ্রেমের বার্তা",
    "পাঠ ৫: নাট্যকার ইব্রাহীম খাঁ'র সাহিত্যকর্ম ও নাটকের গঠনরীতি বিশ্লেষণ",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

TOPICS_TIRONDAJ = [
    "পাঠ ১: 'তিরন্দাজ' গল্পের উৎস (মহাভারতের আদিপর্ব) ও মূল বিষয়বস্তু",
    "পাঠ ২: কৌরব ও পাণ্ডবদের পারস্পরিক সম্পর্ক, বৈরিতা ও অস্ত্রশিক্ষা",
    "পাঠ ৩: অর্জুনের একাগ্রতা, অধ্যবসায়, লক্ষ্যভেদ ও অনন্য ধনুর্বিদ্যা",
    "পাঠ ৪: আচার্য দ্রোণাচার্যের পরীক্ষা, ব্রহ্মশিরা অস্ত্রদান ও অর্জুনের সাফল্য",
    "পাঠ ৫: কর্মনিষ্ঠা, চর্চা, একাগ্রতা ও গুরুভক্তির তাৎপর্য বিশ্লেষণ",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

def run_import():
    print("======================================================================")
    print("IMPORTING QUESTIONS FROM PDF: MAN-SINGHO O ESHA KHA & TIRONDAJ")
    print("======================================================================")
    print(f"Loaded 'মানসিংহ ও ঈশা খাঁ' questions: {len(mansingho_questions)} (১ নং থেকে ১০ নং)")
    print(f"Loaded 'তিরন্দাজ' questions: {len(tirondaj_questions)} (১১ নং থেকে ১৯ নং)")
    print(f"Total questions to import: {len(mansingho_questions) + len(tirondaj_questions)}")

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

        ch_mansingho = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%মানসিংহ%')).first()
        ch_tirondaj = Chapter.query.filter(Chapter.subject_id == subject_obj.id, Chapter.title.like('%তিরন্দাজ%')).first()

        if not ch_mansingho:
            print("ERROR: Chapter 'মানসিংহ ও ঈশা খাঁ' not found!")
            return
        if not ch_tirondaj:
            print("ERROR: Chapter 'তিরন্দাজ' not found!")
            return

        print(f"\nTarget Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"Target Subject: ID {subject_obj.id} - '{subject_obj.name}'")
        print(f"Chapter 1     : ID {ch_mansingho.id} - '{ch_mansingho.chapter_no}: {ch_mansingho.title}'")
        print(f"Chapter 2     : ID {ch_tirondaj.id} - '{ch_tirondaj.chapter_no}: {ch_tirondaj.title}'")

        # ---------------------------------------------------------
        # A. Setup Topics and Import for 'মানসিংহ ও ঈশা খাঁ' (Ch 658)
        # ---------------------------------------------------------
        print("\n--- Processing 'নাটক : মানসিংহ ও ঈশা খাঁ (ইব্রাহীম খাঁ)' ---")
        existing_m_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=ch_mansingho.id).all()}
        for idx, t_title in enumerate(TOPICS_MANSINGHO, 1):
            if t_title not in existing_m_topics:
                new_topic = Topic(chapter_id=ch_mansingho.id, title=t_title, order_num=idx)
                db.session.add(new_topic)
                print(f"  + Added Topic: {t_title}")
            else:
                existing_m_topics[t_title].order_num = idx
        db.session.commit()

        # Find topic for descriptive questions (Topic 6)
        m_desc_topic = Topic.query.filter(
            Topic.chapter_id == ch_mansingho.id,
            Topic.title.like('%বর্ণনামূলক%') | Topic.title.like('%সৃজনশীল%')
        ).first()

        # Clean existing questions in Ch 658
        del_m = Question.query.filter_by(chapter_id=ch_mansingho.id).delete()
        if del_m > 0:
            print(f"  Cleared {del_m} previous questions from chapter {ch_mansingho.id}.")

        # Insert 1-10 questions
        for item in mansingho_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=ch_mansingho.id,
                topic_id=m_desc_topic.id if m_desc_topic else None,
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
            print(f"  + Q{item['sl']:02d} Prepared -> ক: {item['ka'][:35]}... | খ: {item['kha'][:35]}...")

        # ---------------------------------------------------------
        # B. Setup Topics and Import for 'তিরন্দাজ' (Ch 657)
        # ---------------------------------------------------------
        print("\n--- Processing 'তিরন্দাজ (যোগীন্দ্রনাথ সরকার)' ---")
        existing_t_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=ch_tirondaj.id).all()}
        for idx, t_title in enumerate(TOPICS_TIRONDAJ, 1):
            if t_title not in existing_t_topics:
                new_topic = Topic(chapter_id=ch_tirondaj.id, title=t_title, order_num=idx)
                db.session.add(new_topic)
                print(f"  + Added Topic: {t_title}")
            else:
                existing_t_topics[t_title].order_num = idx
        db.session.commit()

        # Find topic for descriptive questions (Topic 6)
        t_desc_topic = Topic.query.filter(
            Topic.chapter_id == ch_tirondaj.id,
            Topic.title.like('%বর্ণনামূলক%') | Topic.title.like('%সৃজনশীল%')
        ).first()

        # Clean existing questions in Ch 657
        del_t = Question.query.filter_by(chapter_id=ch_tirondaj.id).delete()
        if del_t > 0:
            print(f"  Cleared {del_t} previous questions from chapter {ch_tirondaj.id}.")

        # Insert 11-19 questions
        for item in tirondaj_questions:
            q = Question(
                class_id=class_obj.id,
                subject_id=subject_obj.id,
                chapter_id=ch_tirondaj.id,
                topic_id=t_desc_topic.id if t_desc_topic else None,
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
            print(f"  + Q{item['sl']:02d} Prepared -> ক: {item['ka'][:35]}... | খ: {item['kha'][:35]}...")

        # Commit all to DB
        db.session.commit()
        print("\n======================================================================")
        print("DATABASE COMMIT SUCCESSFUL!")
        print("======================================================================")

        # ---------------------------------------------------------
        # Verification & Assertions
        # ---------------------------------------------------------
        m_count = Question.query.filter_by(chapter_id=ch_mansingho.id).count()
        t_count = Question.query.filter_by(chapter_id=ch_tirondaj.id).count()

        print(f"Verification Results:")
        print(f"  'মানসিংহ ও ঈশা খাঁ' Total Questions: {m_count} (Expected: 10)")
        print(f"  'তিরন্দাজ' Total Questions          : {t_count} (Expected: 9)")
        print(f"  Total Ingested                     : {m_count + t_count} (Expected: 19)")

        assert m_count == 10, f"Expected 10 questions in Mansingho, got {m_count}"
        assert t_count == 9, f"Expected 9 questions in Tirondaj, got {t_count}"

        # Check Question 10 school tag
        q10 = Question.query.filter_by(chapter_id=ch_mansingho.id).order_by(Question.id).all()[-1]
        print(f"\nChecking Q10 (ID: {q10.id}):")
        print(f"  ক: {q10.cq_sub_ka}")
        print(f"  খ: {q10.cq_sub_kha}")
        assert "গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা" in q10.cq_sub_kha

        # Check Question 19 school tag
        q19 = Question.query.filter_by(chapter_id=ch_tirondaj.id).order_by(Question.id).all()[-1]
        print(f"\nChecking Q19 (ID: {q19.id}):")
        print(f"  ক: {q19.cq_sub_ka}")
        print(f"  খ: {q19.cq_sub_kha}")
        assert "গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা" in q19.cq_sub_kha

        print("\n✓ ALL ASSERTIONS AND VERIFICATIONS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    run_import()
