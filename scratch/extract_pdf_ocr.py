import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

transcript_path = r'C:\Users\niron\.gemini\antigravity-ide\brain\199da8f8-d732-48d6-b058-5f2346c329f1\.system_generated\logs\transcript_full.jsonl'

with open(transcript_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Start of OCR' in line or 'বহুনির্বাচনি অংশ' in line or 'অতিথির স্মৃতি' in line:
        data = json.loads(line)
        c = data.get('content', '')
        print(f"Match at line {i}, type={data.get('type')}, len={len(c)}")
        with open(r'c:\Users\niron\OneDrive\Desktop\Question\scratch\raw_pdf_text.txt', 'w', encoding='utf-8') as out:
            out.write(c)
        print("Written to scratch/raw_pdf_text.txt")
        break
