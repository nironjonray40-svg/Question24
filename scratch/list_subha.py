import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/subha_questions_dump.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Total Short Questions: {len(data['shorts'])}")
for i, s in enumerate(data['shorts']):
    print(f"[{i+1}] ID: {s['id']} | Q: {s['question']}")

print(f"\nTotal Creative Questions: {len(data['cqs'])}")
for i, c in enumerate(data['cqs']):
    print(f"\n==========================================")
    print(f"[{i+1}] CQ ID: {c['id']}")
    print(f"উদ্দীপক: {c['stem']}")
    print(f"ক) {c['ka']}")
    print(f"খ) {c['kha']}")
    print(f"গ) {c['ga']}")
    print(f"ঘ) {c['gha']}")
