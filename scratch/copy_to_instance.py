import sqlite3, sys

sys.stdout.reconfigure(encoding='utf-8')

src_conn = sqlite3.connect('question_bank.db')
src_cur = src_conn.cursor()

dst_conn = sqlite3.connect('instance/question_bank.db')
dst_cur = dst_conn.cursor()

target_chapters = [644, 220, 645, 646]

# First check existing count in dst
print("Checking dst counts before copy:")
for ch_id in target_chapters:
    dst_cur.execute("SELECT COUNT(*) FROM questions WHERE chapter_id = ?", (ch_id,))
    print(f"Chapter {ch_id}: {dst_cur.fetchone()[0]} questions")

# Delete if any partial exists
for ch_id in target_chapters:
    dst_cur.execute("DELETE FROM questions WHERE chapter_id = ?", (ch_id,))

# Get columns from questions table
dst_cur.execute("PRAGMA table_info(questions)")
columns = [col[1] for col in dst_cur.fetchall() if col[1] != 'id'] # exclude autoincrement id
col_names_str = ", ".join(columns)
placeholders = ", ".join(["?"] * len(columns))

insert_sql = f"INSERT INTO questions ({col_names_str}) VALUES ({placeholders})"

# Fetch rows from source
src_cur.execute(f"SELECT {col_names_str} FROM questions WHERE chapter_id IN (644, 220, 645, 646)")
rows = src_cur.fetchall()

print(f"\nFetched {len(rows)} questions from root question_bank.db")

dst_cur.executemany(insert_sql, rows)
dst_conn.commit()

print("\nSuccessfully copied into instance/question_bank.db!")

# Verify counts in dst
print("\nVerifying instance/question_bank.db counts:")
grand_total = 0
for ch_id in target_chapters:
    dst_cur.execute("SELECT chapter_no, title FROM chapters WHERE id = ?", (ch_id,))
    ch = dst_cur.fetchone()
    dst_cur.execute("SELECT question_type, COUNT(*) FROM questions WHERE chapter_id = ? GROUP BY question_type", (ch_id,))
    counts = dict(dst_cur.fetchall())
    total = sum(counts.values())
    grand_total += total
    print(f"\nঅধ্যায় ID {ch_id} [{ch[0]}: {ch[1]}]:")
    print(f"  • MCQ: {counts.get('mcq', 0)} টি")
    print(f"  • Short: {counts.get('short', 0)} টি")
    print(f"  • CQ: {counts.get('cq', 0)} টি")
    print(f"  • মোট: {total} টি")

print(f"\nমোট প্রশ্ন instance/question_bank.db তে যুক্ত হয়েছে: {grand_total} টি")
