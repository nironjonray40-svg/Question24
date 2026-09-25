import json, sys

p = r"C:\Users\niron\.gemini\antigravity-ide\brain\464a2d2b-00d7-4441-93b8-8cfd3e0a95c4\.system_generated\logs\transcript_full.jsonl"
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if i in (66, 67, 68):
            data = json.loads(line)
            print(f"=== Step {i} ({data.get('type')}) ===")
            print(data.get('content', '')[:1000])
