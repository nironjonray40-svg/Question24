import json, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\niron\.gemini\antigravity-ide\brain\464a2d2b-00d7-4441-93b8-8cfd3e0a95c4\.system_generated\logs\transcript_full.jsonl"
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i in (67, 68, 69, 70):
            d = json.loads(line)
            print(f"=== Step {i} ({d.get('type')}) ===")
            c = d.get('content')
            if c:
                print(f"Content length: {len(c)}")
                print(c[:500])
            t = d.get('tool_calls')
            if t:
                print(f"Tool calls: {t}")
