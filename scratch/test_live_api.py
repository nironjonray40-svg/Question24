import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

connected = False
for port in [5000, 5001, 8000, 8080]:
    try:
        url = f'http://127.0.0.1:{port}/api/settings/chapters?class_id=3&subject_id=47'
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            print(f"Port {port} connected! Found {len(data)} chapters.")
            for ch in data:
                if any(x in ch['title'] for x in ['বাবুরের', 'নারী', 'আবার আসিব', 'রূপাই']):
                    print(f"  • {ch['title']} (ID: {ch['id']}): {ch['question_count']} টি প্রশ্ন")
            connected = True
            break
    except Exception as e:
        pass

if not connected:
    print("Could not connect to localhost ports 5000, 5001, 8000, 8080")
