# -*- coding: utf-8 -*-
"""
Ingestion script for 5 Anandapath chapters:
Class: ৮ম শ্রেণি (ClassLevel ID: 3)
Subject: বাংলা ১ম পত্র (Subject ID: 47)

Chapters:
1. আনন্দপাঠ : মুক্তি (অ্যালেক্স হ্যালি; অনুবাদ: গীতি সেন) (ID: 655) - 10 Questions
2. আনন্দপাঠ : হেমাপ্যাথি, এ্যালাপ্যাথি (হাসান আজিজুল হক) (ID: 653) - 12 Questions
3. আনন্দপাঠ : ফিলিস্তিনের চিঠি (ঘাসান কানাফানি; অনুবাদ: মানবেন্দ্র বন্দ্যোপাধ্যায়) (ID: 656) - 9 Questions
4. আনন্দপাঠ : কাকতাড়ুয়া (সত্যজিৎ রায়) (ID: 651) - 12 Questions
5. আনন্দপাঠ : ডেভিড কপারফিল্ড (চার্লস ডিকেন্স; রূপান্তর: আখতারুজ্জামান ইলিয়াস) (ID: 654) - 10 Questions

Total: 53 Questions
"""

import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

from mukti_questions import mukti_questions
from hemapathy_questions import hemapathy_questions
from filistiner_chithi_questions import filistiner_chithi_questions
from kaktadua_questions import kaktadua_questions
from david_copperfield_questions import david_copperfield_questions

