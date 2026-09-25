import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
p = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript_full.jsonl')

with open(p, 'r', encoding='utf-8') as f:
    text = f.read()
    print("Full file length:", len(text))
    print("'==Start of PDF==' in text:", '==Start of PDF==' in text)
    print("'==Start of OCR' in text:", '==Start of OCR' in text)
    print("'একুশের গান' in text:", 'একুশের গান' in text)
    print("'সুকান্ত' in text:", 'সুকান্ত' in text)
