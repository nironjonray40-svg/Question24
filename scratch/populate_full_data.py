import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db, seed_database
from models import ClassLevel, Subject, Chapter, Topic, Question, User, SchoolProfile, ExamPaper

print("=== POPULATING NCTB CURRICULUM AND QUESTIONS ===")

with app.app_context():
    seed_database()
    print("✓ seed_database() executed.")
    
    classes_count = ClassLevel.query.count()
    subjects_count = Subject.query.count()
    chapters_count = Chapter.query.count()
    topics_count = Topic.query.count()
    print(f"Classes: {classes_count}, Subjects: {subjects_count}, Chapters: {chapters_count}, Topics: {topics_count}")

# Now execute the specific question import scripts
import_scripts = [
    'scratch/update_subha_verified.py',
    'scratch/import_boi_pora.py',
    'scratch/import_polli_sahitya.py',
    'scratch/import_abhagir_sworgo.py',
    'scratch/import_abhagir_sworgo_cq_short.py',
    'scratch/import_short_cq.py',
    'scratch/import_bhab_o_kaj.py'
]

import subprocess

for script in import_scripts:
    if os.path.exists(script):
        print(f"\n--- Running {script} ---")
        try:
            res = subprocess.run([sys.executable, script], capture_output=True, text=True, encoding='utf-8', errors='replace')
            print(res.stdout)
            if res.stderr:
                print("Stderr:", res.stderr)
            print(f"✓ {script} completed with returncode {res.returncode}")
        except Exception as e:
            print(f"Error in {script}: {e}")

with app.app_context():
    q_total = Question.query.count()
    q_mcq = Question.query.filter_by(question_type='mcq').count()
    q_cq = Question.query.filter_by(question_type='cq').count()
    q_short = Question.query.filter_by(question_type='short').count()
    users_total = User.query.count()
    
    print("\n==============================================")
    print("FINAL DATABASE VERIFICATION REPORT")
    print("==============================================")
    print(f"● Total Classes: {ClassLevel.query.count()}")
    print(f"● Total Subjects: {Subject.query.count()}")
    print(f"● Total Chapters: {Chapter.query.count()}")
    print(f"● Total Topics: {Topic.query.count()}")
    print(f"● Total Questions: {q_total} (MCQ: {q_mcq}, CQ: {q_cq}, Short: {q_short})")
    print(f"● Total Users: {users_total}")
    print("==============================================")
