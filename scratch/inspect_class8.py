import sqlite3
import sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('question_bank.db')
c = conn.cursor()

print("--- Class Levels ---")
for row in c.execute("SELECT id, name FROM class_levels"):
    print(row)

print("\n--- Subjects for Class 8 ---")
for row in c.execute("""
    SELECT s.id, s.name, cl.name 
    FROM subjects s 
    JOIN class_levels cl ON s.class_level_id = cl.id
    WHERE cl.name LIKE '%৮%' OR cl.name LIKE '%8%' OR cl.name LIKE '%অষ্টম%'
"""):
    print(row)

print("\n--- Chapters for Class 8 Bangla ---")
for row in c.execute("""
    SELECT ch.id, ch.name, s.name, cl.name
    FROM chapters ch
    JOIN subjects s ON ch.subject_id = s.id
    JOIN class_levels cl ON s.class_level_id = cl.id
    WHERE (cl.name LIKE '%৮%' OR cl.name LIKE '%8%' OR cl.name LIKE '%অষ্টম%')
      AND s.name LIKE '%বাংলা%'
"""):
    print(row)
