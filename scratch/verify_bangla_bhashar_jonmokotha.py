# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

def verify():
    print("=== VERIFYING 'বাংলা ভাষার জন্মকথা (হুমায়ুন আজাদ)' INGESTION ===")
    with app.app_context():
        chapter = Chapter.query.filter(Chapter.title.like('%বাংলা ভাষার জন্মকথা%')).first()
        if not chapter:
            print("ERROR: Chapter not found!")
            return

        print(f"Chapter ID: {chapter.id}, Title: {chapter.title}")
        
        # 1. Topics
        topics = Topic.query.filter_by(chapter_id=chapter.id).order_by(Topic.order_num).all()
        print(f"\n1. Topics in Chapter ({len(topics)} total):")
        for t in topics:
            q_cnt = Question.query.filter_by(topic_id=t.id).count()
            print(f"  - [{t.order_num}] ID {t.id}: {t.title} -> {q_cnt} questions")

        # 2. Question counts by type
        total_q = Question.query.filter_by(chapter_id=chapter.id).count()
        mcqs = Question.query.filter_by(chapter_id=chapter.id, question_type='mcq').all()
        shorts = Question.query.filter_by(chapter_id=chapter.id, question_type='short').all()
        cqs = Question.query.filter_by(chapter_id=chapter.id, question_type='cq').all()

        print(f"\n2. Question Counts:")
        print(f"  Total: {total_q} (Expected: 135)")
        print(f"  MCQ  : {len(mcqs)} (Expected: 112)")
        print(f"  Short: {len(shorts)} (Expected: 9)")
        print(f"  CQ   : {len(cqs)} (Expected: 14)")

        assert total_q == 135
        assert len(mcqs) == 112
        assert len(shorts) == 9
        assert len(cqs) == 14

        # 3. Verify Stimulus presence in MCQs
        print("\n3. Verifying Stimulus in MCQs:")
        stimulus_indices = [25, 26, 28, 29, 109, 110] # 0-indexed for questions 26, 27, 29, 30, 110, 111
        for idx in stimulus_indices:
            q = mcqs[idx]
            has_stimulus = "উদ্দীপকটি পড়ে" in q.mcq_stem
            print(f"  MCQ #{idx+1} has stimulus: {has_stimulus}")
            assert has_stimulus, f"MCQ #{idx+1} does not have stimulus!"

        # 4. Verify Board and School Tags
        print("\n4. Verifying Board/School Tags:")
        tagged_mcqs = [q for q in mcqs if "[" in q.mcq_stem and "]" in q.mcq_stem]
        print(f"  Tagged MCQs count: {len(tagged_mcqs)}")
        
        sample_tags = ["[ঢা. বো.'২০১৯]", "[ম. বো.'২০১৯]", "[বরিশাল জিলা স্কুল]", "[ভিকারুননিসা নূন স্কুল এন্ড কলেজ, ঢাকা]"]
        for tag in sample_tags:
            found = any(tag in q.mcq_stem for q in mcqs)
            print(f"  Found '{tag}' in MCQs: {found}")
            assert found, f"Tag '{tag}' not found in any MCQ!"

        cq_10 = cqs[9]
        print(f"  CQ 10 has tag '[রা. বো.]': {'[রা. বো.]' in cq_10.cq_stem}")
        assert '[রা. বো.]' in cq_10.cq_stem

        cq_14 = cqs[13]
        print(f"  CQ 14 has tag '[ময়মনসিংহ গার্লস ক্যাডেট কলেজ]': {'[ময়মনসিংহ গার্লস ক্যাডেট কলেজ]' in cq_14.cq_stem}")
        assert '[ময়মনসিংহ গার্লস ক্যাডেট কলেজ]' in cq_14.cq_stem

        # 5. Check Short questions completeness
        print("\n5. Verifying Short Questions:")
        for idx, sq in enumerate(shorts, 1):
            assert sq.short_question and len(sq.short_question.strip()) > 5
            assert sq.short_answer and len(sq.short_answer.strip()) > 10
        print(f"  All {len(shorts)} short questions have complete questions and answers.")

        # 6. Check CQs completeness
        print("\n6. Verifying Creative Questions:")
        for idx, cq in enumerate(cqs, 1):
            assert cq.cq_stem and len(cq.cq_stem.strip()) > 10
            assert cq.cq_sub_ka and len(cq.cq_sub_ka.strip()) > 2
            assert cq.cq_sub_kha and len(cq.cq_sub_kha.strip()) > 2
            assert cq.cq_sub_ga and len(cq.cq_sub_ga.strip()) > 2
            assert cq.cq_sub_gha and len(cq.cq_sub_gha.strip()) > 2
            assert cq.cq_solution and len(cq.cq_solution.strip()) > 20
        print(f"  All {len(cqs)} CQs have complete stems, sub-questions (ক, খ, গ, ঘ), and solutions.")

        print("\n✓ ALL VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    verify()
