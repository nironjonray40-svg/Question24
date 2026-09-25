import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
p = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript_full.jsonl')

with open(p, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        data = json.loads(line)
        t = data.get('type')
        c = data.get('content', '')
        print(f"Line {idx}: type={t}, len={len(c)}, keys={list(data.keys())}")
        if len(c) > 0:
            print(f"  sample: {c[:100]}...")
