# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

for ch_id in [210, 211, 213, 214, 215, 636, 637]:
    ch = c.execute("SELECT id, chapter_no, title FROM chapters WHERE id=?", (ch_id,)).fetchone()
    print(f"\n--- Chapter {ch} ---")
    topics = c.execute("SELECT id, title, order_num FROM topics WHERE chapter_id=? ORDER BY order_num", (ch_id,)).fetchall()
    for t in topics:
        q_count = c.execute("SELECT count(*) FROM questions WHERE topic_id=?", (t[0],)).fetchone()[0]
        print(f"  Topic {t[0]} ({t[2]}): {t[1]} [Questions: {q_count}]")
