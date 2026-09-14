import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/subha_questions_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for i, s in enumerate(data['shorts'][:27]):
    print(f"{i+1}. ID: {s['id']} | Q: {s['question']}")
