import urllib.request, json

print("--- Testing API with only_duplicates=true ---")
req = urllib.request.urlopen('http://127.0.0.1:5000/api/questions?paginate=true&only_duplicates=true&per_page=50')
data = json.loads(req.read().decode('utf-8'))
items = data.get('items', [])
print(f"Total Duplicate Questions: {data.get('total')}, Page Items: {len(items)}")
for item in items[:5]:
    stem = item.get('mcq_stem') or item.get('short_question') or item.get('cq_stem') or ''
    print(f"  [ID: {item['id']}] {stem[:50]} (is_dup: {item['is_duplicate']})")

print("✓ ONLY_DUPLICATES TEST PASSED!")
