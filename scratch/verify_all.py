import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')
conn = sqlite3.connect('question_bank.db')
c = conn.cursor()

print("=== Question Bank Import Verification ===")
grand_total = 0
for ch_id in [644, 220, 645, 646]:
    c.execute('SELECT chapter_no, title FROM chapters WHERE id = ?', (ch_id,))
    ch = c.fetchone()
    c.execute('SELECT question_type, COUNT(*) FROM questions WHERE chapter_id = ? GROUP BY question_type', (ch_id,))
    counts = dict(c.fetchall())
    total = sum(counts.values())
    grand_total += total
    print(f"\nঅধ্যায় ID {ch_id} [{ch[0]}: {ch[1]}]:")
    print(f"  • MCQ (বহুনির্বাচনি): {counts.get('mcq', 0)} টি")
    print(f"  • Short (সংক্ষিপ্ত প্রশ্ন): {counts.get('short', 0)} টি")
    print(f"  • CQ (সৃজনশীল প্রশ্ন): {counts.get('cq', 0)} টি")
    print(f"  • মোট প্রশ্ন: {total} টি")

print(f"\nসর্বমোট যুক্ত হওয়া প্রশ্নের সংখ্যা: {grand_total} টি")
