# -*- coding: utf-8 -*-
import os
import re

files_to_clean = [
    'scratch/mukti_questions.py',
    'scratch/hemapathy_questions.py',
    'scratch/filistiner_chithi_questions.py',
    'scratch/kaktadua_questions.py',
    'scratch/david_copperfield_questions.py',
    'scratch/noya_potton_questions.py',
    'scratch/mansingho_esha_kha_questions.py',
    'scratch/tirondaj_questions.py'
]

for fpath in files_to_clean:
    if os.path.exists(fpath):
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        cleaned = re.sub(r'\s*\[\s*ক্রিয়েটিভ মডেল স্কুল\s*\]', '', content)
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print(f"Cleaned file: {fpath}")

print("All scratch question files cleaned successfully.")
