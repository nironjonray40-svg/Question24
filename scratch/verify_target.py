import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("Subjects for class_id=4:")
for r in c.execute("SELECT id, name FROM subjects WHERE class_id=4").fetchall():
    print(r)

print("\nChapters for 'পল্লি-সাহিত্য':")
for r in c.execute("SELECT ch.id, ch.subject_id, s.name, cl.name, ch.chapter_no, ch.title FROM chapters ch JOIN subjects s ON ch.subject_id = s.id JOIN class_levels cl ON s.class_id = cl.id WHERE ch.title LIKE '%পল্লি-সাহিত্য%' OR ch.title LIKE '%পল্লিসাহিত্য%'").fetchall():
    print(r)
