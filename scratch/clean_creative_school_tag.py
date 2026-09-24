# -*- coding: utf-8 -*-
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

# Find all questions with 'ক্রিয়েটিভ মডেল স্কুল'
rows = c.execute("SELECT id, cq_sub_kha FROM questions WHERE cq_sub_kha LIKE '%ক্রিয়েটিভ মডেল স্কুল%'").fetchall()
print(f"Total questions with [ক্রিয়েটিভ মডেল স্কুল]: {len(rows)}")

updated_count = 0
for q_id, kha in rows:
    # Remove [ক্রিয়েটিভ মডেল স্কুল] or (ক্রিয়েটিভ মডেল স্কুল) or variants
    new_kha = re.sub(r'\s*\[\s*ক্রিয়েটিভ মডেল স্কুল\s*\]', '', kha)
    new_kha = re.sub(r'\s*\(\s*ক্রিয়েটিভ মডেল স্কুল\s*\)', '', new_kha)
    new_kha = new_kha.strip()
    c.execute("UPDATE questions SET cq_sub_kha = ? WHERE id = ?", (new_kha, q_id))
    updated_count += 1

conn.commit()
print(f"Successfully cleaned {updated_count} questions in DB.")

# Check again
remaining = c.execute("SELECT COUNT(id) FROM questions WHERE cq_sub_kha LIKE '%ক্রিয়েটিভ মডেল স্কুল%'").fetchone()[0]
print(f"Remaining questions with [ক্রিয়েটিভ মডেল স্কুল]: {remaining}")
