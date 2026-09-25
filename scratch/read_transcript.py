import json, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r'C:\Users\niron\.gemini\antigravity-ide\brain\fddb5b1d-518d-47a1-9413-cdd80e0b7328\.system_generated\logs\transcript_full.jsonl'
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        if i >= 148 and (data.get('type') in ['USER_INPUT', 'PLANNER_RESPONSE'] or i in [180, 190, 200, 210, 220]):
            print(f"=== STEP {i} ({data.get('type')}) ===")
            content = str(data.get('content', ''))
            print(content[:600])

