# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=== VERIFYING CHAPTER 639 (মংডুর পথে) ===")

# 1. Total counts
counts = c.execute("""
    SELECT question_type, COUNT(*) 
    FROM questions 
    WHERE chapter_id = 639 
    GROUP BY question_type
""").fetchall()

print("\n--- Question Counts by Type ---")
for qtype, cnt in counts:
    print(f"  {qtype.upper()}: {cnt}")

total_q = sum(cnt for _, cnt in counts)
print(f"  TOTAL: {total_q}")
assert total_q == 158

# 2. Check Stimulus MCQs
print("\n--- Stimulus MCQs Verification ---")
stimulus_mcqs = c.execute("""
    SELECT id, mcq_stem 
    FROM questions 
    WHERE chapter_id = 639 AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপকটি পড়ে%'
    ORDER BY id
""").fetchall()

print(f"Found {len(stimulus_mcqs)} stimulus-based MCQs:")
for qid, stem in stimulus_mcqs:
    first_line = stem.splitlines()[0]
    second_line = stem.splitlines()[1] if len(stem.splitlines()) > 1 else ''
    q_line = [l for l in stem.splitlines() if '?' in l or '—' in l or '।' in l][-1]
    print(f"  ID {qid}: {first_line} | {second_line[:40]}... | {q_line}")

assert len(stimulus_mcqs) == 6, f"Expected 6 stimulus-based MCQs, got {len(stimulus_mcqs)}"

# 3. Check Board and School Tags
print("\n--- Tagged Questions in Chapter 639 ---")
tagged_q = c.execute("""
    SELECT id, question_type, mcq_stem, short_question, cq_stem 
    FROM questions 
    WHERE chapter_id = 639 AND (
        mcq_stem LIKE '%[%]%' OR 
        short_question LIKE '%[%]%' OR 
        cq_stem LIKE '%[%]%'
    )
    ORDER BY id
""").fetchall()

print(f"Total tagged questions: {len(tagged_q)}")
for qid, qtype, mcq, short, cq in tagged_q:
    text = mcq if qtype == 'mcq' else (short if qtype == 'short' else cq)
    tag_start = text.find('[')
    tag_end = text.find(']')
    tag = text[tag_start:tag_end+1] if tag_start != -1 and tag_end != -1 else 'No tag'
    first_line = text.splitlines()[0]
    print(f"  ID {qid} ({qtype.upper()}): {tag} -> {first_line[:60]}")

# 4. Check CQ Structure
print("\n--- CQ Sub-question & Solution Verification ---")
cqs = c.execute("""
    SELECT id, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha, cq_solution 
    FROM questions 
    WHERE chapter_id = 639 AND question_type = 'cq'
    ORDER BY id
""").fetchall()

for idx, (qid, ka, kha, ga, gha, sol) in enumerate(cqs, 1):
    assert ka and kha and ga and gha and sol, f"CQ ID {qid} has missing fields!"
    assert "ক)" in sol and "খ)" in sol and "গ)" in sol and "ঘ)" in sol, f"CQ ID {qid} solution missing parts!"
print(f"All {len(cqs)} CQs verified with valid ক, খ, গ, ঘ sub-questions and complete solutions!")

# 5. Check Short questions
print("\n--- Short Questions Verification ---")
shorts = c.execute("""
    SELECT id, short_question, short_answer 
    FROM questions 
    WHERE chapter_id = 639 AND question_type = 'short'
    ORDER BY id
""").fetchall()

for idx, (qid, q, ans) in enumerate(shorts, 1):
    assert q and ans, f"Short Q ID {qid} has empty question or answer!"
print(f"All {len(shorts)} Short questions verified with valid question and answer text!")

# 6. Check Topics
print("\n--- Topics Verification ---")
topics = c.execute("SELECT id, title, order_num FROM topics WHERE chapter_id = 639 ORDER BY order_num").fetchall()
for tid, title, order_num in topics:
    q_count = c.execute("SELECT COUNT(*) FROM questions WHERE topic_id = ?", (tid,)).fetchone()[0]
    print(f"  Topic {order_num} (ID {tid}): '{title}' -> {q_count} questions")

print("\n✓ ALL VERIFICATIONS SUCCESSFUL!")
