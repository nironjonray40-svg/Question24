import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
print("Using DB:", db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("\n--- Classes ---")
for r in c.execute("SELECT id, name FROM class_levels").fetchall():
    print(r)

print("\n--- Subjects for Class 8 ---")
for r in c.execute("SELECT s.id, s.name FROM subjects s JOIN class_levels cl ON s.class_id = cl.id WHERE cl.name LIKE '%৮ম%'").fetchall():
    print(r)

print("\n--- Chapters in Class 8 Bangla 1st ---")
for r in c.execute("""
    SELECT ch.id, ch.chapter_no, ch.title 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE cl.name LIKE '%৮ম%' AND s.name LIKE '%বাংলা ১ম%'
    ORDER BY ch.chapter_no, ch.id
""").fetchall():
    print(r)

print("\n--- Search for লাইব্রেরি anywhere in DB ---")
for r in c.execute("SELECT id, chapter_no, title, subject_id FROM chapters WHERE title LIKE '%লাইব্রেরি%'").fetchall():
    print(r)
