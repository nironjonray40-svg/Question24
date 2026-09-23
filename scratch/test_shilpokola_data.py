# -*- coding: utf-8 -*-
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from shilpokola_mcqs import all_mcqs
from shilpokola_short import short_questions
from shilpokola_cqs import cqs

print(f"MCQs count: {len(all_mcqs)}")
print(f"Shorts count: {len(short_questions)}")
print(f"CQs count: {len(cqs)}")
total = len(all_mcqs) + len(short_questions) + len(cqs)
print(f"Total questions: {total}")

assert len(all_mcqs) == 87, f"Expected 87 MCQs, got {len(all_mcqs)}"
assert len(short_questions) == 10, f"Expected 10 Shorts, got {len(short_questions)}"
assert len(cqs) == 15, f"Expected 15 CQs, got {len(cqs)}"
assert total == 112, f"Expected 112 questions, got {total}"

# Check MCQs
valid_options = {'ক', 'খ', 'গ', 'ঘ'}
stimulus_indices = [18, 19, 36, 37, 52, 53, 86, 87]
for idx, q in enumerate(all_mcqs, 1):
    assert q['stem'], f"Empty stem in MCQ {idx}"
    assert q['option_a'], f"Empty option_a in MCQ {idx}"
    assert q['option_b'], f"Empty option_b in MCQ {idx}"
    assert q['option_c'], f"Empty option_c in MCQ {idx}"
    assert q['option_d'], f"Empty option_d in MCQ {idx}"
    assert q['correct_option'] in valid_options, f"Invalid correct_option '{q['correct_option']}' in MCQ {idx}"
    if idx in stimulus_indices:
        assert "উদ্দীপকটি পড়ে" in q['stem'], f"Stimulus missing in MCQ {idx}"

# Check board/school tags
mcq_tags = [q['stem'] for q in all_mcqs if '[' in q['stem']]
print(f"Tagged MCQs: {len(mcq_tags)}")

# Check Shorts
for idx, q in enumerate(short_questions, 1):
    assert q['q'], f"Empty question in Short {idx}"
    assert q['ans'], f"Empty answer in Short {idx}"

short_tags = [q['q'] for q in short_questions if '[' in q['q']]
print(f"Tagged Shorts: {len(short_tags)}")

# Check CQs
for idx, q in enumerate(cqs, 1):
    assert q['stem'], f"Empty stem in CQ {idx}"
    assert q['ka'], f"Empty ka in CQ {idx}"
    assert q['kha'], f"Empty kha in CQ {idx}"
    assert q['ga'], f"Empty ga in CQ {idx}"
    assert q['gha'], f"Empty gha in CQ {idx}"
    assert q['solution'], f"Empty solution in CQ {idx}"

cq_tags = [q['stem'] for q in cqs if '[' in q['stem']]
print(f"Tagged CQs: {len(cq_tags)}")

print("\n--- All Checks Passed Successfully! ---")
