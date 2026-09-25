import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('question_bank.db')
c = conn.cursor()

print("Existing questions with brackets:")
for r in c.execute("SELECT id, question_type, mcq_stem, short_question, cq_stem FROM questions WHERE mcq_stem LIKE '%[%]%' OR short_question LIKE '%[%]%' OR cq_stem LIKE '%[%]%' LIMIT 5"):
    print(r)
    print("="*40)
