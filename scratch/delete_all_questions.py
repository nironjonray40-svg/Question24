import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, ClassLevel, Subject, Chapter, Topic, User, SchoolProfile

with app.app_context():
    count_before = Question.query.count()
    print(f"Questions before deletion: {count_before}")
    
    # Delete all records from Question table
    deleted_rows = Question.query.delete()
    db.session.commit()
    
    count_after = Question.query.count()
    print(f"Questions after deletion: {count_after}")
    print(f"Deleted successfully: {deleted_rows} questions")
    
    # Check other tables to make sure they are intact
    print("\n--- Intact Database Summary ---")
    print(f"● Classes: {ClassLevel.query.count()}")
    print(f"● Subjects: {Subject.query.count()}")
    print(f"● Chapters: {Chapter.query.count()}")
    print(f"● Topics: {Topic.query.count()}")
    print(f"● Questions: {Question.query.count()}")
    print(f"● Users: {User.query.count()}")
