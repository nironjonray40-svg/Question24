import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

path = 'C:/Users/niron/.gemini/antigravity-ide/brain/ebe55076-e47d-47a4-a272-a0c82e56bdbe/.system_generated/logs/transcript_full.jsonl'
with open(path, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        d = json.loads(line)
        src = d.get('source')
        tp = d.get('type')
        print(f"Line {i}: source={src}, type={tp}")
        c = d.get('content')
        if isinstance(c, list):
            print(f"  content is list of {len(c)}")
            for j, elem in enumerate(c):
                if isinstance(elem, dict):
                    print(f"    item {j}: keys={list(elem.keys())}")
                    if 'text' in elem:
                        print(f"      text prefix: {elem['text'][:80]!r}")
        elif isinstance(c, str):
            print(f"  content str len={len(c)}, prefix={c[:80]!r}")
