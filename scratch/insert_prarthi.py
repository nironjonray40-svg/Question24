# -*- coding: utf-8 -*-
"""
Database insertion script for কবিতা ১২ - প্রার্থী (Chapter ID: 660)
"""
import sys
import os
from datetime import datetime

# Adjust path to import models and app
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')

from app import app, db
from models import Question, Chapter
from scratch.data_prarthi_mcq_p1 import MCQS_PRARTHI_P1
from scratch.data_prarthi_mcq_p2 import MCQS_PRARTHI_P2
from scratch.data_prarthi_sq_cq import SHORT_QUESTIONS, CREATIVE_QUESTIONS

CLASS_ID = 3       # ৮ম শ্রেণি
SUBJECT_ID = 47    # বাংলা ১ম পত্র
CHAPTER_ID = 660   # কবিতা ১২ - প্রার্থী (সুকান্ত ভট্টাচার্য)

def insert_prarthi_questions():
    with app.app_context():
        chapter = db.session.get(Chapter, CHAPTER_ID)
        if not chapter:
            print(f"Error: Chapter ID {CHAPTER_ID} not found!")
            return

        print(f"Target Chapter: {chapter.chapter_no} - {chapter.title} (ID: {chapter.id})")
        
        # 1. Insert MCQs
        all_mcqs = MCQS_PRARTHI_P1 + MCQS_PRARTHI_P2
        print(f"Inserting {len(all_mcqs)} MCQs...")
        for mcq in all_mcqs:
            q = Question(
                class_id=CLASS_ID,
                subject_id=SUBJECT_ID,
                chapter_id=CHAPTER_ID,
                topic_id=None,
                question_type='mcq',
                difficulty='medium',
                marks=1.0,
                mcq_stem=mcq['mcq_stem'],
                option_a=mcq['option_a'],
                option_b=mcq['option_b'],
                option_c=mcq['option_c'],
                option_d=mcq['option_d'],
                correct_option=mcq['correct_option'],
                explanation=mcq['explanation'],
                created_at=datetime.utcnow()
            )
            db.session.add(q)
            
        # 2. Insert Short Questions
        print(f"Inserting {len(SHORT_QUESTIONS)} Short Questions...")
        for sq in SHORT_QUESTIONS:
            q = Question(
                class_id=CLASS_ID,
                subject_id=SUBJECT_ID,
                chapter_id=CHAPTER_ID,
                topic_id=None,
                question_type='short',
                difficulty='medium',
                marks=2.0,
                short_question=sq['short_question'],
                short_answer=sq['short_answer'],
                created_at=datetime.utcnow()
            )
            db.session.add(q)

        # 3. Insert Creative Questions (CQ)
        print(f"Inserting {len(CREATIVE_QUESTIONS)} Creative Questions...")
        for cq in CREATIVE_QUESTIONS:
            q = Question(
                class_id=CLASS_ID,
                subject_id=SUBJECT_ID,
                chapter_id=CHAPTER_ID,
                topic_id=None,
                question_type='cq',
                difficulty='medium',
                marks=10.0,
                cq_stem=cq['cq_stem'],
                cq_sub_ka=cq['cq_sub_ka'],
                cq_sub_kha=cq['cq_sub_kha'],
                cq_sub_ga=cq['cq_sub_ga'],
                cq_sub_gha=cq['cq_sub_gha'],
                cq_solution=cq['cq_solution'],
                created_at=datetime.utcnow()
            )
            db.session.add(q)

        db.session.commit()
        print("Successfully committed all questions for কবিতা ১২ - প্রার্থী!")

        # Verify counts in DB
        mcq_count = Question.query.filter_by(chapter_id=CHAPTER_ID, question_type='mcq').count()
        sq_count = Question.query.filter_by(chapter_id=CHAPTER_ID, question_type='short').count()
        cq_count = Question.query.filter_by(chapter_id=CHAPTER_ID, question_type='cq').count()
        print(f"Verification -> MCQs: {mcq_count}, Short: {sq_count}, CQ: {cq_count}, Total: {mcq_count + sq_count + cq_count}")

if __name__ == '__main__':
    insert_prarthi_questions()
