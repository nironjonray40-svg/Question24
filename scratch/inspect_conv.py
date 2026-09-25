import json, sys
sys.stdout.reconfigure(encoding='utf-8')

p = r"C:\Users\niron\.gemini\antigravity-ide\brain\464a2d2b-00d7-4441-93b8-8cfd3e0a95c4\.system_generated\logs\transcript.jsonl"
with open(p, 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        data = json.loads(line)
        stype = data.get('type')
        status = data.get('status')
        print(f"Step {i}: type={stype}, status={status}")
        content = data.get('content', '')
        if stype == 'PLANNER_RESPONSE' and content:
            print("Response excerpt:", content[:400].replace('\n', ' '))
        elif stype == 'USER_INPUT':
            print("User input:", content[:200].replace('\n', ' '))
