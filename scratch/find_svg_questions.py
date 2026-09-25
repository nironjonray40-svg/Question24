import sqlite3, sys
sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print('--- Searching questions with svg or img ---')
rows = c.execute("""
    SELECT id, chapter_id, question_type, cq_stem, mcq_stem 
    FROM questions 
    WHERE cq_stem LIKE '%<svg%' OR cq_stem LIKE '%svg%' OR cq_stem LIKE '%<img%'
       OR mcq_stem LIKE '%<svg%' OR mcq_stem LIKE '%svg%' OR mcq_stem LIKE '%<img%'
""").fetchall()
print(f'Found: {len(rows)}')
for r in rows[:10]:
    txt = r[3] or r[4] or ''
    print(r[0], r[1], r[2], txt[:120])

print('\n--- Searching questions with চিত্র ---')
rows = c.execute("""
    SELECT id, chapter_id, question_type, cq_stem 
    FROM questions 
    WHERE cq_stem LIKE '%চিত্র%'
""").fetchall()
print(f'Found: {len(rows)}')
for r in rows:
    print(r[0], r[1], r[2], r[3][:150])
