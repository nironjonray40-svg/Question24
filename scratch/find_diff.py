import sqlite3

c1 = sqlite3.connect('question_bank.db').cursor()
c2 = sqlite3.connect('instance/question_bank.db').cursor()

c1.execute("SELECT mcq_stem FROM questions WHERE chapter_id = 644 AND question_type = 'mcq'")
stems1 = set([r[0] for r in c1.fetchall()])

c2.execute("SELECT mcq_stem FROM questions WHERE chapter_id = 644 AND question_type = 'mcq'")
stems2 = set([r[0] for r in c2.fetchall()])

diff = stems1 - stems2
print("In Root but not in Instance:", len(diff))
print("Diff item:", diff)
print("Len stems1:", len(stems1), "Len stems2:", len(stems2))

# Check duplicates in root:
c1.execute("SELECT mcq_stem, count(*) FROM questions WHERE chapter_id = 644 AND question_type = 'mcq' GROUP BY mcq_stem HAVING count(*) > 1")
print("Duplicates in Root:", c1.fetchall())
