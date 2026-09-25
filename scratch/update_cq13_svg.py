import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

new_stem = """<div class="my-3 text-center"><img src="/static/img/questions/cq_13_shaheed_minar.svg" alt="কেন্দ্রীয় শহীদ মিনার" class="max-w-xs md:max-w-sm mx-auto rounded-lg border border-slate-300 shadow-sm" style="max-height: 220px; object-fit: contain;"></div>
নিচের চিত্রটি দেখে প্রশ্নগুলোর উত্তর দাও :"""

c.execute("UPDATE questions SET cq_stem = ? WHERE id = 3011", (new_stem,))
conn.commit()

# Verify
row = c.execute("SELECT id, chapter_id, cq_stem FROM questions WHERE id = 3011").fetchone()
print("Updated successfully!")
print("ID:", row[0])
print("Chapter ID:", row[1])
print("cq_stem:\n", row[2])
