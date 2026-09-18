import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
for r in c.execute("SELECT q.id, q.chapter_id, ch.title, q.topic_id, q.question_type FROM questions q JOIN chapters ch ON q.chapter_id = ch.id WHERE ch.subject_id = 1 LIMIT 20").fetchall():
    print(r)
