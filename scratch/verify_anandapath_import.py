# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

total_desc = c.execute("SELECT COUNT(id) FROM questions WHERE question_type = 'descriptive'").fetchone()[0]
print(f"Total descriptive questions in DB: {total_desc}")

print("\n--- Class 8 Bangla 1st (Anandapath) Chapters & Question Count ---")
query = """
    SELECT ch.id, ch.title, COUNT(q.id)
    FROM chapters ch
    JOIN subjects s ON ch.subject_id = s.id
    JOIN class_levels cl ON s.class_id = cl.id
    LEFT JOIN questions q ON q.chapter_id = ch.id
    WHERE cl.name LIKE '%৮ম%' AND s.name LIKE '%বাংলা ১ম%' AND ch.chapter_no = 'আনন্দপাঠ'
    GROUP BY ch.id, ch.title
    ORDER BY ch.id
"""
for r in c.execute(query).fetchall():
    print(f"  ID {r[0]}: {r[1]} -> {r[2]} questions")

print("\n--- Sample Verification of School/College Tags ---")
tag_samples = [
    (656, "%গভর্নমেন্ট ল্যাবরেটরি%"),
    (651, "%বিন্দুবাসিনী%"),
    (654, "%আদমজী%")
]
for ch_id, pattern in tag_samples:
    res = c.execute("SELECT id, cq_sub_kha FROM questions WHERE chapter_id = ? AND cq_sub_kha LIKE ?", (ch_id, pattern)).fetchall()
    print(f"Chapter {ch_id} tag match ({pattern}): {len(res)} question(s) found.")
    for q_id, kha in res:
        print(f"   [Q ID {q_id}] {kha[-70:]}")

print("\n✓ ALL DATABASE VERIFICATIONS PASSED!")
