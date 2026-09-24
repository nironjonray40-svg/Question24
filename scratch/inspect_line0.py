import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

path = 'C:/Users/niron/.gemini/antigravity-ide/brain/ebe55076-e47d-47a4-a272-a0c82e56bdbe/.system_generated/logs/transcript_full.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    line0 = f.readline()
    d = json.loads(line0)
    print("Keys:", list(d.keys()))
    c = d.get('content')
    print("Content type:", type(c))
    if isinstance(c, list):
        print("List length:", len(c))
        for idx, item in enumerate(c):
            if isinstance(item, dict):
                print(f"Item {idx}: keys={list(item.keys())}")
                for k, v in item.items():
                    if isinstance(v, str):
                        print(f"  {k} len={len(v)}, start={v[:100]!r}")
            else:
                print(f"Item {idx}: {type(item)}")
    elif isinstance(c, str):
        print("String length:", len(c))
