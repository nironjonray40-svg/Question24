import pypdf
import os, sys

conv_id = '59f6a4b1-d9a9-4f4b-8004-9460809e7d05'
pdf_path = os.path.expanduser(f'~/.gemini/antigravity-ide/brain/{conv_id}/.user_uploaded/media_1790302290621.pdf')

reader = pypdf.PdfReader(pdf_path)
page = reader.pages[23] # 24th page (0-indexed 23)

print("Images on page 24:", len(page.images))
for i, img in enumerate(page.images):
    name = f"scratch/page24_img_{i}.{img.name.split('.')[-1]}"
    with open(name, "wb") as f:
        f.write(img.data)
    print(f"Saved {name}, size={len(img.data)} bytes, format={img.name}")
