import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()

for r in c.execute("""
    SELECT ch.id, ch.title, q.question_type, t.id, t.title, COUNT(q.id)
    FROM questions q
    JOIN chapters ch ON q.chapter_id = ch.id
    LEFT JOIN topics t ON q.topic_id = t.id
    WHERE ch.subject_id = 1
    GROUP BY ch.id, q.question_type, t.id
    LIMIT 30
""").fetchall():
    print(r)
