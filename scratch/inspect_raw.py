import pypdf
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
conv_id = '464a2d2b-00d7-4441-93b8-8cfd3e0a95c4'
folder = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.user_uploaded')
path = os.path.join(folder, 'media_1790272536986.pdf')

reader = pypdf.PdfReader(path)
page = reader.pages[0]

def visitor_body(text, cm, tm, fontDict, fontSize):
    if text.strip():
        # print text and font info
        pass

# Let's inspect raw text of page 0
raw = page.extract_text()
print("Raw characters and their unicodes for first 100 chars:")
for ch in raw[:100]:
    print(f"{ch} -> U+{ord(ch):04X}")
