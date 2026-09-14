from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class ClassLevel(db.Model):
    __tablename__ = 'class_levels'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)  # e.g., "৬ষ্ঠ শ্রেণি (Class 6)" or "Class 10"
    code = db.Column(db.String(20), nullable=True)                 # e.g., "6", "10"
    order_num = db.Column(db.Integer, default=0)
    
    subjects = db.relationship('Subject', backref='class_level', cascade="all, delete-orphan", lazy=True)
    questions = db.relationship('Question', backref='class_level', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code,
            'subject_count': len(self.subjects)
        }

    def __repr__(self):
        return f'<ClassLevel {self.name}>'


class Subject(db.Model):
    __tablename__ = 'subjects'
    __table_args__ = (
        db.Index('idx_subjects_class_id', 'class_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class_levels.id'), nullable=False)
    name = db.Column(db.String(150), nullable=False)  # e.g., "বাংলা ১ম পত্র", "গণিত"
    code = db.Column(db.String(30), nullable=True)    # e.g., "101", "109"
    
    chapters = db.relationship('Chapter', backref='subject', cascade="all, delete-orphan", lazy=True)
    questions = db.relationship('Question', backref='subject', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'class_id': self.class_id,
            'name': self.name,
            'code': self.code,
            'chapter_count': len(self.chapters)
        }

    def __repr__(self):
        return f'<Subject {self.name}>'


