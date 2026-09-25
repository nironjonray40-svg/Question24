import json, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\niron\.gemini\antigravity-ide\brain\fddb5b1d-518d-47a1-9413-cdd80e0b7328\.system_generated\logs\transcript_full.jsonl'
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        if i == 0:
            print("Step 0 keys:", data.keys())
            for k in data:
                if k != 'content':
                    print(k, data[k])
            print("Step 0 content:", repr(data['content']))
