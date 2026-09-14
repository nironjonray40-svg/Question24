import sys
# Generate test html to verify SVG and CSS bubbles
html = """<!DOCTYPE html>
<html lang="bn">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Tiro+Bangla:ital@0;1&family=Noto+Serif+Bengali:wght@400;600;700;800&family=Hind+Siliguri:wght@400;600;700&display=swap" rel="stylesheet">
<style>
body { font-family: 'Tiro Bangla', 'Noto Serif Bengali', serif; padding: 40px; background: #fff; }
.test-row { display: flex; align-items: center; gap: 20px; margin-bottom: 20px; }
.svg-bubble { display: inline-block; vertical-align: middle; }
</style>
</head>
<body>
<h2>Encircled Bangla Options Test (ক, খ, গ, ঘ)</h2>
<div class="test-row">
    <span>SVG Approach (Size 18x18):</span>
    <svg width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="8.5" fill="#ffffff" stroke="#000000" stroke-width="1.3"/>
        <text x="10" y="10.5" text-anchor="middle" dominant-baseline="central" font-family="'Noto Serif Bengali', serif" font-size="11" font-weight="700" fill="#000000">ক</text>
    </svg>
    <svg width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="8.5" fill="#ffffff" stroke="#000000" stroke-width="1.3"/>
        <text x="10" y="10.5" text-anchor="middle" dominant-baseline="central" font-family="'Noto Serif Bengali', serif" font-size="11" font-weight="700" fill="#000000">খ</text>
    </svg>
    <svg width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="8.5" fill="#ffffff" stroke="#000000" stroke-width="1.3"/>
        <text x="10" y="10.5" text-anchor="middle" dominant-baseline="central" font-family="'Noto Serif Bengali', serif" font-size="11" font-weight="700" fill="#000000">গ</text>
    </svg>
    <svg width="20" height="20" viewBox="0 0 20 20">
        <circle cx="10" cy="10" r="8.5" fill="#ffffff" stroke="#000000" stroke-width="1.3"/>
        <text x="10" y="10.5" text-anchor="middle" dominant-baseline="central" font-family="'Noto Serif Bengali', serif" font-size="11" font-weight="700" fill="#000000">ঘ</text>
    </svg>
</div>
</body>
</html>
"""
with open('scratch/test_bubble.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Wrote test_bubble.html successfully')
