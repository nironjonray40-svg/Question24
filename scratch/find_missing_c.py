import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/import_abar_asibo.py', 'r', encoding='utf-8') as f:
    text = f.read()

pattern = r'\{[^{}]*\}'
matches = re.findall(pattern, text)
print(f"Total dict matches: {len(matches)}")
for i, m in enumerate(matches):
    if '"stem":' in m:
        for opt in ['"a":', '"b":', '"c":', '"d":', '"ans":']:
            if opt not in m:
                print(f"Item {i+1} missing {opt}:\n{m}\n")
