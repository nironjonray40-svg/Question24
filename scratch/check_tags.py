import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

cqs = c.execute("""
    SELECT id, chapter_id, cq_stem, cq_sub_ka 
    FROM questions 
    WHERE (cq_stem LIKE '%[%]%' OR cq_sub_ka LIKE '%[%]%') 
    LIMIT 10
""").fetchall()

for r in cqs:
    print(f'ID {r[0]}, Chap {r[1]}:')
    print('  Stem:', repr(r[2]))
    print('  Ka:', repr(r[3]))
