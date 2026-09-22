# -*- coding: utf-8 -*-
import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("Sample MCQ stems with 'উদ্দীপক' in other chapters:")
rows = c.execute("""
    SELECT id, chapter_id, mcq_stem 
    FROM questions 
    WHERE question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপক%' AND chapter_id != 211 
    LIMIT 15
""").fetchall()

for r in rows:
    print(f"ID {r[0]} (Ch {r[1]}):")
    print(r[2])
    print("-" * 50)
