import os
import sys

# Force UTF-8 encoding for standard output and error on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import time
import threading
import webbrowser

def open_browser():
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

def print_banner():
    # ANSI color codes for sleek terminal look
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    # Enable ANSI escape sequences on Windows
    os.system("")

    print(f"{CYAN}{BOLD}")
    print("=" * 72)
    print("      ★ আলহেরা এডুকেয়ার হোম (AL-HERA EDUCARE HOME) ★")
    print("        প্রশ্ন ব্যাংক ও প্রশ্নপত্র জেনারেটর ম্যানেজমেন্ট সিস্টেম")
    print("=" * 72)
    print(f"{RESET}")
    print(f"  {GREEN}●{RESET} {BOLD}লোকাল সার্ভার লিঙ্ক  :{RESET} {CYAN}http://127.0.0.1:5000{RESET}")
    print(f"  {GREEN}●{RESET} {BOLD}ব্রাউজার এক্সেস      :{RESET} {CYAN}http://localhost:5000{RESET}")
    print(f"  {YELLOW}●{RESET} {BOLD}স্বয়ংক্রিয় ব্রাউজার   :{RESET} ব্রাউজারে সাইটটি ওপেন হচ্ছে...")
    print(f"  {YELLOW}●{RESET} {BOLD}সার্ভার বন্ধ করতে     :{RESET} কিবোর্ডে {BOLD}[Ctrl + C]{RESET} চাপুন")
    print(f"{CYAN}" + "-" * 72 + f"{RESET}\n")

if __name__ == '__main__':
    print_banner()
    
    # Check dependencies
    try:
        import flask
        import flask_sqlalchemy
    except ImportError:
        print("[!] প্রয়োজনীয় প্যাকেজ ইনস্টল করা হচ্ছে...")
        os.system(f'"{sys.executable}" -m pip install -r requirements.txt')
        print("[✓] প্যাকেজ ইনস্টলেশন সম্পন্ন!\n")

    # Start browser opener thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run app
    from app import app, seed_database
    seed_database()
    app.run(debug=True, port=5000, use_reloader=False)
