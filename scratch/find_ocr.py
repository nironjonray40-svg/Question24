import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
log_file = os.path.expanduser('~/.gemini/antigravity-ide/brain/464a2d2b-00d7-4441-93b8-8cfd3e0a95c4/.system_generated/logs/transcript_full.jsonl')

with open(log_file, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '==Start of OCR' in line:
            obj = json.loads(line)
            print(f'Line {idx}: type={obj.get("type")}, keys={list(obj.keys())}')
            for k in obj:
                val = str(obj[k])
                if '==Start of OCR' in val:
                    print(f'  Found in field "{k}": length {len(val)}')
