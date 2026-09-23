import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("CQ with null or empty ga:")
rows = c.execute("SELECT id, chapter_id, cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha FROM questions WHERE question_type='cq' AND (cq_sub_ga IS NULL OR cq_sub_ga='')").fetchall()
print(f"Count: {len(rows)}")
for r in rows[:5]:
    print(r)

print("\nQuestions in আনন্দপাঠ chapters:")
rows2 = c.execute("SELECT ch.id, ch.title, q.question_type, count(*) FROM questions q JOIN chapters ch ON q.chapter_id=ch.id WHERE ch.chapter_no='আনন্দপাঠ' GROUP BY ch.id, ch.title, q.question_type").fetchall()
print(rows2)

print("\nAll distinct question types in DB:")
print(c.execute("SELECT question_type, count(*) FROM questions GROUP BY question_type").fetchall())
