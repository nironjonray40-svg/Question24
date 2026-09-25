import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('question_bank.db')
c = conn.cursor()

print("Sample Short Question:")
c.execute("SELECT short_question, short_answer FROM questions WHERE question_type = 'short' LIMIT 2")
for r in c.fetchall():
    print(r)
    print('-'*30)

print("\nSample CQ:")
c.execute("SELECT cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha, cq_solution FROM questions WHERE question_type = 'cq' LIMIT 2")
for r in c.fetchall():
    print(r)
    print('-'*30)