TOPICS_MUKTI = [
    "পাঠ ১: 'মুক্তি' গল্পের প্রেক্ষাপট, আফ্রিকান দাসপ্রথা ও ঐতিহাসিক পটভূমি",
    "পাঠ ২: কুন্টার বন্দিদশা, নিলামে বিক্রয় ও দাসজীবনের অমানবিক নির্যাতন",
    "পাঠ ৩: জাতিগত ও বর্ণগত নিপীড়ন এবং কুন্টার আত্মমর্যাদাবোধ",
    "পাঠ ৪: বুদ্ধি, সাহস ও শক্তি দিয়ে বন্দিদশা থেকে কুন্টার মুক্তির সংগ্রাম",
    "পাঠ ৫: লেখক অ্যালেক্স হ্যালি ও মূল উপন্যাস 'রুটস' (Roots) সংক্রান্ত আলোচনা",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

TOPICS_HEMAPATHY = [
    "পাঠ ১: 'হেমাপ্যাথি, এ্যালাপ্যাথি' গল্পের গ্রামীণ প্রেক্ষাপট ও বিষয়বস্তু",
    "পাঠ ২: গ্রামের রোগবালাই (ম্যালেরিয়া, কলেরা) ও গ্রামীণ মানুষের চিকিৎসাব্যবস্থা",
    "পাঠ ৩: অঘোর ডাক্তার ও তোরাপ ডাক্তারের অপচিকিৎসা ও পারস্পরিক প্রতিদ্বন্দ্বিতা",
    "পাঠ ৪: ইদরিসের চিকিৎসায় সুচ ভেঙে যাওয়ার ঘটনা ও শিক্ষা ('যার কাজ তারেই সাজে')",
    "পাঠ ৫: কথাসাহিত্যিক হাসান আজিজুল হকের সাহিত্যকর্ম ও সমাজবাস্তবতা",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

TOPICS_FILISTIN = [
    "পাঠ ১: 'ফিলিস্তিনের চিঠি' গল্পের প্রেক্ষাপট, ঐতিহাসিক পটভূমি ও বিষয়বস্তু",
    "পাঠ ২: যুদ্ধবিধ্বস্ত ফিলিস্তিন, ইসরায়েলি বর্বরতা ও গাজার মানবিক বিপর্যয়",
    "পাঠ ৩: ভাতিজি নাদিয়ার আত্মত্যাগ, দুই পা হারানো ও দেশপ্রেমের চরম নিদর্শন",
    "পাঠ ৪: ক্যালিফোর্নিয়া যাত্রা বাতিল, স্বদেশের প্রতি দায়বদ্ধতা ও বন্ধু মুস্তাফাকে আহ্বান",
    "পাঠ ৫: লেখক ঘাসান কানাফানি ও অনুবাদক মানবেন্দ্র বন্দ্যোপাধ্যায়ের সাহিত্যকর্ম",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

TOPICS_KAKTADUA = [
    "পাঠ ১: 'কাকতাড়ুয়া' গল্পের পটভূমি, চরিত্র ও মূল বিষয়বস্তু",
    "পাঠ ২: পানাগড়ের পথে গাড়ি বিকল ও জনমানবহীন পরিবেশের বর্ণনা",
    "পাঠ ৩: কুসংস্কারের অন্ধকার, ওঝার চালপড়া ও বিশ্বস্ত চাকর অভিরামের পরিণতি",
    "পাঠ ৪: মৃগাঙ্কবাবুর অবচেতন মনের ভাবনা, কাকতাড়ুয়ারূপে অভিরামের আবির্ভাব ও সত্য উন্মোচন",
    "পাঠ ৫: লেখক ও চলচ্চিত্রকার সত্যজিৎ রায়ের জীবন ও সাহিত্যকর্ম",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

TOPICS_DAVID = [
    "পাঠ ১: 'ডেভিড কপারফিল্ড' উপন্যাসের ভাবানুবাদ ও মূল বিষয়বস্তু",
    "পাঠ ২: শৈশবের সুখ, মায়ের দ্বিতীয় বিয়ে ও সৎপিতা মার্ডস্টোনের নির্মম নির্যাতন",
    "পাঠ ৩: লন্ডনের জনাকীর্ণ শহরে নির্বাসন ও সালেম হাউসে নিঃসঙ্গ ডেভিড",
    "পাঠ ৪: শিক্ষক মেল সাহেবের দারিদ্র্য, স্টিরফোর্ড ও ক্রিকল সাহেবের অপমানজনক আচরণ",
    "পাঠ ৫: ডেভিডের ধৈর্য, মনোবল, সংগ্রামশীলতা ও জীবনের প্রতিকূলতা জয়",
    "পাঠ ৬: বর্ণনামূলক ও সৃজনশীল প্রশ্নোত্তর অনুশীলন",
    "পাঠ ৭: সংক্ষিপ্ত ও বহুনির্বাচনি মূল্যায়ন"
]

CHAPTER_CONFIGS = [
    {
        "ch_id": 655,
        "title_keyword": "মুক্তি",
        "name": "মুক্তি (অ্যালেক্স হ্যালি; অনুবাদ: গীতি সেন)",
        "topics": TOPICS_MUKTI,
        "questions": mukti_questions,
        "expected_count": 10
    },
    {
        "ch_id": 653,
        "title_keyword": "হেমাপ্যাথি",
        "name": "হেমাপ্যাথি, এ্যালাপ্যাথি (হাসান আজিজুল হক)",
        "topics": TOPICS_HEMAPATHY,
        "questions": hemapathy_questions,
        "expected_count": 12
    },
    {
        "ch_id": 656,
        "title_keyword": "ফিলিস্তিনের চিঠি",
        "name": "ফিলিস্তিনের চিঠি (ঘাসান কানাফানি; অনুবাদ: মানবেন্দ্র বন্দ্যোপাধ্যায়)",
        "topics": TOPICS_FILISTIN,
        "questions": filistiner_chithi_questions,
        "expected_count": 9
    },
    {
        "ch_id": 651,
        "title_keyword": "কাকতাড়ুয়া",
        "name": "কাকতাড়ুয়া (সত্যজিৎ রায়)",
        "topics": TOPICS_KAKTADUA,
        "questions": kaktadua_questions,
        "expected_count": 12
    },
    {
        "ch_id": 654,
        "title_keyword": "ডেভিড কপারফিল্ড",
        "name": "ডেভিড কপারফিল্ড (চার্লস ডিকেন্স; রূপান্তর: আখতারুজ্জামান ইলিয়াস)",
        "topics": TOPICS_DAVID,
        "questions": david_copperfield_questions,
        "expected_count": 10
    }
]

def run_import():
    print("======================================================================")
    print("IMPORTING QUESTIONS FOR 5 ANANDAPATH CHAPTERS (CLASS 8, BANGLA 1ST)")
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

        print(f"Target Class  : ID {class_obj.id} - '{class_obj.name}'")
        print(f"Target Subject: ID {subject_obj.id} - '{subject_obj.name}'\n")

        total_imported = 0

        for config in CHAPTER_CONFIGS:
            ch_id = config["ch_id"]
            ch_obj = Chapter.query.filter_by(id=ch_id, subject_id=subject_obj.id).first()
            if not ch_obj:
                ch_obj = Chapter.query.filter(
                    Chapter.subject_id == subject_obj.id,
                    Chapter.title.like(f"%{config['title_keyword']}%")
                ).first()

            if not ch_obj:
                print(f"ERROR: Chapter '{config['name']}' not found!")
                continue

            print(f"--- Processing Chapter ID {ch_obj.id}: '{ch_obj.title}' ---")

            # Setup Topics
            existing_topics = {t.title: t for t in Topic.query.filter_by(chapter_id=ch_obj.id).all()}
            for idx, t_title in enumerate(config["topics"], 1):
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

            # Clean previous questions in this chapter
            del_count = Question.query.filter_by(chapter_id=ch_obj.id).delete()
            if del_count > 0:
                print(f"  Cleared {del_count} previous questions from chapter {ch_obj.id}.")

            # Insert questions
            q_list = config["questions"]
            for item in q_list:
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
            print(f"  Successfully saved {count} questions for '{ch_obj.title}'.\n")
            total_imported += count

        print("======================================================================")
        print(f"DATABASE COMMIT SUCCESSFUL! TOTAL IMPORTED: {total_imported}")
        print("======================================================================")

        # ---------------------------------------------------------
        # Verification & Assertions
        # ---------------------------------------------------------
        print("\nVerifying Questions & School Tags:")
        for config in CHAPTER_CONFIGS:
            ch_id = config["ch_id"]
            count = Question.query.filter_by(chapter_id=ch_id).count()
            expected = config["expected_count"]
            print(f"  Chapter ID {ch_id}: {count} questions (Expected: {expected})")
            assert count == expected, f"Expected {expected} in Chapter {ch_id}, found {count}"

        # Specific school tag checks:
        # 1. ফিলিস্তিনের চিঠি Q09: [গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা]
        q_filistin_9 = Question.query.filter_by(chapter_id=656).order_by(Question.id).all()[-1]
        print(f"\nChecking ফিলিস্তিনের চিঠি Q09 (ID: {q_filistin_9.id}):")
        print(f"  খ: {q_filistin_9.cq_sub_kha}")
        assert "গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা" in q_filistin_9.cq_sub_kha

        # 2. কাকতাড়ুয়া Q12: [বিন্দুবাসিনী সরকারি বালক উচ্চ বিদ্যালয়, টাঙ্গাইল, ভিকারুননিসা নূন স্কুল এন্ড কলেজ, ঢাকা]
        q_kaktadua_12 = Question.query.filter_by(chapter_id=651).order_by(Question.id).all()[-1]
        print(f"\nChecking কাকতাড়ুয়া Q12 (ID: {q_kaktadua_12.id}):")
        print(f"  খ: {q_kaktadua_12.cq_sub_kha}")
        assert "বিন্দুবাসিনী সরকারি বালক উচ্চ বিদ্যালয়" in q_kaktadua_12.cq_sub_kha
        assert "ভিকারুননিসা নূন স্কুল এন্ড কলেজ" in q_kaktadua_12.cq_sub_kha

        # 3. ডেভিড কপারফিল্ড Q10: [আদমজী ক্যান্টনমেন্ট পাবলিক স্কুল, ঢাকা, রাজউক উত্তরা মডেল কলেজ, ঢাকা]
        q_david_10 = Question.query.filter_by(chapter_id=654).order_by(Question.id).all()[-1]
        print(f"\nChecking ডেভিড কপারফিল্ড Q10 (ID: {q_david_10.id}):")
        print(f"  খ: {q_david_10.cq_sub_kha}")
        assert "আদমজী ক্যান্টনমেন্ট পাবলিক স্কুল" in q_david_10.cq_sub_kha
        assert "রাজউক উত্তরা মডেল কলেজ" in q_david_10.cq_sub_kha

        print("\n✓ ALL ASSERTIONS AND SCHOOL TAG VERIFICATIONS COMPLETED SUCCESSFULLY!")

if __name__ == '__main__':
    run_import()
