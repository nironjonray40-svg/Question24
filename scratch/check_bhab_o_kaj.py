import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')

db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
print('DB path:', db_path)
conn = sqlite3.connect(db_path)
c = conn.cursor()

print('Classes:')
for r in c.execute('SELECT id, name, code FROM class_levels').fetchall():
    print(r)

print('\nSubjects for Class 8:')
for r in c.execute('SELECT s.id, s.class_id, s.name, s.code FROM subjects s JOIN class_levels cl ON s.class_id = cl.id WHERE cl.name LIKE "%৮ম%" OR cl.name LIKE "%8%"').fetchall():
    print(r)

print('\nChapters matching "ভাব ও কাজ":')
for r in c.execute('''SELECT ch.id, ch.subject_id, ch.chapter_no, ch.title, s.name, cl.name 
                      FROM chapters ch 
                      JOIN subjects s ON ch.subject_id = s.id 
                      JOIN class_levels cl ON s.class_id = cl.id 
                      WHERE ch.title LIKE "%ভাব ও কাজ%"''').fetchall():
    print(r)