class Chapter(db.Model):
    __tablename__ = 'chapters'
    __table_args__ = (
        db.Index('idx_chapters_subject_id', 'subject_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    chapter_no = db.Column(db.String(50), nullable=True)  # e.g., "১ম অধ্যায়", "অধ্যায় ১"
    title = db.Column(db.String(200), nullable=False)     # e.g., "বাস্তব সংখ্যা", "মানুষ মুহম্মদ (সঃ)"
    
    topics = db.relationship('Topic', backref='chapter', cascade="all, delete-orphan", lazy=True)
    questions = db.relationship('Question', backref='chapter', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'subject_id': self.subject_id,
            'chapter_no': self.chapter_no,
            'title': self.title,
            'display_name': f"{self.chapter_no + ': ' if self.chapter_no else ''}{self.title}",
            'topic_count': len(self.topics)
        }

    def __repr__(self):
        return f'<Chapter {self.chapter_no}: {self.title}>'


class Topic(db.Model):
    __tablename__ = 'topics'
    __table_args__ = (
        db.Index('idx_topics_chapter_id', 'chapter_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)  # e.g., "পাঠ ১: মূলদ ও অমূলদ সংখ্যা"
    order_num = db.Column(db.Integer, default=0)
    
    questions = db.relationship('Question', backref='topic', cascade="all, delete-orphan", lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'chapter_id': self.chapter_id,
            'title': self.title,
            'question_count': len(self.questions)
        }

    def __repr__(self):
        return f'<Topic {self.title}>'


class Question(db.Model):
    __tablename__ = 'questions'
    __table_args__ = (
        db.Index('idx_questions_hierarchy', 'class_id', 'subject_id', 'chapter_id'),
        db.Index('idx_questions_type', 'question_type'),
        db.Index('idx_questions_created_at', 'created_at'),
        db.Index('idx_questions_topic_id', 'topic_id'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey('class_levels.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'), nullable=False)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=True)
    
    # Types: 'mcq' (বহুনির্বাচনি), 'short' (সংক্ষিপ্ত প্রশ্ন), 'cq' (সৃজনশীল প্রশ্ন)
    question_type = db.Column(db.String(20), nullable=False)
    difficulty = db.Column(db.String(20), default='medium')  # 'easy', 'medium', 'hard'
    marks = db.Column(db.Float, default=1.0)
    
    # MCQ fields (বহুনির্বাচনি প্রশ্ন)
    mcq_stem = db.Column(db.Text, nullable=True)          # Question stem / stimulus
    option_a = db.Column(db.Text, nullable=True)          # ক
    option_b = db.Column(db.Text, nullable=True)          # খ
    option_c = db.Column(db.Text, nullable=True)          # গ
    option_d = db.Column(db.Text, nullable=True)          # ঘ
    correct_option = db.Column(db.String(10), nullable=True) # 'a', 'b', 'c', 'd' or 'ক', 'খ', 'গ', 'ঘ'
    explanation = db.Column(db.Text, nullable=True)       # ব্যাখ্যা
    
    # Short Question fields (সংক্ষিপ্ত প্রশ্ন)
    short_question = db.Column(db.Text, nullable=True)
    short_answer = db.Column(db.Text, nullable=True)      # Model answer / Rubrics
    
    # Creative Question / CQ fields (সৃজনশীল প্রশ্ন)
    cq_stem = db.Column(db.Text, nullable=True)           # উদ্দীপক / Scenario
    cq_sub_ka = db.Column(db.Text, nullable=True)         # ক (জ্ঞানমূলক - ১ নম্বর)
    cq_sub_kha = db.Column(db.Text, nullable=True)        # খ (অনুধাবনমূলক - ২ নম্বর)
    cq_sub_ga = db.Column(db.Text, nullable=True)         # গ (প্রয়োগমূলক - ৩ নম্বর)
    cq_sub_gha = db.Column(db.Text, nullable=True)        # ঘ (উচ্চতর দক্ষতামূলক - ৪ নম্বর)
    cq_solution = db.Column(db.Text, nullable=True)       # সমাধান / নির্দেশনা
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        data = {
            'id': self.id,
            'class_id': self.class_id,
            'class_name': self.class_level.name if self.class_level else '',
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'chapter_id': self.chapter_id,
            'chapter_title': self.chapter.title if self.chapter else '',
            'chapter_no': self.chapter.chapter_no if self.chapter else '',
            'topic_id': self.topic_id,
            'topic_title': self.topic.title if self.topic else '',
            'question_type': self.question_type,
            'difficulty': self.difficulty,
            'marks': self.marks,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }
        
        if self.question_type == 'mcq':
            data.update({
                'mcq_stem': self.mcq_stem,
                'option_a': self.option_a,
                'option_b': self.option_b,
                'option_c': self.option_c,
                'option_d': self.option_d,
                'correct_option': self.correct_option,
                'explanation': self.explanation
            })
        elif self.question_type == 'short':
            data.update({
                'short_question': self.short_question,
                'short_answer': self.short_answer
            })
        elif self.question_type == 'cq':
            data.update({
                'cq_stem': self.cq_stem,
                'cq_sub_ka': self.cq_sub_ka,
                'cq_sub_kha': self.cq_sub_kha,
                'cq_sub_ga': self.cq_sub_ga,
                'cq_sub_gha': self.cq_sub_gha,
                'cq_solution': self.cq_solution
            })
            
        return data

    def __repr__(self):
        return f'<Question {self.id} ({self.question_type})>'


class ExamPaper(db.Model):
    __tablename__ = 'exam_papers'
    __table_args__ = (
        db.Index('idx_exam_papers_created_at', 'created_at'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)             # e.g., "অর্ধ-বার্ষিক পরীক্ষা ২০২৬"
    school_name = db.Column(db.String(255), default="আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়")
    exam_name = db.Column(db.String(150), default="অর্ধ-বার্ষিক পরীক্ষা")
    class_id = db.Column(db.Integer, db.ForeignKey('class_levels.id'), nullable=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=True)
    time_allowed = db.Column(db.String(100), default="২ ঘণ্টা ৩০ মিনিট")
    total_marks = db.Column(db.Float, default=100.0)
    instructions = db.Column(db.Text, default="[সকল প্রশ্নের উত্তর দেওয়া আবশ্যক। ডান পাশের সংখ্যা প্রশ্নের পূর্ণমান নির্দেশক]")
    
    # Store selected questions payload (JSON text: IDs, sections, order, marks overrides)
    questions_json = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    class_level = db.relationship('ClassLevel', backref='exam_papers', lazy=True)
    subject = db.relationship('Subject', backref='exam_papers', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'school_name': self.school_name,
            'exam_name': self.exam_name,
            'class_id': self.class_id,
            'class_name': self.class_level.name if self.class_level else '',
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else '',
            'time_allowed': self.time_allowed,
            'total_marks': self.total_marks,
            'instructions': self.instructions,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }

    def __repr__(self):
        return f'<ExamPaper {self.title}>'
