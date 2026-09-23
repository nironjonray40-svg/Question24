# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("--- CQ Samples with tags ---")
for r in c.execute("SELECT id, cq_stem, cq_sub_ka, cq_sub_kha FROM questions WHERE cq_stem LIKE '%[%]%' LIMIT 5").fetchall():
    print(r)

print("--- Short Samples with tags ---")
for r in c.execute("SELECT id, short_question FROM questions WHERE short_question LIKE '%[%]%' LIMIT 5").fetchall():
    print(r)
