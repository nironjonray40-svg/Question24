
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('question_bank.db')
c = conn.cursor()

print("--- Class Levels ---")
for r in c.execute("SELECT id, name, code FROM class_levels"):
    print(r)

print("\n--- Subjects for Class 8 ---")
for r in c.execute("""
    SELECT s.id, s.class_id, cl.name, s.name, s.code 
    FROM subjects s 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE cl.name LIKE '%৮%' OR cl.name LIKE '%8%'
"""):
    print(r)

print("\n--- Chapters under Class 8 Bangla ---")
for r in c.execute("""
    SELECT ch.id, ch.subject_id, s.name, ch.chapter_no, ch.title 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE (cl.name LIKE '%৮%' OR cl.name LIKE '%8%') AND s.name LIKE '%বাংলা%'
"""):
    print(r)
