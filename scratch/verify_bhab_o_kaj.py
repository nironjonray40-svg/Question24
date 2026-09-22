# -*- coding: utf-8 -*-
import sqlite3, os, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("==================================================")
print("VERIFICATION: भाव ও কাজ (কাজী নজরুল ইসলাম)")
print("==================================================")

# Chapter info
ch = c.execute("""SELECT cl.name, s.name, ch.chapter_no, ch.title, ch.id 
                  FROM chapters ch 
                  JOIN subjects s ON ch.subject_id = s.id 
                  JOIN class_levels cl ON s.class_id = cl.id 
                  WHERE ch.id = 211""").fetchone()
print(f"Class: {ch[0]}, Subject: {ch[1]}, Chapter: {ch[2]} - {ch[3]} (ID: {ch[4]})")

# Topics
print("\nTopics in Chapter 211:")
for r in c.execute("SELECT id, order_num, title FROM topics WHERE chapter_id = 211 ORDER BY order_num").fetchall():
    print(f"  [{r[1]}] ID {r[0]}: {r[2]}")

# Counts by type
print("\nQuestions Count by Type:")
for r in c.execute("""SELECT question_type, count(*) 
                      FROM questions 
                      WHERE chapter_id = 211 
                      GROUP BY question_type""").fetchall():
    print(f"  {r[0]}: {r[1]}")

# Total
total = c.execute("SELECT count(*) FROM questions WHERE chapter_id = 211").fetchone()[0]
print(f"  Total: {total}")

# Sample MCQ
print("\nSample MCQ (Q1):")
q_mcq = c.execute("""SELECT mcq_stem, option_a, option_b, option_c, option_d, correct_option 
                     FROM questions 
                     WHERE chapter_id = 211 AND question_type = 'mcq' 
                     LIMIT 1""").fetchone()
print(f"  Stem: {q_mcq[0]}")
print(f"  (ক) {q_mcq[1]}  (খ) {q_mcq[2]}  (গ) {q_mcq[3]}  (ঘ) {q_mcq[4]}")
print(f"  Correct: {q_mcq[5]}")

# Sample MCQ with explanation
print("\nSample MCQ with explanation:")
q_exp = c.execute("""SELECT mcq_stem, correct_option, explanation 
                     FROM questions 
                     WHERE chapter_id = 211 AND explanation IS NOT NULL 
                     LIMIT 1""").fetchone()
print(f"  Stem: {q_exp[0]}")
print(f"  Correct: {q_exp[1]}")
print(f"  Explanation: {q_exp[2]}")

# Sample Short
print("\nSample Short Question (Q1):")
q_sh = c.execute("""SELECT short_question, short_answer 
                    FROM questions 
                    WHERE chapter_id = 211 AND question_type = 'short' 
                    LIMIT 1""").fetchone()
print(f"  Q: {q_sh[0]}")
print(f"  Ans: {q_sh[1][:120]}...")

# Sample CQ
print("\nSample CQ (Q1):")
q_cq = c.execute("""SELECT cq_stem, cq_sub_ka, cq_sub_kha, cq_sub_ga, cq_sub_gha 
                    FROM questions 
                    WHERE chapter_id = 211 AND question_type = 'cq' 
                    LIMIT 1""").fetchone()
print(f"  Stem: {q_cq[0][:100]}...")
print(f"  (ক) {q_cq[1]}")
print(f"  (খ) {q_cq[2]}")
print(f"  (গ) {q_cq[3]}")
print(f"  (ঘ) {q_cq[4]}")

print("\n✓ Verification successful!")
