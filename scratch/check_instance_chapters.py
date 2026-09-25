import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("--- Chapters in instance/question_bank.db ---")
for r in c.execute("""
    SELECT ch.id, ch.subject_id, s.name, cl.name, ch.chapter_no, ch.title 
    FROM chapters ch 
    JOIN subjects s ON ch.subject_id = s.id 
    JOIN class_levels cl ON s.class_id = cl.id 
    WHERE (cl.name LIKE '%৮%' OR cl.name LIKE '%8%') AND s.name LIKE '%বাংলা%'
    AND (ch.title LIKE '%বাবুরের%' OR ch.title LIKE '%নারী%' OR ch.title LIKE '%আবার আসিব%' OR ch.title LIKE '%রূপাই%')
"""):
    print(r)
