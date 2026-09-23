# -*- coding: utf-8 -*-
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, Chapter, Subject, ClassLevel, Topic

def verify():
    print("=== RUNNING VERIFICATION FOR 'গণঅভ্যুত্থানের কথা (সংকলিত)' ===")
    with app.app_context():
        chapter = Chapter.query.filter(Chapter.title.like('%গণঅভ্যুত্থানের কথা%')).first()
        if not chapter:
            print("ERROR: Chapter not found!")
            return

        print(f"Chapter ID: {chapter.id}, Name: {chapter.chapter_no}: {chapter.title}")

        # 1. Total counts
        all_q = Question.query.filter_by(chapter_id=chapter.id).order_by(Question.id).all()
        mcqs = [q for q in all_q if q.question_type == 'mcq']
        shorts = [q for q in all_q if q.question_type == 'short']
        cqs = [q for q in all_q if q.question_type == 'cq']

        print(f"Total Questions : {len(all_q)}")
        print(f"MCQs            : {len(mcqs)}")
        print(f"Short Questions : {len(shorts)}")
        print(f"CQs             : {len(cqs)}")

        assert len(all_q) == 180, f"Expected 180 total, got {len(all_q)}"
        assert len(mcqs) == 152, f"Expected 152 MCQs, got {len(mcqs)}"
        assert len(shorts) == 9, f"Expected 9 Short questions, got {len(shorts)}"
        assert len(cqs) == 19, f"Expected 19 CQs, got {len(cqs)}"
        print("✓ Question count check passed!")

        # 2. Check MCQs validity
        for idx, q in enumerate(mcqs, 1):
            assert q.mcq_stem, f"MCQ {idx} missing stem"
            assert q.option_a, f"MCQ {idx} missing option_a"
            assert q.option_b, f"MCQ {idx} missing option_b"
            assert q.option_c, f"MCQ {idx} missing option_c"
            assert q.option_d, f"MCQ {idx} missing option_d"
            assert q.correct_option in ['ক', 'খ', 'গ', 'ঘ'], f"MCQ {idx} invalid correct_option: {q.correct_option}"
        print("✓ All 152 MCQs have valid stem, options, and correct_option!")

        # 3. Check Stimulus MCQs
        stimulus_mcqs = [q for q in mcqs if "উদ্দীপকটি পড়ে নিচের প্রশ্নের উত্তর দাও:" in q.mcq_stem]
        print(f"Found {len(stimulus_mcqs)} stimulus MCQs.")
        assert len(stimulus_mcqs) == 8, f"Expected 8 stimulus MCQs (85, 86, 146, 147, 148, 149, 150, 151), got {len(stimulus_mcqs)}"
        
        # Verify specific stimulus contents
        assert "একজন আদর্শ শাসকের প্রয়োজনীয়তা অপরিসীম" in mcqs[84].mcq_stem  # Q85
        assert "একজন আদর্শ শাসকের প্রয়োজনীয়তা অপরিসীম" in mcqs[85].mcq_stem  # Q86
        assert "১৯৭১ সালে বাংলাদেশ স্বাধীন হয়" in mcqs[145].mcq_stem  # Q146
        assert "১৯৭১ সালে বাংলাদেশ স্বাধীন হয়" in mcqs[146].mcq_stem  # Q147
        assert "রাজপথে ফের রক্ত লাগুক" in mcqs[147].mcq_stem  # Q148
        assert "রাজপথে ফের রক্ত লাগুক" in mcqs[148].mcq_stem  # Q149
        assert "ঢাকা বিশ্ববিদ্যালয় বাংলাদেশের আন্দোলন-সংগ্রামের সূতিকাগার" in mcqs[149].mcq_stem  # Q150
        assert "ঢাকা বিশ্ববিদ্যালয় বাংলাদেশের আন্দোলন-সংগ্রামের সূতিকাগার" in mcqs[150].mcq_stem  # Q151
        print("✓ All 8 stimulus MCQs correctly contain their individual stimulus!")

        # 4. Check School/College tags
        tagged_mcqs = [q for q in mcqs if "[" in q.mcq_stem and "]" in q.mcq_stem]
        print(f"Found {len(tagged_mcqs)} tagged MCQs:")
        for q in tagged_mcqs:
            tag = q.mcq_stem[q.mcq_stem.find('['):q.mcq_stem.find(']')+1]
            print(f"  ID {q.id}: {tag}")
        assert len(tagged_mcqs) == 3, f"Expected 3 tagged MCQs, got {len(tagged_mcqs)}"
        assert "[রাজউক উত্তরা মডেল কলেজ, ঢাকা]" in mcqs[118].mcq_stem  # Q119
        assert "[রাজশাহী কলেজ,রাজউক উত্তরা মডেল কলেজ, ঢাকা]" in mcqs[127].mcq_stem  # Q128
        assert "[গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা]" in mcqs[128].mcq_stem  # Q129
        print("✓ All tagged MCQs verified with correct school/college/board names!")

        # 5. Check Short questions
        for idx, q in enumerate(shorts, 1):
            assert q.short_question, f"Short Q {idx} missing question text"
            assert q.short_answer, f"Short Q {idx} missing answer"
        print("✓ All 9 Short Questions verified with question and answer!")

        # 6. Check CQs
        for idx, q in enumerate(cqs, 1):
            assert q.cq_stem, f"CQ {idx} missing stem"
            assert q.cq_sub_ka, f"CQ {idx} missing ka"
            assert q.cq_sub_kha, f"CQ {idx} missing kha"
            assert q.cq_sub_ga, f"CQ {idx} missing ga"
            assert q.cq_sub_gha, f"CQ {idx} missing gha"
            assert q.cq_solution, f"CQ {idx} missing solution"
        print("✓ All 19 Creative Questions verified with full sub-questions and solutions!")

        # 7. Check Topics
        topics = Topic.query.filter_by(chapter_id=chapter.id).order_by(Topic.order_num).all()
        print(f"\nTopics in chapter ({len(topics)}):")
        for t in topics:
            q_count = Question.query.filter_by(topic_id=t.id).count()
            print(f"  Topic ID {t.id} (Order {t.order_num}): '{t.title}' -> {q_count} questions")

        print("\n==========================================")
        print("✓✓✓ ALL VERIFICATION TESTS PASSED SUCCESSFULLY! ✓✓✓")
        print("==========================================")

if __name__ == '__main__':
    verify()
