import sqlite3
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

for path in ['instance/question_bank.db', 'instance/backups/app_pre_shuffle.db', 'question_bank.db', 'instance/app.db']:
    if os.path.exists(path):
        print(f"\n--- Checking {path} (Size: {os.path.getsize(path)} bytes) ---")
        try:
            conn = sqlite3.connect(path)
            cur = conn.cursor()
            tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
            print(f"Tables: {tables}")
            for t in ['users', 'questions', 'class_levels', 'subjects', 'chapters', 'topics', 'exam_papers', 'school_profiles']:
                if t in tables:
                    count = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
                    print(f"  - {t}: {count} rows")
            if 'users' in tables:
                users = cur.execute("SELECT id, name, mobile, role, is_admin FROM users").fetchall()
                print(f"  - User records: {users}")
        except Exception as e:
            print(f"  Error: {e}")
