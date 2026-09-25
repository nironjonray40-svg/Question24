import pypdf
import sys, glob, os

sys.stdout.reconfigure(encoding='utf-8')

folder = r'C:\Users\niron\.gemini\antigravity-ide\brain\fddb5b1d-518d-47a1-9413-cdd80e0b7328\.user_uploaded'
pdfs = sorted(glob.glob(os.path.join(folder, '*.pdf')))

for p in pdfs:
    print(f"\nChecking {os.path.basename(p)}:")
    reader = pypdf.PdfReader(p)
    print(f"Num pages: {len(reader.pages)}")
    first_page_text = reader.pages[0].extract_text()
    print("Page 1 text sample (first 300 chars):")
    print(first_page_text[:300] if first_page_text else "[NO TEXT EXTRACTED - SCANNED]")
