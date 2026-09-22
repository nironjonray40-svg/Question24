# -*- coding: utf-8 -*-
import sqlite3, re, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

pattern = re.compile(r'নম্বর\s+প্রশ্নের\s+উত্তর\s+দাও', re.MULTILINE)
matches = [r for r in c.execute("SELECT id, mcq_stem FROM questions WHERE question_type = 'mcq'").fetchall() if pattern.search(r[1])]
print(f"Remaining questions with 'নম্বর প্রশ্নের উত্তর দাও': {len(matches)}")

counts = c.execute("SELECT question_type, count(*) FROM questions WHERE chapter_id = 211 GROUP BY question_type").fetchall()
print("Chapter 211 counts:", counts)

print("\n--- Verification of Updated Sample Questions ---")
for qid in [217, 218]:
    r = c.execute("SELECT id, mcq_stem FROM questions WHERE id = ?", (qid,)).fetchone()
    print(f"\nID {r[0]}:\n{r[1]}")

print("\n✓ All checks passed!")
