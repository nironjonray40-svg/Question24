import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
p = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript_full.jsonl')

with open(p, 'r', encoding='utf-8') as f:
    line0 = json.loads(f.readline())
    print("Keys in line 0:", list(line0.keys()))
    for k, v in line0.items():
        if isinstance(v, str):
            print(f"Key {k}: length {len(v)}, start: {v[:100]}")
        else:
            print(f"Key {k}: {type(v)}")
