# -*- coding: utf-8 -*-
import json
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

path = 'C:/Users/niron/.gemini/antigravity-ide/brain/ebe55076-e47d-47a4-a272-a0c82e56bdbe/.system_generated/logs/transcript_full.jsonl'

with open(path, 'r', encoding='utf-8') as f:
    for line in f:
        d = json.loads(line)
        if d.get('type') == 'USER_INPUT':
            content = d.get('content', '')
            if isinstance(content, list):
                # May contain text parts
                text_parts = []
                for p in content:
                    if isinstance(p, dict) and 'text' in p:
                        text_parts.append(p['text'])
                    elif isinstance(p, str):
                        text_parts.append(p)
                full_text = '\n'.join(text_parts)
            else:
                full_text = str(content)
            
            with open('scratch/full_user_input.txt', 'w', encoding='utf-8') as out:
                out.write(full_text)
            print(f"Wrote scratch/full_user_input.txt, length: {len(full_text)} chars")
            break
