import sqlite3

c1 = sqlite3.connect('question_bank.db').cursor()
c2 = sqlite3.connect('instance/question_bank.db').cursor()

c1.execute("SELECT count(*) FROM questions WHERE chapter_id = 644 AND question_type = 'mcq'")
print("Root DB:", c1.fetchone()[0])

c2.execute("SELECT count(*) FROM questions WHERE chapter_id = 644 AND question_type = 'mcq'")
print("Instance DB:", c2.fetchone()[0])
