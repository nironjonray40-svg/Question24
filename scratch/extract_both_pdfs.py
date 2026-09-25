import json, sys, os
sys.stdout.reconfigure(encoding='utf-8')

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
p = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.system_generated/logs/transcript_full.jsonl')

with open(p, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        if '==Start of PDF==' in line:
            obj = json.loads(line)
            print(f"Line {idx}: type={obj.get('type')}, status={obj.get('status')}")
            for k in obj:
                val = str(obj[k])
                if '==Start of PDF==' in val:
                    print(f"  Found in field '{k}', length {len(val)}")
                    # Split into the two PDFs
                    pdf_parts = val.split('==Start of PDF==')
                    print(f"  Number of PDF parts: {len(pdf_parts)-1}")
                    for p_num, part in enumerate(pdf_parts[1:], 1):
                        content = part.split('==End of PDF==')[0]
                        out_path = f"scratch/pdf_{p_num}_ocr.txt"
                        with open(out_path, 'w', encoding='utf-8') as out:
                            out.write(content)
                        print(f"  Wrote PDF {p_num} to {out_path} ({len(content)} chars)")
