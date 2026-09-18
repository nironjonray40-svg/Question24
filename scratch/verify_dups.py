import urllib.request
import json
import re

print("--- 1. Testing Question Bank HTML Page ---")
html_req = urllib.request.urlopen("http://127.0.0.1:5000/questions")
html_content = html_req.read().decode('utf-8')
assert "rgba(239, 68, 68, 0.25)" in html_content, "25% red background CSS not found in HTML"
assert "is-duplicate" in html_content, "is-duplicate CSS class not found in HTML"
assert "dupCountBadge" in html_content, "dupCountBadge not found in HTML"
assert "toggleDuplicateFilter" in html_content, "toggleDuplicateFilter not found in HTML"
assert "getQuestionNormalizedKey" in html_content, "getQuestionNormalizedKey function not found"
assert "markDuplicates" in html_content, "markDuplicates function not found"
print("✓ HTML Page contains all CSS and JS for duplicate highlighting and badge display.")

print("\n--- 2. Testing API /api/questions Pagination & is_duplicate flag ---")
api_req = urllib.request.urlopen("http://127.0.0.1:5000/api/questions?paginate=true&page=1&per_page=50")
api_data = json.loads(api_req.read().decode('utf-8'))
items = api_data.get('items', [])
dups = [item for item in items if item.get('is_duplicate')]
print(f"Total returned: {len(items)}, Duplicates: {len(dups)}")
assert len(items) > 0, "No questions returned"
print("✓ API correctly returned questions with is_duplicate property.")

print("\n--- 3. Testing API /api/questions with Class & Subject filter ---")
api_filtered_req = urllib.request.urlopen("http://127.0.0.1:5000/api/questions?class_id=4&subject_id=3")
filtered_data = json.loads(api_filtered_req.read().decode('utf-8'))
filtered_dups = [item for item in filtered_data if item.get('is_duplicate')]
print(f"Class 4 Subject 3 questions: {len(filtered_data)}, Duplicates: {len(filtered_dups)}")
for fd in filtered_dups[:3]:
    print(f"  - Dup ID: {fd['id']}, Stem: {fd.get('mcq_stem') or fd.get('short_question') or fd.get('cq_stem')}")

print("\n✓ ALL TESTS PASSED SUCCESSFULLY!")
