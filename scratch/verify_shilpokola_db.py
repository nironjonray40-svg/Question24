# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=== VERIFYING CHAPTER 638 (শিল্পকলার নানা দিক) ===")

# 1. Total questions count
total = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 638").fetchone()[0]
mcq_cnt = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 638 AND question_type = 'mcq'").fetchone()[0]
short_cnt = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 638 AND question_type = 'short'").fetchone()[0]
cq_cnt = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 638 AND question_type = 'cq'").fetchone()[0]

print(f"Total Questions : {total} (Expected: 112)")
print(f"MCQ Questions   : {mcq_cnt} (Expected: 87)")
print(f"Short Questions : {short_cnt} (Expected: 10)")
print(f"CQ Questions    : {cq_cnt} (Expected: 15)")

assert total == 112
assert mcq_cnt == 87
assert short_cnt == 10
assert cq_cnt == 15

# 2. Verify Topics
topics = c.execute("SELECT id, title, order_num FROM topics WHERE chapter_id = 638 ORDER BY order_num").fetchall()
print(f"\nTopics ({len(topics)}):")
for tid, title, order_num in topics:
    cnt = c.execute("SELECT count(*) FROM questions WHERE topic_id = ?", (tid,)).fetchone()[0]
    print(f"  [{order_num}] Topic {tid}: {title} (Questions: {cnt})")

assert len(topics) == 7

# 3. Verify Stimulus in MCQs
stimulus_mcqs = c.execute("SELECT id, mcq_stem FROM questions WHERE chapter_id = 638 AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপকটি পড়ে%'").fetchall()
print(f"\nStimulus-based MCQs found: {len(stimulus_mcqs)} (Expected: 8)")
for qid, stem in stimulus_mcqs:
    first_line = stem.splitlines()[0]
    last_line = stem.splitlines()[-1]
    print(f"  ID {qid}: {first_line} ... {last_line}")
assert len(stimulus_mcqs) == 8

# 4. Verify Board and School Tags
tagged_qs = c.execute("""
    SELECT id, question_type, mcq_stem, short_question, cq_stem 
    FROM questions 
    WHERE chapter_id = 638 AND (mcq_stem LIKE '%[%]%' OR short_question LIKE '%[%]%' OR cq_stem LIKE '%[%]%')
    ORDER BY id
""").fetchall()

print(f"\nTotal Tagged Questions: {len(tagged_qs)}")
for qid, qtype, mcq, short, cq in tagged_qs:
    txt = mcq or short or cq
    tag = txt[txt.find('['):txt.find(']')+1] if '[' in txt else ''
    first_line = txt.splitlines()[0]
    print(f"  ID {qid} ({qtype.upper()}): {tag} -> {first_line[:60]}")

# 5. Check Samples
print("\n--- Sample MCQ ---")
sample_mcq = c.execute("SELECT id, mcq_stem, option_a, option_b, option_c, option_d, correct_option FROM questions WHERE chapter_id = 638 AND question_type = 'mcq' LIMIT 1").fetchone()
print(f"ID: {sample_mcq[0]}\nStem:\n{sample_mcq[1]}\n(ক) {sample_mcq[2]} (খ) {sample_mcq[3]} (গ) {sample_mcq[4]} (ঘ) {sample_mcq[5]}\nAnswer: {sample_mcq[6]}")

print("\n--- Sample Short Question ---")
sample_short = c.execute("SELECT id, short_question, short_answer FROM questions WHERE chapter_id = 638 AND question_type = 'short' LIMIT 1").fetchone()
print(f"ID: {sample_short[0]}\nQ: {sample_short[1]}\nAns: {sample_short[2]}")

print("\n--- Sample CQ ---")
sample_cq = c.execute("SELECT id, cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha FROM questions WHERE chapter_id = 638 AND question_type = 'cq' LIMIT 1").fetchone()
print(f"ID: {sample_cq[0]}\nStem: {sample_cq[1][:80]}...\nক: {sample_cq[2]}\nখ: {sample_cq[3]}\nগ: {sample_cq[4]}\nঘ: {sample_cq[5]}")

print("\n✓ ALL DATABASE VERIFICATIONS PASSED 100%!")
