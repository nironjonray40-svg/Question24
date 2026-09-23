# -*- coding: utf-8 -*-
"""
Comprehensive Verification Script for Chapter 637: সুখী মানুষ (মমতাজউদদীন আহমদ)
"""
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("==============================================================")
print("VERIFICATION REPORT FOR CHAPTER 637 (সুখী মানুষ - মমতাজউদদীন আহমদ)")
print("==============================================================")

# 1. Total counts
total = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 637").fetchone()[0]
mcqs = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 637 AND question_type = 'mcq'").fetchone()[0]
shorts = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 637 AND question_type = 'short'").fetchone()[0]
cqs = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 637 AND question_type = 'cq'").fetchone()[0]

print(f"Total Questions : {total} (Expected: 196)")
print(f"MCQs            : {mcqs} (Expected: 158)")
print(f"Shorts          : {shorts} (Expected: 17)")
print(f"CQs             : {cqs} (Expected: 21)")

assert total == 196, f"Expected 196 total questions, found {total}"
assert mcqs == 158, f"Expected 158 MCQs, found {mcqs}"
assert shorts == 17, f"Expected 17 short questions, found {shorts}"
assert cqs == 21, f"Expected 21 CQs, found {cqs}"

# 2. Topic verification
topics = c.execute("SELECT id, order_num, title FROM topics WHERE chapter_id = 637 ORDER BY order_num").fetchall()
print(f"\nTopics created: {len(topics)} (Expected: 7)")
for tid, onum, title in topics:
    q_count = c.execute("SELECT count(*) FROM questions WHERE topic_id = ?", (tid,)).fetchone()[0]
    print(f"  {onum}. [ID {tid}] {title} -> {q_count} questions")
assert len(topics) == 7

# 3. MCQ Option Distribution
opt_counts = c.execute("SELECT correct_option, count(*) FROM questions WHERE chapter_id = 637 AND question_type = 'mcq' GROUP BY correct_option").fetchall()
print("\nMCQ Correct Option Distribution:")
for opt, cnt in opt_counts:
    print(f"  Option '{opt}': {cnt}")

# 4. Check Stimulus-based MCQs
stim_mcqs = c.execute("""
    SELECT id, mcq_stem 
    FROM questions 
    WHERE chapter_id = 637 AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপক%'
""").fetchall()

print(f"\nStimulus-based MCQs found: {len(stim_mcqs)} (Expected >= 20)")
for idx, (qid, stem) in enumerate(stim_mcqs, 1):
    first_lines = stem.splitlines()[:3]
    print(f"  {idx:2d}. [ID {qid}] {' / '.join(first_lines)[:90]}...")

assert len(stim_mcqs) >= 20

# Verify multi-question stimulus format
multi_stim_mcqs = c.execute("""
    SELECT id, mcq_stem 
    FROM questions 
    WHERE chapter_id = 637 AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপকটি পড়ে নিচের প্রশ্নের উত্তর দাও:%'
""").fetchall()
print(f"\nMulti-question stimulus MCQs with standard prefix: {len(multi_stim_mcqs)} (Expected: 20)")
assert len(multi_stim_mcqs) == 20

# 5. Check Board and School/College Tags
tagged_all = c.execute("""
    SELECT id, question_type, 
           CASE 
               WHEN question_type = 'mcq' THEN mcq_stem 
               WHEN question_type = 'short' THEN short_question
               WHEN question_type = 'cq' THEN cq_stem
           END as content
    FROM questions 
    WHERE chapter_id = 637 AND (
        (question_type = 'mcq' AND mcq_stem LIKE '%[%]%') OR
        (question_type = 'short' AND short_question LIKE '%[%]%') OR
        (question_type = 'cq' AND cq_stem LIKE '%[%]%')
    )
""").fetchall()

print(f"\nTotal Tagged Questions (Board / School / College): {len(tagged_all)}")
tag_by_type = {}
for qid, qtype, content in tagged_all:
    tag_by_type[qtype] = tag_by_type.get(qtype, 0) + 1

print(f"  Tagged MCQs   : {tag_by_type.get('mcq', 0)}")
print(f"  Tagged Shorts : {tag_by_type.get('short', 0)}")
print(f"  Tagged CQs    : {tag_by_type.get('cq', 0)}")

# Sample tags
print("\nSample Tagged Questions:")
for qid, qtype, content in tagged_all[:6]:
    last_line = content.splitlines()[-1]
    print(f"  [{qtype.upper()}] {last_line}")

# 6. Sample Short Questions
print("\n--- Sample Short Questions (First 2) ---")
for r in c.execute("SELECT id, short_question, short_answer FROM questions WHERE chapter_id = 637 AND question_type = 'short' LIMIT 2").fetchall():
    print(f"ID {r[0]} | Q: {r[1]}")
    print(f"Answer: {r[2][:100]}...\n")

# 7. Sample Creative Questions (CQ)
print("--- Sample Creative Questions (CQ 1 & CQ 11) ---")
for r in c.execute("SELECT id, cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha FROM questions WHERE chapter_id = 637 AND question_type = 'cq' LIMIT 2").fetchall():
    print(f"ID {r[0]} | Stem: {r[1][:80]}...")
    print(f"  (ক): {r[2]}")
    print(f"  (খ): {r[3]}")
    print(f"  (গ): {r[4]}")
    print(f"  (ঘ): {r[5]}\n")

# 8. Check that no question has leading artificial number like '০১।' or '১।'
leading_num_qs = c.execute("""
    SELECT count(*) FROM questions 
    WHERE chapter_id = 637 AND (
        (question_type = 'mcq' AND (mcq_stem LIKE '১.%' OR mcq_stem LIKE '০১.%' OR mcq_stem LIKE '১।%' OR mcq_stem LIKE '০১।%')) OR
        (question_type = 'short' AND (short_question LIKE '১.%' OR short_question LIKE '০১.%' OR short_question LIKE '১।%' OR short_question LIKE '০১।%')) OR
        (question_type = 'cq' AND (cq_stem LIKE '১.%' OR cq_stem LIKE '০১.%' OR cq_stem LIKE '১।%' OR cq_stem LIKE '০১।%'))
    )
""").fetchone()[0]
print(f"Questions with artificial leading numbering: {leading_num_qs} (Expected: 0)")
assert leading_num_qs == 0

print("==============================================================")
print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY WITHOUT ANY ERRORS!")
print("==============================================================")
