# -*- coding: utf-8 -*-
import sqlite3
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

db_path = 'instance/question_bank.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

pattern = re.compile(r'^(?:নিচের\s+)?উদ্দীপকটি\s+পড়ে\s+[০-৯\d\s,ওএবং\-]+নম্বর\s+প্রশ্নের\s+উত্তর\s+দাও\s*:\s*', re.MULTILINE)

rows = c.execute("""
    SELECT id, mcq_stem 
    FROM questions 
    WHERE chapter_id = 211 AND question_type = 'mcq'
""").fetchall()

updated_count = 0
for r in rows:
    qid, stem = r
    if pattern.search(stem):
        new_stem = pattern.sub('উদ্দীপকটি পড়ে নিচের প্রশ্নের উত্তর দাও:\n', stem).strip()
        c.execute("UPDATE questions SET mcq_stem = ? WHERE id = ?", (new_stem, qid))
        updated_count += 1
        print(f"Updated ID {qid}:")
        print(new_stem)
        print("=" * 60)

conn.commit()
print(f"\nSuccessfully updated {updated_count} stimulus MCQs in database!")
