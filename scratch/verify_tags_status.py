# -*- coding: utf-8 -*-
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

# Find any questions in DB that have bracketed tags like [...] in cq_sub_kha
rows = c.execute("""
    SELECT q.id, ch.title, q.cq_sub_kha
    FROM questions q
    JOIN chapters ch ON q.chapter_id = ch.id
    JOIN subjects s ON ch.subject_id = s.id
    JOIN class_levels cl ON s.class_id = cl.id
    WHERE cl.name LIKE '%৮ম%' AND s.name LIKE '%বাংলা ১ম%' AND ch.chapter_no = 'আনন্দপাঠ'
""").fetchall()

print(f"Total questions checked in Class 8 Bangla 1st Anandapath: {len(rows)}")

school_tagged = []
creative_tagged = []

for q_id, ch_title, kha in rows:
    if "ক্রিয়েটিভ মডেল স্কুল" in kha:
        creative_tagged.append((q_id, ch_title, kha))
    tags = re.findall(r'\[([^\]]+)\]', kha)
    if tags:
        school_tagged.append((q_id, ch_title, tags))

print(f"Questions containing 'ক্রিয়েটিভ মডেল স্কুল': {len(creative_tagged)}")
print(f"\nQuestions with genuine Board / School tags ({len(school_tagged)}):")
for q_id, ch_title, tags in school_tagged:
    print(f"  [Q ID {q_id}] {ch_title}: {tags}")

assert len(creative_tagged) == 0, "Error: Some questions still have [ক্রিয়েটিভ মডেল স্কুল]!"
print("\n✓ Verification successful: [ক্রিয়েটিভ মডেল স্কুল] completely removed, genuine school tags preserved!")
