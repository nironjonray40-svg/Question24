import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
p = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript_full.jsonl')

with open(p, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if 'একুশের গান' in line:
            print(f"Found 'একুশের গান' in line {idx}")
            data = json.loads(line)
            print("Keys:", list(data.keys()))
            print("Type:", data.get('type'))
            print("Length:", len(data.get('content', '')))
