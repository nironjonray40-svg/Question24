import urllib.request, json

req = urllib.request.urlopen('http://127.0.0.1:5000/api/questions?paginate=true&page=1&per_page=50')
data = json.loads(req.read().decode('utf-8'))
items = data.get('items', [])
dups = [item for item in items if item.get('is_duplicate')]
print(f"Total items returned: {len(items)}, Duplicates found: {len(dups)}")
for d in dups[:5]:
    stem = d.get('mcq_stem') or d.get('short_question') or d.get('cq_stem') or ''
    print(f"ID: {d['id']}, Type: {d['question_type']}, Stem: {stem[:60]}")
