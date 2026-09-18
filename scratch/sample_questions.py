import sqlite3
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Sample MCQ Questions ---")
for r in c.execute("SELECT * FROM questions WHERE question_type='mcq' LIMIT 5").fetchall():
    print(dict(r))

print("\n--- Sample Short Questions ---")
for r in c.execute("SELECT * FROM questions WHERE question_type='short' LIMIT 3").fetchall():
    print(dict(r))

print("\n--- Sample CQ Questions ---")
for r in c.execute("SELECT * FROM questions WHERE question_type='cq' LIMIT 2").fetchall():
    print(dict(r))
