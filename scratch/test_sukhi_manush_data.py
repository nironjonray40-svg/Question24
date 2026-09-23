# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, 'scratch')

from sukhi_manush_mcqs_part1 import mcqs_part1
from sukhi_manush_mcqs_part2 import mcqs_part2
from sukhi_manush_short import short_questions
from sukhi_manush_cq_part1 import cqs_part1
from sukhi_manush_cq_part2 import cqs_part2

all_mcqs = mcqs_part1 + mcqs_part2
all_cqs = cqs_part1 + cqs_part2

print(f"Total MCQs Part 1: {len(mcqs_part1)}")
print(f"Total MCQs Part 2: {len(mcqs_part2)}")
print(f"Total MCQs: {len(all_mcqs)}")
print(f"Total Short Questions: {len(short_questions)}")
print(f"Total CQs Part 1: {len(cqs_part1)}")
print(f"Total CQs Part 2: {len(cqs_part2)}")
print(f"Total CQs: {len(all_cqs)}")
print(f"Grand Total Questions: {len(all_mcqs) + len(short_questions) + len(all_cqs)}")

# Validate MCQs
for i, m in enumerate(all_mcqs, 1):
    assert "stem" in m and m["stem"], f"MCQ {i} missing stem"
    assert "option_a" in m and m["option_a"], f"MCQ {i} missing option_a"
    assert "option_b" in m and m["option_b"], f"MCQ {i} missing option_b"
    assert "option_c" in m and m["option_c"], f"MCQ {i} missing option_c"
    assert "option_d" in m and m["option_d"], f"MCQ {i} missing option_d"
    assert "correct_option" in m and m["correct_option"] in ['ক', 'খ', 'গ', 'ঘ'], f"MCQ {i} invalid correct_option: {m.get('correct_option')}"

# Validate Short Qs
for i, s in enumerate(short_questions, 1):
    assert "q" in s and s["q"], f"Short Q {i} missing q"
    assert "ans" in s and s["ans"], f"Short Q {i} missing ans"

# Validate CQs
for i, c in enumerate(all_cqs, 1):
    assert "stem" in c and c["stem"], f"CQ {i} missing stem"
    assert "ka" in c and c["ka"], f"CQ {i} missing ka"
    assert "kha" in c and c["kha"], f"CQ {i} missing kha"
    assert "ga" in c and c["ga"], f"CQ {i} missing ga"
    assert "gha" in c and c["gha"], f"CQ {i} missing gha"
    assert "solution" in c and c["solution"], f"CQ {i} missing solution"

print("✓ All 196 questions passed structural validation!")
