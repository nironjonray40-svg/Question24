import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
c = conn.cursor()
for r in c.execute("SELECT id, chapter_id, title, order_num FROM topics WHERE chapter_id = 465").fetchall():
    print(r)
