import pypdf
import sys

sys.stdout.reconfigure(encoding='utf-8')

reader = pypdf.PdfReader(r'C:\Users\niron\.gemini\antigravity-ide\brain\fddb5b1d-518d-47a1-9413-cdd80e0b7328\.user_uploaded\media_1790318315290.pdf')
print("Page 1 full extracted text:")
print(reader.pages[0].extract_text())
