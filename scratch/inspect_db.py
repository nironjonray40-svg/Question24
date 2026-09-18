import sqlite3
import os
import sys

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
print("Using DB:", db_path)

conn = sqlite3.connect(db_path)
c = conn.cursor()

print("\n--- Classes ---")
for row in c.execute("SELECT id, name, code FROM class_levels").fetchall():
    print(row)

print("\n--- Subjects in Class 9-10 ---")
for row in c.execute("""
    SELECT s.id, s.class_id, cl.name, s.name 
    FROM subjects s 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE cl.name LIKE '%৯ম%' OR cl.name LIKE '%9%'
""").fetchall():
    print(row)

print("\n--- Chapters matching পল্লি ---")
for row in c.execute("""
    SELECT ch.id, ch.subject_id, s.name, ch.chapter_no, ch.title 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    WHERE ch.title LIKE '%পল্লি%' OR ch.title LIKE '%পল্লী%'
""").fetchall():
    print(row)

print("\n--- All chapters for Bangla 1st in 9-10 ---")
for row in c.execute("""
    SELECT ch.id, ch.chapter_no, ch.title 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE (cl.name LIKE '%৯ম%' OR cl.name LIKE '%9%') 
      AND (s.name LIKE '%বাংলা ১ম%' OR s.name LIKE '%বাংলা 1st%')
""").fetchall():
    print(row)

print("\n--- Existing Questions Count in Chapter ---")
for row in c.execute("""
    SELECT ch.id, ch.title, q.question_type, COUNT(q.id)
    FROM chapters ch
    LEFT JOIN questions q ON ch.id = q.chapter_id
    WHERE ch.title LIKE '%পল্লি%' OR ch.title LIKE '%পল্লী%'
    GROUP BY ch.id, q.question_type
""").fetchall():
    print(row)
