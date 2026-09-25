# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

for db_path in ['instance/question_bank.db', 'question_bank.db']:
    print(f"\n==========================================")
    print(f"Checking Database: {db_path}")
    print(f"==========================================")
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    grand_total_target = 0
    for ch_id in [649, 647]:
        c.execute('SELECT chapter_no, title FROM chapters WHERE id = ?', (ch_id,))
        ch_info = c.fetchone()
        c.execute('SELECT question_type, COUNT(*) FROM questions WHERE chapter_id = ? GROUP BY question_type', (ch_id,))
        type_counts = dict(c.fetchall())
        total = sum(type_counts.values())
        grand_total_target += total
        print(f"\nঅধ্যায় ID {ch_id} [{ch_info[0]}: {ch_info[1]}]:")
        print(f"  • MCQ: {type_counts.get('mcq', 0)} টি")
        print(f"  • Short: {type_counts.get('short', 0)} টি")
        print(f"  • CQ: {type_counts.get('cq', 0)} টি")
        print(f"  • মোট: {total} টি")
        
    c.execute('SELECT mcq_stem, correct_option FROM questions WHERE chapter_id = 649 AND mcq_stem LIKE "%চ. বো%"')
    print("  • Sample Board MCQ (649):", c.fetchone())
    c.execute('SELECT mcq_stem, correct_option FROM questions WHERE chapter_id = 647 AND mcq_stem LIKE "%রাজউক%"')
    print("  • Sample School MCQ (647):", c.fetchone())
    c.execute('SELECT COUNT(*) FROM questions')
    print(f"\nসমগ্র ডাটাবেজে মোট প্রশ্ন: {c.fetchone()[0]} টি")
    print(f"এই দুটি অধ্যায়ে মোট প্রশ্ন: {grand_total_target} টি")
    conn.close()
