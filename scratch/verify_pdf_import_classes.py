# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=" * 60)
print("VERIFICATION OF INSERTED QUESTIONS IN CLASS 8 BANGLA 1ST")
print("=" * 60)

for ch_id in [650, 660]:
    row = c.execute("SELECT chapter_no, title FROM chapters WHERE id = ?", (ch_id,)).fetchone()
    print(f"\n--- Chapter {ch_id}: {row[0]} - {row[1]} ---")
    
    # Counts by type
    counts = c.execute("""
        SELECT question_type, COUNT(*) 
        FROM questions 
        WHERE chapter_id = ? 
        GROUP BY question_type
    """, (ch_id,)).fetchall()
    
    total = 0
    for qtype, cnt in counts:
        print(f"  {qtype.upper()}: {cnt}")
        total += cnt
    print(f"  TOTAL QUESTIONS: {total}")
    
    # Check stimulus questions
    stim_mcqs = c.execute("""
        SELECT COUNT(*) 
        FROM questions 
        WHERE chapter_id = ? AND question_type = 'mcq' AND mcq_stem LIKE '%উদ্দীপকটি পড়ে নিচের প্রশ্নের উত্তর দাও%'
    """, (ch_id,)).fetchone()[0]
    print(f"  Stimulus-attached MCQs: {stim_mcqs}")
    
    # Check tagged questions
    tagged = c.execute("""
        SELECT id, question_type, mcq_stem, short_question, cq_stem, cq_sub_kha
        FROM questions 
        WHERE chapter_id = ? AND (
            mcq_stem LIKE '%[%]%' OR 
            short_question LIKE '%[%]%' OR 
            cq_stem LIKE '%[%]%' OR 
            cq_sub_kha LIKE '%[%]%'
        )
    """, (ch_id,)).fetchall()
    print(f"  Questions with Board/School Tags: {len(tagged)}")
    for r in tagged[:5]:
        qid, qtype, mcq, sq, cqs, cqk = r
        text = mcq or sq or cqs or cqk or ''
        tag = text[text.find('['):text.find(']')+1]
        print(f"    Sample Tag: {tag} (ID {qid}, {qtype})")

print("\n" + "=" * 60)
print("ALL DATABASE CHECKS COMPLETED SUCCESSFULLY!")
print("=" * 60)
