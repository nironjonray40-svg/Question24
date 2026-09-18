import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
db_path = 'instance/question_bank.db' if os.path.exists('instance/question_bank.db') else 'question_bank.db'
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("--- Question Counts for Chapter 465 ---")
for r in c.execute("SELECT question_type, COUNT(*) as cnt FROM questions WHERE chapter_id=465 GROUP BY question_type").fetchall():
    print(dict(r))

print("\n--- Check MCQs with stimuli (e.g. Q18, Q26, Q50, Q72, Q76) ---")
for r in c.execute("SELECT id, mcq_stem, option_a, correct_option, explanation FROM questions WHERE chapter_id=465 AND question_type='mcq' AND mcq_stem LIKE '%উদ্দীপক%' LIMIT 5").fetchall():
    print("ID:", r['id'])
    print("Stem:", r['mcq_stem'][:100], "...")
    print("Correct:", r['correct_option'])
    print("Explanation:", r['explanation'][:100] if r['explanation'] else None)
    print("-")

print("\n--- Check Sample Short Question ---")
for r in c.execute("SELECT id, short_question, short_answer FROM questions WHERE chapter_id=465 AND question_type='short' LIMIT 2").fetchall():
    print("ID:", r['id'])
    print("Q:", r['short_question'])
    print("A:", r['short_answer'][:150])
    print("-")

print("\n--- Check Sample CQ Question ---")
for r in c.execute("SELECT id, cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha, cq_solution FROM questions WHERE chapter_id=465 AND question_type='cq' LIMIT 2").fetchall():
    print("ID:", r['id'])
    print("Stem:", r['cq_stem'][:100], "...")
    print("Ka:", r['cq_sub_ka'])
    print("Kha:", r['cq_sub_kha'])
    print("Ga:", r['cq_sub_ga'])
    print("Gha:", r['cq_sub_gha'])
    print("Sol:", r['cq_solution'][:150], "...")
    print("-")
