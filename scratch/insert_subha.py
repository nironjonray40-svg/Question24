import os
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/..'))

from app import app, db
from models import Question, ClassLevel, Subject, Chapter, Topic
from scratch.subha_data import mcqs_data, short_questions_data, cqs_data

with app.app_context():
    # Verify hierarchy
    class_obj = ClassLevel.query.filter(ClassLevel.name.like('%৯ম-১০ম%')).first()
    if not class_obj:
        class_obj = ClassLevel.query.get(4)
    print("Class:", class_obj.id, class_obj.name)
    
    subject_obj = Subject.query.filter_by(class_id=class_obj.id, name='বাংলা সাহিত্য').first()
    if not subject_obj:
        subject_obj = Subject.query.filter(Subject.class_id==class_obj.id, Subject.name.like('%বাংলা%')).first()
    print("Subject:", subject_obj.id, subject_obj.name)
    
    chapter_obj = Chapter.query.filter(Chapter.subject_id==subject_obj.id, Chapter.title.like('%সুভা%')).first()
    print("Chapter:", chapter_obj.id, chapter_obj.title, chapter_obj.chapter_no)
    
    topic_obj = Topic.query.filter_by(chapter_id=chapter_obj.id).first()
    if not topic_obj:
        topic_obj = Topic(chapter_id=chapter_obj.id, title='সাধারণ আলোচনা ও প্রশ্নোত্তর', order_num=1)
        db.session.add(topic_obj)
        db.session.commit()
    print("Topic:", topic_obj.id, topic_obj.title)
    
    class_id = class_obj.id
    subject_id = subject_obj.id
    chapter_id = chapter_obj.id
    topic_id = topic_obj.id
    
    # 1. Insert MCQs
    mcq_count = 0
    for item in mcqs_data:
        opts = item.get('options', ['', '', '', ''])
        q = Question(
            class_id=class_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
            question_type='mcq',
            difficulty=item.get('difficulty', 'medium'),
            marks=1.0,
            mcq_stem=item['stem'],
            option_a=opts[0] if len(opts) > 0 else '',
            option_b=opts[1] if len(opts) > 1 else '',
            option_c=opts[2] if len(opts) > 2 else '',
            option_d=opts[3] if len(opts) > 3 else '',
            correct_option=item.get('correct', 'ক'),
            explanation=item.get('explanation')
        )
        db.session.add(q)
        mcq_count += 1
        
    # 2. Insert Short Questions
    short_count = 0
    for item in short_questions_data:
        q = Question(
            class_id=class_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
            question_type='short',
            difficulty=item.get('difficulty', 'medium'),
            marks=2.0,
            short_question=item['q'],
            short_answer=item.get('a', '')
        )
        db.session.add(q)
        short_count += 1
        
    # 3. Insert Creative Questions (CQs)
    cq_count = 0
    for item in cqs_data:
        q = Question(
            class_id=class_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
            question_type='cq',
            difficulty=item.get('difficulty', 'medium'),
            marks=10.0,
            cq_stem=item['stem'],
            cq_sub_ka=item['ka'],
            cq_sub_kha=item['kha'],
            cq_sub_ga=item['ga'],
            cq_sub_gha=item['gha'],
            cq_solution=item.get('solution')
        )
        db.session.add(q)
        cq_count += 1
        
    db.session.commit()
    print(f"Successfully inserted: {mcq_count} MCQs, {short_count} Short Questions, {cq_count} CQs (Total: {mcq_count + short_count + cq_count})")
