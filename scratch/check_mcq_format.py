import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('question_bank.db')
c = conn.cursor()
c.execute("SELECT correct_option, count(*) FROM questions WHERE question_type = 'mcq' GROUP BY correct_option")
print(c.fetchall())

print("\nSample MCQ row:")
c.execute("SELECT mcq_stem, option_a, option_b, option_c, option_d, correct_option, explanation FROM questions WHERE question_type = 'mcq' LIMIT 3")
for r in c.fetchall():
    print(r)
    print('-'*30)
