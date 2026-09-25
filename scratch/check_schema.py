import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()
c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='questions'")
print("Questions table SQL in instance DB:")
print(c.fetchone()[0])

c.execute("SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='questions'")
for r in c.fetchall():
    print(r[0])
