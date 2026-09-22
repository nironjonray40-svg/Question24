# -*- coding: utf-8 -*-
import sqlite3, os, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

c.execute("UPDATE questions SET topic_id = 4193 WHERE chapter_id = 211 AND question_type IN ('short', 'cq')")
conn.commit()
print("Updated short and cq questions to topic 4193.")

print("\nQuestions breakdown by topic and type in Chapter 211:")
for r in c.execute("""SELECT t.id, t.title, q.question_type, count(q.id) 
                      FROM questions q 
                      JOIN topics t ON q.topic_id = t.id 
                      WHERE q.chapter_id = 211 
                      GROUP BY t.id, q.question_type""").fetchall():
    print(r)
