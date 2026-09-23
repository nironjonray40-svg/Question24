# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=== VERIFICATION FOR CHAPTER 636 (লাইব্রেরি) ===")

# Total counts
total = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 636").fetchone()[0]
mcqs = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 636 AND question_type = 'mcq'").fetchone()[0]
shorts = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 636 AND question_type = 'short'").fetchone()[0]
cqs = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 636 AND question_type = 'cq'").fetchone()[0]

print(f"Total Questions : {total}")
print(f"MCQs            : {mcqs}")
print(f"Shorts          : {shorts}")
print(f"CQs             : {cqs}")

assert total == 172
assert mcqs == 139
assert shorts == 13
assert cqs == 20

# Check MCQ options and answers
opt_counts = c.execute("SELECT correct_option, count(*) FROM questions WHERE chapter_id = 636 AND question_type = 'mcq' GROUP BY correct_option").fetchall()
print("\nMCQ Correct Option distribution:", opt_counts)

# Check MCQs with stimuli
stim_mcqs = c.execute("""
    SELECT id, mcq_stem 
    FROM questions 
    WHERE chapter_id = 636 AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপক%'
""").fetchall()

print(f"\nTotal Stimulus-based MCQs found: {len(stim_mcqs)}")
for idx, (qid, stem) in enumerate(stim_mcqs, 1):
    first_lines = stem.splitlines()[:4]
    print(f"  {idx}. [ID {qid}] {' / '.join(first_lines)}")

# Expected stimulus questions:
# 1, 2 (stimulus 1)
# 68, 69 (stimulus 2)
# 70, 71 (stimulus 3)
# 72, 73 (stimulus 4)
# 87, 88 (stimulus 5)
# 131, 132 (stimulus 6)
# 136, 137 (stimulus 7)
# 138, 139 (stimulus 8)
# Total = 2 * 8 = 16 stimulus MCQs
print(f"Expected 16 stimulus MCQs, got: {len(stim_mcqs)}")
assert len(stim_mcqs) == 16, f"Expected 16 stimulus MCQs, found {len(stim_mcqs)}"

# Check that every stimulus MCQ has both the stimulus intro and the question
for qid, stem in stim_mcqs:
    assert "উদ্দীপকটি পড়ে নিচের প্রশ্নের উত্তর দাও:" in stem
    assert len(stem.split("\n\n")) >= 2

# Check Short Questions sample
print("\n--- Short Questions sample (First 2) ---")
for r in c.execute("SELECT short_question, short_answer FROM questions WHERE chapter_id = 636 AND question_type = 'short' LIMIT 2").fetchall():
    print("Q:", r[0])
    print("A:", r[1][:100], "...")
    print()

# Check CQ Questions sample
print("--- Creative Questions sample (First 2) ---")
for r in c.execute("SELECT cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha FROM questions WHERE chapter_id = 636 AND question_type = 'cq' LIMIT 2").fetchall():
    print("STEM:", r[0][:80], "...")
    print("ক:", r[1])
    print("খ:", r[2])
    print("গ:", r[3])
    print("ঘ:", r[4])
    print()

print("ALL VERIFICATIONS PASSED SUCCESSFULLY!")
