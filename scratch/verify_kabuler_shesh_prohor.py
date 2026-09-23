# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=== VERIFYING CHAPTER 659 (কাবুলের শেষ প্রহর) ===")

chapter = c.execute("""
    SELECT ch.id, ch.chapter_no, ch.title, s.name, cl.name 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE ch.id = 659
""").fetchone()

print(f"Chapter: {chapter}")

topics = c.execute("SELECT id, order_num, title FROM topics WHERE chapter_id = 659 ORDER BY order_num").fetchall()
print(f"\nTopics ({len(topics)}):")
for t in topics:
    print(f"  {t[1]}. [ID {t[0]}] {t[2]}")

counts = c.execute("SELECT question_type, count(*), sum(marks) FROM questions WHERE chapter_id = 659 GROUP BY question_type").fetchall()
print(f"\nQuestion counts: {counts}")

print("\n--- All CQ Questions (8) ---")
cqs = c.execute("""
    SELECT id, cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha, marks 
    FROM questions 
    WHERE chapter_id = 659 AND question_type = 'cq' 
    ORDER BY id
""").fetchall()

for i, q in enumerate(cqs, 1):
    qid, stem, ka, kha, ga, gha, marks = q
    tag = stem[stem.find('['):stem.find(']')+1] if '[' in stem else 'NO TAG'
    print(f"\nCQ {i} [ID {qid}] (Marks: {marks}) Tag: {tag}")
    print(f"  Stem : {stem}")
    print(f"  ক    : {ka[:60]}...")
    print(f"  খ    : {kha[:60]}...")

print("\n--- All Short Questions (16) ---")
shorts = c.execute("""
    SELECT id, short_question, short_answer, marks 
    FROM questions 
    WHERE chapter_id = 659 AND question_type = 'short' 
    ORDER BY id
""").fetchall()

for i, q in enumerate(shorts, 1):
    qid, question, answer, marks = q
    tag = question[question.find('['):question.find(']')+1] if '[' in question else 'NO TAG'
    print(f"Short {i:02d} [ID {qid}] (Marks: {marks}) Tag: {tag} | Q: {question[:50]}...")

# Check that every question has [ক্রিয়েটিভ মডেল স্কুল]
total_q = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 659").fetchone()[0]
tagged_q = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 659 AND (mcq_stem LIKE '%[ক্রিয়েটিভ মডেল স্কুল]%' OR cq_stem LIKE '%[ক্রিয়েটিভ মডেল স্কুল]%' OR short_question LIKE '%[ক্রিয়েটিভ মডেল স্কুল]%')").fetchone()[0]

print(f"\nTotal questions: {total_q}")
print(f"Tagged questions with [ক্রিয়েটিভ মডেল স্কুল]: {tagged_q}")
assert total_q == tagged_q == 24, "All questions must be tagged!"
print("\n✓ ALL 24 QUESTIONS HAVE VALID TAGS AND ARE FULLY VERIFIED!")
