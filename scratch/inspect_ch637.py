# -*- coding: utf-8 -*-
import sys
import io
import sqlite3

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tables:", [r[0] for r in c.fetchall()])

c.execute("SELECT id, name FROM class_levels WHERE name LIKE '%৮ম%'")
print("Classes:", c.fetchall())

c.execute("SELECT id, class_id, name FROM subjects WHERE name LIKE '%বাংলা ১ম%'")
print("Subjects:", c.fetchall())

c.execute("SELECT id, subject_id, chapter_no, title FROM chapters WHERE title LIKE '%সুখী মানুষ%'")
print("Chapters:", c.fetchall())

c.execute("SELECT count(*) FROM topics WHERE chapter_id = 637")
print("Topics count for ch 637:", c.fetchone()[0])

c.execute("SELECT count(*) FROM questions WHERE chapter_id = 637")
print("Questions count for ch 637:", c.fetchone()[0])
