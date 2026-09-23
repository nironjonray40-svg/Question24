# -*- coding: utf-8 -*-
import sqlite3
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('instance/question_bank.db')
c = conn.cursor()

print("=== UPDATING SCHOOL/COLLEGE TAGS IN CHAPTER 636 ===")

updates = [
    (
        "'সমস্ত সম্প্রদায়ের আত্মীয়' কে? [গভর্নমেন্ট ল্যাবরেটরি হাই স্কুল, ঢাকা]",
        986
    ),
    (
        "'পরার্থ' শব্দের অর্থ কী? [বি এ এফ শাহীন কলেজ, ঢাকা]",
        995
    ),
    (
        "একজনের পক্ষে সব জ্ঞান আহরণ করা সম্ভব নয় কারণ— [কুমিল্লা জিলা স্কুল]\ni. জ্ঞানভান্ডার বহুমুখী\nii. জ্ঞানভান্ডার বিশাল\niii. জ্ঞানভান্ডার সামষ্টিক\nনিচের কোনটি সঠিক?",
        996
    ),
    (
        "'লাইব্রেরি' প্রবন্ধে যেসব নদীর নাম উল্লেখ রয়েছে— [বি এ এফ শাহীন কলেজ, ঢাকা]\ni. পদ্মা\nii. গঙ্গা\niii. যমুনা\nনিচের কোনটি সঠিক?",
        1000
    )
]

for new_stem, qid in updates:
    c.execute("UPDATE questions SET mcq_stem = ? WHERE id = ? AND chapter_id = 636", (new_stem, qid))
    print(f"Updated ID {qid}: {new_stem.splitlines()[0]}")

conn.commit()

# Verify all questions with tags in chapter 636
print("\n--- All Questions with School/College/Board Tags in Chapter 636 ---")
tagged_q = c.execute("""
    SELECT id, question_type, mcq_stem, cq_stem 
    FROM questions 
    WHERE chapter_id = 636 AND (mcq_stem LIKE '%[%]%' OR cq_stem LIKE '%[%]%')
    ORDER BY id
""").fetchall()

for r in tagged_q:
    qid, qtype, mcq, cq = r
    text = mcq if qtype == 'mcq' else cq
    tag = text[text.find('['):text.find(']')+1] if '[' in text else ''
    first_line = text.splitlines()[0]
    last_line = text.splitlines()[-1]
    print(f"ID {qid} ({qtype.upper()}): {tag} -> {first_line[:50]}... | {last_line}")

print(f"\nTotal tagged questions found: {len(tagged_q)}")
assert len(tagged_q) == 7, f"Expected 7 tagged questions, got {len(tagged_q)}"
print("ALL 7 TAGGED QUESTIONS VERIFIED SUCCESSFULLY!")
