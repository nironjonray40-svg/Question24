import os
import io
import csv
import json
import time
import re
from markupsafe import Markup
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Response, make_response
from sqlalchemy import event
from sqlalchemy.engine import Engine
from models import db, ClassLevel, Subject, Chapter, Topic, Question, ExamPaper, SchoolProfile

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bangladesh-school-question-bank-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///question_bank.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# SQLITE ULTRA HIGH-SPEED ENGINE TUNING
# ==========================================
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Configures SQLite for maximum write & read throughput:
    - WAL Mode: Non-blocking parallel reads/writes
    - SYNCHRONOUS NORMAL: 10x-50x faster write commits
    - CACHE_SIZE: 64MB RAM page cache
    - TEMP_STORE: In-memory temp tables & sorting
    - MMAP_SIZE: 256MB memory mapped I/O
    - BUSY_TIMEOUT: 30s lock wait prevention
    """
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")
        cursor.execute("PRAGMA busy_timeout=30000")
        cursor.close()
    except Exception as e:
        print(f"[SQLITE TUNING NOTE] {e}")

db.init_app(app)

# Helper function to get or initialize SchoolProfile singleton
def get_or_create_school_profile():
    try:
        profile = SchoolProfile.query.first()
        if not profile:
            profile = SchoolProfile(
                school_name_bn="আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়",
                school_name_en="Al Hera Educare Home High School",
                eiin_number="123456",
                school_code="4501",
                center_code="102",
                board_name="ঢাকা",
                institute_type="উচ্চ বিদ্যালয়",
                shift="উভয় শিফট",
                estd_year="১৯৯৫",
                motto="জ্ঞানই শক্তি, শিক্ষাই আলো",
                address="উপজেলা রোড, সদর",
                post_office="প্রধান ডাকঘর",
                post_code="১০০০",
                upazila="সদর",
                district="ঢাকা",
                division="ঢাকা",
                phone="০১৭০০-০০০০০০",
                email="info@alheraschool.edu.bd",
                website="www.alheraschool.edu.bd",
                headmaster_name="মো: নজরুল ইসলাম",
                headmaster_title="প্রধান শিক্ষক",
                headmaster_phone="০১৮০০-০০০০০০",
                headmaster_email="headmaster@alheraschool.edu.bd",
                signature_text="প্রধান শিক্ষক / পরীক্ষা নিয়ন্ত্রক",
                logo_path="/static/img/logo.png",
                default_exam_header="অর্ধ-বার্ষিক পরীক্ষা - ২০২৬",
                default_time_allowed="২ ঘণ্টা ৩০ মিনিট",
                default_instructions="[সকল প্রশ্নের উত্তর দেওয়া আবশ্যক। ডান পাশের সংখ্যা প্রশ্নের পূর্ণমান নির্দেশক]",
                watermark_text="আলহেরা এডুকেয়ার হোম"
            )
            db.session.add(profile)
            db.session.commit()
        return profile
    except Exception as e:
        print(f"[SCHOOL PROFILE INIT ERROR] {e}")
        return None

# Helper function to convert English digits to Bengali numerals if needed
def to_bangla_number(number):
    if number is None:
        return ""
    bangla_digits = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯', '.': '.'}
    return ''.join(bangla_digits.get(char, char) for char in str(number))

@app.template_filter('bangla_num')
def bangla_num_filter(s):
    return to_bangla_number(s)

@app.template_filter('with_source_tags')
def with_source_tags_filter(text):
    if not text:
        return ""
    pattern = re.compile(
        r'(\s*[—–-]\s*)?(\[[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|মাদরাসা|স্কুল|বিদ্যালয়|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|জিলা|ক্যান্টনমেন্ট|ল্যাবরেটরি|পাবলিক|বিশ্ববিদ্যালয়|ইনস্টিটিউট|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]|\([^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|মাদরাসা|স্কুল|বিদ্যালয়|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|জিলা)[^\)]*\))',
        re.IGNORECASE
    )
    def repl(m):
        prefix = m.group(1) or ''
        tag = m.group(2) or m.group(0)
        return f'<span class="question-source-tag font-semibold text-slate-700 italic">{prefix}{tag}</span>'
    return Markup(pattern.sub(repl, str(text)))


@app.context_processor
def inject_global_data():
    try:
        classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    except Exception:
        classes = []
    try:
        school_profile = get_or_create_school_profile()
    except Exception:
        school_profile = None
    return dict(global_classes=classes, school_profile=school_profile)


from curriculum_data import seed_nctb_curriculum

def ensure_schema_migrations():
    """Ensure newly added columns like order_num exist in existing SQLite database tables"""
    try:
        with db.engine.connect() as conn:
            # Check subjects table
            res = conn.execute(db.text("PRAGMA table_info(subjects)")).fetchall()
            cols = [r[1] for r in res]
            if 'order_num' not in cols:
                conn.execute(db.text("ALTER TABLE subjects ADD COLUMN order_num INTEGER DEFAULT 0"))
            
            # Check chapters table
            res2 = conn.execute(db.text("PRAGMA table_info(chapters)")).fetchall()
            cols2 = [r[1] for r in res2]
            if 'order_num' not in cols2:
                conn.execute(db.text("ALTER TABLE chapters ADD COLUMN order_num INTEGER DEFAULT 0"))
            conn.commit()
    except Exception as e:
        print(f"[SCHEMA MIGRATION NOTE] {e}")


# ==========================================
# SEED INITIAL DATA (Bangladeshi Curriculum)
# ==========================================
def seed_database():
    with app.app_context():
        db.create_all()
        ensure_schema_migrations()
        # Seed or sync full NCTB 2026 hierarchy (Class -> Subject -> Chapter -> Topic)
        # স্বয়ংক্রিয় ডিফল্ট কারিকুলাম ও শ্রেণি সিডিং বন্ধ রাখা হয়েছে:
        # seed_nctb_curriculum()
        
        # Seed initial sample questions if none exist
        if Question.query.count() == 0:
            print("[INFO] Adding initial sample questions...")
            c9 = ClassLevel.query.filter_by(code="9-10").first()
            if c9:
                s_bangla = Subject.query.filter_by(class_id=c9.id, name="বাংলা ১ম পত্র (সাহিত্য)").first()
                s_math = Subject.query.filter_by(class_id=c9.id, name="সাধারণ গণিত (General Math)").first()
                s_science = Subject.query.filter_by(class_id=c9.id, name="পদার্থবিজ্ঞান (Physics)").first()
                
                ch_shova = Chapter.query.filter_by(subject_id=s_bangla.id, title="সুভা (রবীন্দ্রনাথ ঠাকুর)").first() if s_bangla else None
                ch_algebra = Chapter.query.filter_by(subject_id=s_math.id, title="বীজগাণিতিক রাশি (Algebraic Expressions)").first() if s_math else None
                ch_motion = Chapter.query.filter_by(subject_id=s_science.id, title="গতি (Motion)").first() if s_science else None
                
                t_shova = Topic.query.filter_by(chapter_id=ch_shova.id).first() if ch_shova else None
                t_math = Topic.query.filter_by(chapter_id=ch_algebra.id).first() if ch_algebra else None
                t_phy = Topic.query.filter_by(chapter_id=ch_motion.id).first() if ch_motion else None
                
                samples = []
                if ch_shova:
                    samples.append(Question(
                        class_id=c9.id,
                        subject_id=s_bangla.id,
                        chapter_id=ch_shova.id,
                        topic_id=t_shova.id if t_shova else None,
                        question_type='mcq',
                        difficulty='easy',
                        marks=1.0,
                        mcq_stem='সুভার সাথে কার ঘনিষ্ঠ বন্ধুত্ব ছিল?',
                        option_a='প্রতাপ',
                        option_b='গোঁসাইদের ছোট ছেলে',
                        option_c='সর্বশী ও পাঙ্গুলি নামের দুটি গাভী',
                        option_d='গ্রামের সমবয়সী মেয়েরা',
                        correct_option='গ',
                        explanation='সুভার মূক প্রকৃতির সাথে বোবা প্রাণী দুটি (সর্বশী ও পাঙ্গুলি) অন্তরঙ্গ বন্ধু ছিল।'
                    ))
                    samples.append(Question(
                        class_id=c9.id,
                        subject_id=s_bangla.id,
                        chapter_id=ch_shova.id,
                        topic_id=t_shova.id if t_shova else None,
                        question_type='cq',
                        difficulty='hard',
                        marks=10.0,
                        cq_stem='দশম শ্রেণির ছাত্রী মিতু চোখে দেখে না। কিন্তু তার স্মৃতিশক্তি প্রখর এবং গানের গলা চমৎকার। পরিবারের সদস্যরা তাকে নিয়ে লজ্জিত না হয়ে তার সংগীত চর্চায় সর্বাত্মক সহায়তা করেন। ফলে মিতু জাতীয় পর্যায়ে শ্রেষ্ঠ সংগীতশিল্পী হিসেবে পুরস্কার অর্জন করে।',
                        cq_sub_ka='সুভার পিতার নাম কী?',
                        cq_sub_kha='‘সুভার একটি বিশেষ সুবিধা ছিল’—কথাটি দ্বারা কী বোঝানো হয়েছে?',
                        cq_sub_ga='উদ্দীপকের মিতুর পারিবারিক পরিবেশ ‘সুভা’ গল্পের কোন ভিন্ন দিকটি উন্মোচন করে? ব্যাখ্যা কর।',
                        cq_sub_gha='“মিতু অনুকূল পরিবেশ পেলেও সুভা তা থেকে বঞ্চিত ছিল”—মন্তব্যটি ‘সুভা’ গল্পের আলোকে বিশ্লেষণ কর।',
                        cq_solution='ক) সুভার পিতার নাম বাণীকণ্ঠ।\nখ) অনুধাবনমূলক বিশ্লেষণ।\nগ) উদ্দীপক ও পাঠ্যবইয়ের তুলনামূলক আলোচনা।\nঘ) উচ্চতর দক্ষতামূলক বিশ্লেষণ।'
                    ))
                
                if ch_algebra:
                    samples.append(Question(
                        class_id=c9.id,
                        subject_id=s_math.id,
                        chapter_id=ch_algebra.id,
                        topic_id=t_math.id if t_math else None,
                        question_type='mcq',
                        difficulty='medium',
                        marks=1.0,
                        mcq_stem='x + 1/x = 2 হলে, x³ + 1/x³ এর মান কত?',
                        option_a='0',
                        option_b='2',
                        option_c='4',
                        option_d='8',
                        correct_option='খ',
                        explanation='x³ + 1/x³ = (x + 1/x)³ - 3(x)(1/x)(x + 1/x) = 2³ - 3(2) = 8 - 6 = 2'
                    ))
                    samples.append(Question(
                        class_id=c9.id,
                        subject_id=s_math.id,
                        chapter_id=ch_algebra.id,
                        topic_id=t_math.id if t_math else None,
                        question_type='cq',
                        difficulty='medium',
                        marks=10.0,
                        cq_stem='p = 3 + 2√2 এবং a² - 2√6a + 1 = 0 দুটি বীজগাণিতিক সম্পর্ক।',
                        cq_sub_ka='1/p এর মান নির্ণয় কর।',
                        cq_sub_kha='প্রমাণ কর যে, p√p - 1/(p√p) = 22√2',
                        cq_sub_ga='a⁵ + 1/a⁵ এর মান নির্ণয় কর।',
                        cq_sub_gha='যদি a² + 1/a² = k হয়, তবে দেখাও যে a³ + 1/a³ এর মান k এর মাধ্যমে প্রকাশযোগ্য।',
                        cq_solution='ক) 1/p = 3 - 2√2\nখ) প্রমাণ...\nগ) মান নির্ণয়...'
                    ))

                if samples:
                    db.session.add_all(samples)
                    db.session.commit()
            print("[SUCCESS] Database successfully initialized and seeded with NCTB 2026 Curriculum!")


# ==========================================
# CORE ROUTES (Dashboard, CRUD, Paper Gen)
# ==========================================

@app.route('/')
def dashboard():
    total_classes = ClassLevel.query.count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_questions = Question.query.count()
    
    mcq_count = Question.query.filter_by(question_type='mcq').count()
    short_count = Question.query.filter_by(question_type='short').count()
    cq_count = Question.query.filter_by(question_type='cq').count()
    
    recent_questions = Question.query.order_by(Question.created_at.desc()).limit(8).all()
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    
    return render_template('dashboard.html',
                           total_classes=total_classes,
                           total_subjects=total_subjects,
                           total_chapters=total_chapters,
                           total_questions=total_questions,
                           mcq_count=mcq_count,
                           short_count=short_count,
                           cq_count=cq_count,
                           recent_questions=recent_questions,
                           classes=classes)


# ------------------------------------------
# QUESTION BANK (View, Filter, Add, Edit, Delete)
# ------------------------------------------

@app.route('/questions')
def question_list():
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('questions/list.html', classes=classes)


@app.route('/questions/add', methods=['GET', 'POST'])
def question_add():
    if request.method == 'POST':
        class_id = request.form.get('class_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        chapter_id = request.form.get('chapter_id', type=int)
        topic_id = request.form.get('topic_id', type=int) or None
        question_type = request.form.get('question_type')
        difficulty = request.form.get('difficulty', 'medium')
        marks = request.form.get('marks', type=float) or 1.0

        if not (class_id and subject_id and chapter_id and question_type):
            flash('দয়া করে শ্রেণি, বিষয়, অধ্যায় এবং প্রশ্নের ধরন সঠিকভাবে নির্বাচন করুন।', 'danger')
            return redirect(url_for('question_add'))

        new_q = Question(
            class_id=class_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            topic_id=topic_id,
            question_type=question_type,
            difficulty=difficulty,
            marks=marks
        )

        if question_type == 'mcq':
            new_q.mcq_stem = request.form.get('mcq_stem')
            new_q.option_a = request.form.get('option_a')
            new_q.option_b = request.form.get('option_b')
            new_q.option_c = request.form.get('option_c')
            new_q.option_d = request.form.get('option_d')
            new_q.correct_option = request.form.get('correct_option')
            new_q.explanation = request.form.get('explanation')
        elif question_type == 'short':
            new_q.short_question = request.form.get('short_question')
            new_q.short_answer = request.form.get('short_answer')
        elif question_type == 'cq':
            new_q.cq_stem = request.form.get('cq_stem')
            new_q.cq_sub_ka = request.form.get('cq_sub_ka')
            new_q.cq_sub_kha = request.form.get('cq_sub_kha')
            new_q.cq_sub_ga = request.form.get('cq_sub_ga')
            new_q.cq_sub_gha = request.form.get('cq_sub_gha')
            new_q.cq_solution = request.form.get('cq_solution')

        db.session.add(new_q)
        db.session.commit()
        flash('প্রশ্নটি সফলভাবে ডাটাবেজে সংরক্ষণ করা হয়েছে!', 'success')
        return redirect(url_for('question_list'))

    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('questions/add_edit.html', classes=classes, question=None)


@app.route('/questions/<int:id>/edit', methods=['GET', 'POST'])
def question_edit(id):
    question = Question.query.get_or_404(id)
    if request.method == 'POST':
        question.class_id = request.form.get('class_id', type=int)
        question.subject_id = request.form.get('subject_id', type=int)
        question.chapter_id = request.form.get('chapter_id', type=int)
        question.topic_id = request.form.get('topic_id', type=int) or None
        question.question_type = request.form.get('question_type')
        question.difficulty = request.form.get('difficulty', 'medium')
        question.marks = request.form.get('marks', type=float) or 1.0

        if question.question_type == 'mcq':
            question.mcq_stem = request.form.get('mcq_stem')
            question.option_a = request.form.get('option_a')
            question.option_b = request.form.get('option_b')
            question.option_c = request.form.get('option_c')
            question.option_d = request.form.get('option_d')
            question.correct_option = request.form.get('correct_option')
            question.explanation = request.form.get('explanation')
        elif question.question_type == 'short':
            question.short_question = request.form.get('short_question')
            question.short_answer = request.form.get('short_answer')
        elif question.question_type == 'cq':
            question.cq_stem = request.form.get('cq_stem')
            question.cq_sub_ka = request.form.get('cq_sub_ka')
            question.cq_sub_kha = request.form.get('cq_sub_kha')
            question.cq_sub_ga = request.form.get('cq_sub_ga')
            question.cq_sub_gha = request.form.get('cq_sub_gha')
            question.cq_solution = request.form.get('cq_solution')

        db.session.commit()
        flash('প্রশ্নটি সফলভাবে আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('question_list'))

    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('questions/add_edit.html', classes=classes, question=question)


@app.route('/questions/<int:id>/delete', methods=['POST'])
def question_delete(id):
    question = Question.query.get_or_404(id)
    db.session.delete(question)
    db.session.commit()
    return jsonify({'success': True, 'message': 'প্রশ্নটি সফলভাবে মুছে ফেলা হয়েছে।'})


# ------------------------------------------
# CONSTRUCTIVE (গঠনমূলক) & STRUCTURED IMPORT
# ------------------------------------------

@app.route('/constructive')
def constructive_view():
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('questions/constructive_import.html', classes=classes)


def normalize_question_data(item, default_class_id, default_subject_id, default_chapter_id, default_topic_id=None):
    """Normalize and validate a raw question dictionary into a structured Question object"""
    # Detect question type
    raw_type = str(item.get('question_type') or item.get('type') or item.get('ধরন') or '').strip().lower()
    
    if raw_type in ['cq', 'creative', 'সৃজনশীল', 'গঠনমূলক', 'structured']:
        q_type = 'cq'
    elif raw_type in ['mcq', 'multiple_choice', 'বহুনির্বাচনি', 'নৈর্ব্যক্তিক']:
        q_type = 'mcq'
    elif raw_type in ['short', 'সংক্ষিপ্ত', 'সংক্ষিপ্ত প্রশ্ন']:
        q_type = 'short'
    else:
        # Auto-infer based on present keys
        if any(k in item for k in ['cq_stem', 'sub_ka', 'ক', 'উদ্দীপক', 'stem']):
            q_type = 'cq'
        elif any(k in item for k in ['option_a', 'option_b', 'opt_a', 'ক)']):
            q_type = 'mcq'
        else:
            q_type = 'short'

    difficulty = str(item.get('difficulty') or item.get('কঠিন্যতা') or 'medium').strip().lower()
    if difficulty in ['সহজ', 'easy']:
        difficulty = 'easy'
    elif difficulty in ['কঠিন', 'hard']:
        difficulty = 'hard'
    else:
        difficulty = 'medium'

    # Determine topic
    topic_id = item.get('topic_id') or default_topic_id
    topic_title = item.get('topic_title') or item.get('topic') or item.get('টপিক') or item.get('পাঠ')
    if not topic_id and topic_title and default_chapter_id:
        existing_t = Topic.query.filter_by(chapter_id=default_chapter_id, title=str(topic_title).strip()).first()
        if existing_t:
            topic_id = existing_t.id
        else:
            new_t = Topic(chapter_id=default_chapter_id, title=str(topic_title).strip())
            db.session.add(new_t)
            db.session.flush()
            topic_id = new_t.id

    # Marks
    try:
        marks = float(item.get('marks') or item.get('পূর্ণমান') or (10.0 if q_type == 'cq' else (2.0 if q_type == 'short' else 1.0)))
    except (ValueError, TypeError):
        marks = 10.0 if q_type == 'cq' else (2.0 if q_type == 'short' else 1.0)

    q = Question(
        class_id=item.get('class_id') or default_class_id,
        subject_id=item.get('subject_id') or default_subject_id,
        chapter_id=item.get('chapter_id') or default_chapter_id,
        topic_id=topic_id,
        question_type=q_type,
        difficulty=difficulty,
        marks=marks
    )

    if q_type == 'cq':
        q.cq_stem = str(item.get('cq_stem') or item.get('stem') or item.get('উদ্দীপক') or item.get('দৃশ্যকল্প') or '').strip()
        q.cq_sub_ka = str(item.get('cq_sub_ka') or item.get('sub_ka') or item.get('ka') or item.get('ক') or item.get('ক)') or '').strip()
        q.cq_sub_kha = str(item.get('cq_sub_kha') or item.get('sub_kha') or item.get('kha') or item.get('খ') or item.get('খ)') or '').strip()
        q.cq_sub_ga = str(item.get('cq_sub_ga') or item.get('sub_ga') or item.get('ga') or item.get('গ') or item.get('গ)') or '').strip()
        q.cq_sub_gha = str(item.get('cq_sub_gha') or item.get('sub_gha') or item.get('gha') or item.get('ঘ') or item.get('ঘ)') or '').strip()
        q.cq_solution = str(item.get('cq_solution') or item.get('solution') or item.get('সমাধান') or item.get('উত্তর') or '').strip()
    elif q_type == 'mcq':
        q.mcq_stem = str(item.get('mcq_stem') or item.get('question') or item.get('stem') or item.get('প্রশ্ন') or '').strip()
        q.option_a = str(item.get('option_a') or item.get('opt_a') or item.get('a') or item.get('ক') or '').strip()
        q.option_b = str(item.get('option_b') or item.get('opt_b') or item.get('b') or item.get('খ') or '').strip()
        q.option_c = str(item.get('option_c') or item.get('opt_c') or item.get('c') or item.get('গ') or '').strip()
        q.option_d = str(item.get('option_d') or item.get('opt_d') or item.get('d') or item.get('ঘ') or '').strip()
        
        raw_ans = str(item.get('correct_option') or item.get('answer') or item.get('correct_ans') or item.get('সঠিক_উত্তর') or '').strip()
        ans_map = {'a': 'ক', 'b': 'খ', 'c': 'গ', 'd': 'ঘ', '1': 'ক', '2': 'খ', '3': 'গ', '4': 'ঘ'}
        q.correct_option = ans_map.get(raw_ans.lower(), raw_ans)
        q.explanation = str(item.get('explanation') or item.get('ব্যাখ্যা') or '').strip()
    elif q_type == 'short':
        q.short_question = str(item.get('short_question') or item.get('question') or item.get('প্রশ্ন') or '').strip()
        q.short_answer = str(item.get('short_answer') or item.get('answer') or item.get('উত্তর') or '').strip()

    return q


def parse_structured_text_questions(raw_text):
    """Parse human-formatted Bengali question text containing CQ, MCQ, or Short questions"""
    questions = []
    blocks = [b.strip() for b in raw_text.replace('\r\n', '\n').split('\n\n\n') if b.strip()]
    if len(blocks) <= 1:
        # Try split by delimiter or lines starting with [ বা প্রশ্ন
        lines = raw_text.replace('\r\n', '\n').split('\n')
        current_block = []
        blocks = []
        for line in lines:
            if line.strip().startswith(('[', '---', '===')) and current_block:
                blocks.append('\n'.join(current_block))
                current_block = [line]
            else:
                current_block.append(line)
        if current_block:
            blocks.append('\n'.join(current_block))

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
            
        block_text = '\n'.join(lines)
        
        # Check if CQ (Creative / গঠনমূলক)
        if any(k in block_text for k in ['উদ্দীপক:', 'উদ্দীপক', 'ক)', 'ক.', 'খ)', 'খ.', 'দৃশ্যকল্প:']):
            stem = ""
            ka, kha, ga, gha, sol = "", "", "", "", ""
            current_field = 'stem'
            
            for line in lines:
                if line.startswith(('উদ্দীপক:', 'দৃশ্যকল্প:', 'উদ্দীপক -', 'অনুচ্ছেদ:')):
                    current_field = 'stem'
                    stem += line.split(':', 1)[-1].strip() + "\n"
                elif line.startswith(('ক)', 'ক.', 'ক -', 'ক:')):
                    current_field = 'ka'
                    ka = line.lstrip('ক). -:').strip()
                elif line.startswith(('খ)', 'খ.', 'খ -', 'খ:')):
                    current_field = 'kha'
                    kha = line.lstrip('খ). -:').strip()
                elif line.startswith(('গ)', 'গ.', 'গ -', 'গ:')):
                    current_field = 'ga'
                    ga = line.lstrip('গ). -:').strip()
                elif line.startswith(('ঘ)', 'ঘ.', 'ঘ -', 'ঘ:')):
                    current_field = 'gha'
                    gha = line.lstrip('ঘ). -:').strip()
                elif line.startswith(('সমাধান:', 'উত্তর:', 'নির্দেশনা:')):
                    current_field = 'sol'
                    sol += line.split(':', 1)[-1].strip() + "\n"
                elif line.startswith('['):
                    continue
                else:
                    if current_field == 'stem':
                        stem += line + "\n"
                    elif current_field == 'ka':
                        ka += " " + line
                    elif current_field == 'kha':
                        kha += " " + line
                    elif current_field == 'ga':
                        ga += " " + line
                    elif current_field == 'gha':
                        gha += " " + line
                    elif current_field == 'sol':
                        sol += line + "\n"
            
            questions.append({
                'type': 'cq',
                'cq_stem': stem.strip(),
                'cq_sub_ka': ka.strip(),
                'cq_sub_kha': kha.strip(),
                'cq_sub_ga': ga.strip(),
                'cq_sub_gha': gha.strip(),
                'cq_solution': sol.strip(),
                'marks': 10.0,
                'difficulty': 'medium'
            })
        elif any(k in block_text for k in ['ক)', 'ক.', 'খ)', 'খ.', 'গ)', 'ঘ)']):
            # MCQ Question
            q_stem = ""
            opt_a, opt_b, opt_c, opt_d = "", "", "", ""
            ans, exp = "", ""
            for line in lines:
                if line.startswith(('প্রশ্ন:', 'প্রশ্ন -', 'Q:')):
                    q_stem = line.split(':', 1)[-1].strip()
                elif line.startswith(('ক)', 'ক.', 'A)', 'A.')):
                    opt_a = line.lstrip('কA). -:').strip()
                elif line.startswith(('খ)', 'খ.', 'B)', 'B.')):
                    opt_b = line.lstrip('খB). -:').strip()
                elif line.startswith(('গ)', 'গ.', 'C)', 'C.')):
                    opt_c = line.lstrip('গC). -:').strip()
                elif line.startswith(('ঘ)', 'ঘ.', 'D)', 'D.')):
                    opt_d = line.lstrip('ঘD). -:').strip()
                elif line.startswith(('সঠিক উত্তর:', 'উত্তর:', 'Ans:')):
                    ans = line.split(':', 1)[-1].strip()
                elif line.startswith(('ব্যাখ্যা:', 'ব্যাখ্যা -', 'Exp:')):
                    exp = line.split(':', 1)[-1].strip()
                elif not q_stem and not line.startswith('['):
                    q_stem = line
            
            questions.append({
                'type': 'mcq',
                'mcq_stem': q_stem.strip(),
                'option_a': opt_a.strip(),
                'option_b': opt_b.strip(),
                'option_c': opt_c.strip(),
                'option_d': opt_d.strip(),
                'correct_option': ans.strip(),
                'explanation': exp.strip(),
                'marks': 1.0,
                'difficulty': 'medium'
            })
        else:
            # Short question
            q_text = ""
            ans_text = ""
            for line in lines:
                if line.startswith(('প্রশ্ন:', 'প্রশ্ন -', 'Q:')):
                    q_text = line.split(':', 1)[-1].strip()
                elif line.startswith(('উত্তর:', 'সমাধান:', 'Ans:')):
                    ans_text = line.split(':', 1)[-1].strip()
                elif not q_text and not line.startswith('['):
                    q_text = line
                elif q_text and not ans_text:
                    ans_text = line
            
            if q_text:
                questions.append({
                    'type': 'short',
                    'short_question': q_text.strip(),
                    'short_answer': ans_text.strip(),
                    'marks': 2.0,
                    'difficulty': 'medium'
                })
    return questions


# ==========================================
# ULTRA HIGH-SPEED FAST SAVE CORE ENGINE
# ==========================================

def fast_save_questions_core(raw_items, default_class_id=None, default_subject_id=None, default_chapter_id=None, default_topic_id=None):
    """
    Ultra-optimized bulk/single question saver with in-memory caching:
    - Resolves string names or integer IDs with zero redundant queries
    - Microsecond dictionary parsing and normalization
    - Single atomic database transaction for peak SQLite performance
    - Returns detailed performance telemetry (execution time in ms, speed items/sec)
    """
    t_start = time.perf_counter()
    
    if not isinstance(raw_items, list):
        raw_items = [raw_items]
        
    if not raw_items:
        return {
            'success': False,
            'count': 0,
            'time_taken_ms': 0.0,
            'speed_items_per_sec': 0.0,
            'message': 'কোনো প্রশ্ন পাওয়া যায়নি।'
        }

    # In-memory lookup caches to eliminate N+1 queries during bulk operations
    class_cache = {}    # id or name -> ClassLevel obj
    subject_cache = {}  # (class_id, name) or id -> Subject obj
    chapter_cache = {}  # (subject_id, title) or id -> Chapter obj
    topic_cache = {}    # (chapter_id, title) or id -> Topic obj

    # Pre-cache defaults if provided
    if default_class_id:
        c = ClassLevel.query.get(default_class_id)
        if c:
            class_cache[c.id] = c
            class_cache[c.name.strip().lower()] = c
    if default_subject_id:
        s = Subject.query.get(default_subject_id)
        if s:
            subject_cache[s.id] = s
            subject_cache[(s.class_id, s.name.strip().lower())] = s
    if default_chapter_id:
        ch = Chapter.query.get(default_chapter_id)
        if ch:
            chapter_cache[ch.id] = ch
            chapter_cache[(ch.subject_id, ch.title.strip().lower())] = ch
    if default_topic_id:
        top = Topic.query.get(default_topic_id)
        if top:
            topic_cache[top.id] = top
            topic_cache[(top.chapter_id, top.title.strip().lower())] = top

    created_questions = []
    
    for item in raw_items:
        if not isinstance(item, dict):
            continue

        # 1. Resolve Class
        target_class_id = item.get('class_id') or default_class_id
        class_name = str(item.get('class_name') or item.get('class') or item.get('শ্রেণি') or '').strip()
        
        if not target_class_id and class_name:
            cn_key = class_name.lower()
            if cn_key in class_cache:
                target_class_id = class_cache[cn_key].id
            else:
                c_obj = ClassLevel.query.filter(ClassLevel.name.ilike(f"%{class_name}%")).first()
                if not c_obj:
                    c_obj = ClassLevel(name=class_name, code=class_name[:10])
                    db.session.add(c_obj)
                    db.session.flush()
                class_cache[c_obj.id] = c_obj
                class_cache[cn_key] = c_obj
                target_class_id = c_obj.id

        # 2. Resolve Subject
        target_subject_id = item.get('subject_id') or default_subject_id
        subject_name = str(item.get('subject_name') or item.get('subject') or item.get('বিষয়') or '').strip()
        
        if not target_subject_id and subject_name and target_class_id:
            s_key = (target_class_id, subject_name.lower())
            if s_key in subject_cache:
                target_subject_id = subject_cache[s_key].id
            else:
                s_obj = Subject.query.filter(Subject.class_id == target_class_id, Subject.name.ilike(f"%{subject_name}%")).first()
                if not s_obj:
                    s_obj = Subject(class_id=target_class_id, name=subject_name)
                    db.session.add(s_obj)
                    db.session.flush()
                subject_cache[s_obj.id] = s_obj
                subject_cache[s_key] = s_obj
                target_subject_id = s_obj.id

        # 3. Resolve Chapter
        target_chapter_id = item.get('chapter_id') or default_chapter_id
        chapter_title = str(item.get('chapter_title') or item.get('chapter_name') or item.get('chapter') or item.get('অধ্যায়') or '').strip()
        chapter_no = str(item.get('chapter_no') or '').strip()
        
        if not target_chapter_id and chapter_title and target_subject_id:
            ch_key = (target_subject_id, chapter_title.lower())
            if ch_key in chapter_cache:
                target_chapter_id = chapter_cache[ch_key].id
            else:
                ch_obj = Chapter.query.filter(Chapter.subject_id == target_subject_id, Chapter.title.ilike(f"%{chapter_title}%")).first()
                if not ch_obj:
                    ch_obj = Chapter(subject_id=target_subject_id, title=chapter_title, chapter_no=chapter_no)
                    db.session.add(ch_obj)
                    db.session.flush()
                chapter_cache[ch_obj.id] = ch_obj
                chapter_cache[ch_key] = ch_obj
                target_chapter_id = ch_obj.id

        # 4. Resolve Topic
        target_topic_id = item.get('topic_id') or default_topic_id
        topic_title = str(item.get('topic_title') or item.get('topic') or item.get('টপিক') or item.get('পাঠ') or '').strip()
        
        if not target_topic_id and topic_title and target_chapter_id:
            t_key = (target_chapter_id, topic_title.lower())
            if t_key in topic_cache:
                target_topic_id = topic_cache[t_key].id
            else:
                t_obj = Topic.query.filter(Topic.chapter_id == target_chapter_id, Topic.title.ilike(f"%{topic_title}%")).first()
                if not t_obj:
                    t_obj = Topic(chapter_id=target_chapter_id, title=topic_title)
                    db.session.add(t_obj)
                    db.session.flush()
                topic_cache[t_obj.id] = t_obj
                topic_cache[t_key] = t_obj
                target_topic_id = t_obj.id

        if not (target_class_id and target_subject_id and target_chapter_id):
            continue

        # Fast question object generation
        q_obj = normalize_question_data(item, target_class_id, target_subject_id, target_chapter_id, target_topic_id)
        created_questions.append(q_obj)

    if not created_questions:
        return {
            'success': False,
            'count': 0,
            'time_taken_ms': round((time.perf_counter() - t_start) * 1000, 2),
            'speed_items_per_sec': 0.0,
            'message': 'সঠিক শ্রেণি, বিষয় ও অধ্যায় তথ্য সংবলিত কোনো প্রশ্ন পাওয়া যায়নি।'
        }

    # Atomic fast commit
    db.session.add_all(created_questions)
    db.session.commit()
    
    t_elapsed_sec = time.perf_counter() - t_start
    t_taken_ms = round(t_elapsed_sec * 1000, 2)
    saved_count = len(created_questions)
    items_per_sec = round(saved_count / max(t_elapsed_sec, 0.0001), 1)
    
    return {
        'success': True,
        'count': saved_count,
        'time_taken_ms': t_taken_ms,
        'speed_items_per_sec': items_per_sec,
        'saved_ids': [q.id for q in created_questions],
        'items': [q.to_dict() for q in created_questions[:50]] if saved_count <= 50 else [],
        'message': f'মোট {to_bangla_number(saved_count)}টি প্রশ্ন মাত্র {to_bangla_number(t_taken_ms)} মিলিসেকেন্ডে সংরক্ষিত হয়েছে!'
    }


# ==========================================
# HIGH-PERFORMANCE RESTful FAST API ENDPOINTS
# ==========================================

@app.route('/api/v1/fast-save', methods=['POST'])
@app.route('/api/v1/questions/save', methods=['POST'])
def api_v1_fast_save():
    """
    ⚡ Ultra-Fast Save API:
    Supports single question JSON, array of questions, multipart file/text, or form-data.
    Returns microsecond telemetry with saved IDs and speed metrics.
    """
    try:
        class_id = None
        subject_id = None
        chapter_id = None
        topic_id = None
        questions_raw = []

        if request.content_type and 'multipart/form-data' in request.content_type:
            class_id = request.form.get('class_id', type=int)
            subject_id = request.form.get('subject_id', type=int)
            chapter_id = request.form.get('chapter_id', type=int)
            topic_id = request.form.get('topic_id', type=int) or None
            
            if 'file' in request.files:
                file = request.files['file']
                filename = file.filename.lower()
                content = file.read().decode('utf-8-sig', errors='replace')
                if filename.endswith('.json'):
                    data = json.loads(content)
                    questions_raw = data if isinstance(data, list) else data.get('questions', [])
                elif filename.endswith(('.csv', '.tsv')):
                    delimiter = '\t' if filename.endswith('.tsv') else ','
                    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                    questions_raw = list(reader)
                else:
                    try:
                        data = json.loads(content)
                        questions_raw = data if isinstance(data, list) else data.get('questions', [])
                    except Exception:
                        questions_raw = parse_structured_text_questions(content)
            elif request.form.get('raw_text'):
                raw_text = request.form.get('raw_text', '')
                try:
                    data = json.loads(raw_text)
                    questions_raw = data if isinstance(data, list) else data.get('questions', [])
                except Exception:
                    questions_raw = parse_structured_text_questions(raw_text)
            else:
                # Single form submission
                single_dict = request.form.to_dict()
                questions_raw = [single_dict]
        else:
            payload = request.get_json(force=True, silent=True) or {}
            
            if isinstance(payload, list):
                questions_raw = payload
            elif 'questions' in payload and isinstance(payload['questions'], list):
                class_id = payload.get('class_id')
                subject_id = payload.get('subject_id')
                chapter_id = payload.get('chapter_id')
                topic_id = payload.get('topic_id')
                questions_raw = payload['questions']
            elif 'raw_text' in payload:
                class_id = payload.get('class_id')
                subject_id = payload.get('subject_id')
                chapter_id = payload.get('chapter_id')
                topic_id = payload.get('topic_id')
                questions_raw = parse_structured_text_questions(payload['raw_text'])
            else:
                class_id = payload.get('class_id')
                subject_id = payload.get('subject_id')
                chapter_id = payload.get('chapter_id')
                topic_id = payload.get('topic_id')
                questions_raw = [payload]

        result = fast_save_questions_core(
            raw_items=questions_raw,
            default_class_id=class_id,
            default_subject_id=subject_id,
            default_chapter_id=chapter_id,
            default_topic_id=topic_id
        )

        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'ফাস্ট সেভ প্রক্রিয়ায় ত্রুটি ঘটেছে: {str(e)}',
            'error': str(e)
        }), 500


@app.route('/api/v1/questions/batch', methods=['POST'])
def api_v1_questions_batch():
    """Dedicated high-throughput batch question ingestion endpoint"""
    return api_v1_fast_save()


@app.route('/api/v1/curriculum/bulk-save', methods=['POST'])
def api_v1_curriculum_bulk_save():
    """
    ⚡ Ultra-Fast Batch Curriculum Sync/Save API:
    Accepts full hierarchy tree or flat lists of classes, subjects, chapters, topics.
    """
    t_start = time.perf_counter()
    try:
        payload = request.get_json(force=True) or {}
        classes_data = payload.get('classes', [])
        
        created_classes = 0
        created_subjects = 0
        created_chapters = 0
        created_topics = 0
        
        for c_data in classes_data:
            c_name = c_data.get('name', '').strip()
            if not c_name:
                continue
            cls = ClassLevel.query.filter_by(name=c_name).first()
            if not cls:
                cls = ClassLevel(name=c_name, code=c_data.get('code', ''), order_num=c_data.get('order_num', 0))
                db.session.add(cls)
                db.session.flush()
                created_classes += 1
                
            for s_data in c_data.get('subjects', []):
                s_name = s_data.get('name', '').strip()
                if not s_name:
                    continue
                sub = Subject.query.filter_by(class_id=cls.id, name=s_name).first()
                if not sub:
                    sub = Subject(class_id=cls.id, name=s_name, code=s_data.get('code', ''))
                    db.session.add(sub)
                    db.session.flush()
                    created_subjects += 1
                    
                for ch_data in s_data.get('chapters', []):
                    ch_title = ch_data.get('title', '').strip()
                    if not ch_title:
                        continue
                    ch = Chapter.query.filter_by(subject_id=sub.id, title=ch_title).first()
                    if not ch:
                        ch = Chapter(subject_id=sub.id, title=ch_title, chapter_no=ch_data.get('chapter_no', ''))
                        db.session.add(ch)
                        db.session.flush()
                        created_chapters += 1
                        
                    for t_data in ch_data.get('topics', []):
                        t_title = t_data.get('title', '').strip() if isinstance(t_data, dict) else str(t_data).strip()
                        if not t_title:
                            continue
                        top = Topic.query.filter_by(chapter_id=ch.id, title=t_title).first()
                        if not top:
                            top = Topic(chapter_id=ch.id, title=t_title)
                            db.session.add(top)
                            db.session.flush()
                            created_topics += 1
                            
        db.session.commit()
        t_taken_ms = round((time.perf_counter() - t_start) * 1000, 2)
        
        return jsonify({
            'success': True,
            'time_taken_ms': t_taken_ms,
            'summary': {
                'classes_created': created_classes,
                'subjects_created': created_subjects,
                'chapters_created': created_chapters,
                'topics_created': created_topics
            },
            'message': f'পাঠ্যক্রম মাত্র {to_bangla_number(t_taken_ms)} মিলিসেকেন্ডে সংরক্ষিত হয়েছে!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/v1/exam-papers/fast-save', methods=['POST'])
def api_v1_exam_paper_fast_save():
    """⚡ Ultra-Fast Exam Paper Persistence API"""
    t_start = time.perf_counter()
    try:
        payload = request.get_json(force=True) or {}
        paper_id = payload.get('id')
        
        if paper_id:
            paper = ExamPaper.query.get(paper_id)
            if not paper:
                return jsonify({'success': False, 'message': 'প্রশ্নপত্রটি পাওয়া যায়নি'}), 404
        else:
            paper = ExamPaper(questions_json='[]')
            db.session.add(paper)
            
        paper.title = payload.get('title', 'সৃজনশীল প্রশ্নপত্র')
        paper.school_name = payload.get('school_name', 'আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়')
        paper.exam_name = payload.get('exam_name', 'অর্ধ-বার্ষিক পরীক্ষা')
        paper.class_id = payload.get('class_id')
        paper.subject_id = payload.get('subject_id')
        paper.time_allowed = payload.get('time_allowed', '২ ঘণ্টা ৩০ মিনিট')
        paper.total_marks = float(payload.get('total_marks', 100))
        paper.instructions = payload.get('instructions', '')
        
        q_ids = payload.get('question_ids', [])
        paper.questions_json = json.dumps(q_ids if isinstance(q_ids, list) else [int(x) for x in str(q_ids).split(',') if x.strip().isdigit()])
        
        db.session.commit()
        t_taken_ms = round((time.perf_counter() - t_start) * 1000, 2)
        
        return jsonify({
            'success': True,
            'paper_id': paper.id,
            'time_taken_ms': t_taken_ms,
            'data': paper.to_dict(),
            'message': f'প্রশ্নপত্রটি মাত্র {to_bangla_number(t_taken_ms)} মিলিসেকেন্ডে সংরক্ষিত হয়েছে!'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/v1/database/optimize', methods=['POST', 'GET'])
def api_v1_database_optimize():
    """Run SQLite PRAGMA maintenance and WAL checkpoint for continuous peak speed"""
    t_start = time.perf_counter()
    try:
        with db.engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA optimize;")
            conn.exec_driver_sql("PRAGMA wal_checkpoint(TRUNCATE);")
            conn.exec_driver_sql("ANALYZE;")
        t_taken_ms = round((time.perf_counter() - t_start) * 1000, 2)
        return jsonify({
            'success': True,
            'time_taken_ms': t_taken_ms,
            'message': f'ডাটাবেজ ইঞ্জিন সফলভাবে অপ্টিমাইজ করা হয়েছে ({to_bangla_number(t_taken_ms)} ms)!'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/v1/database/benchmark', methods=['GET', 'POST'])
def api_v1_database_benchmark():
    """Live Speed Benchmark for Measuring Real-Time Write & Read Throughput"""
    test_count = request.args.get('count', default=50, type=int)
    test_count = min(max(test_count, 10), 200)
    
    c = ClassLevel.query.first()
    s = Subject.query.filter_by(class_id=c.id).first() if c else None
    ch = Chapter.query.filter_by(subject_id=s.id).first() if s else None
    
    if not (c and s and ch):
        return jsonify({'success': False, 'message': 'বেঞ্চমার্ক চালানোর জন্য পর্যাপ্ত পাঠ্যক্রম ডাটা নেই'}), 400

    # 1. Write Benchmark
    mock_items = []
    for i in range(test_count):
        mock_items.append({
            'question_type': 'mcq',
            'difficulty': 'easy',
            'marks': 1.0,
            'mcq_stem': f'[বেঞ্চমার্ক টেস্ট প্রশ্ন #{i+1}] পানির রাসায়নিক সংকেত কোনটি?',
            'option_a': 'H2O',
            'option_b': 'CO2',
            'option_c': 'NaCl',
            'option_d': 'CH4',
            'correct_option': 'ক',
            'explanation': 'বেঞ্চমার্ক টেস্টিং রেকর্ড'
        })
        
    t_write_start = time.perf_counter()
    res = fast_save_questions_core(mock_items, default_class_id=c.id, default_subject_id=s.id, default_chapter_id=ch.id)
    t_write_ms = res.get('time_taken_ms', 0)
    saved_ids = res.get('saved_ids', [])
    
    # 2. Read Benchmark
    t_read_start = time.perf_counter()
    _ = Question.query.filter(Question.id.in_(saved_ids)).all()
    t_read_ms = round((time.perf_counter() - t_read_start) * 1000, 2)
    
    # Clean up benchmark questions to keep DB pristine
    if saved_ids:
        Question.query.filter(Question.id.in_(saved_ids)).delete(synchronize_session=False)
        db.session.commit()
        
    return jsonify({
        'success': True,
        'benchmark_items': test_count,
        'write_time_ms': t_write_ms,
        'write_speed_items_per_sec': round(test_count / max(t_write_ms / 1000.0, 0.0001), 1),
        'read_time_ms': t_read_ms,
        'read_speed_items_per_sec': round(test_count / max(t_read_ms / 1000.0, 0.0001), 1),
        'sqlite_mode': 'WAL (Write-Ahead Logging)',
        'message': f'{to_bangla_number(test_count)}টি প্রশ্নের ডাটাবেজ রাইট টেস্ট মাত্র {to_bangla_number(t_write_ms)} ms এ সম্পন্ন হয়েছে!'
    })


@app.route('/api/v1/database/stats')
def api_v1_database_stats():
    """Get Database size and performance statistics"""
    db_path = os.path.join(app.instance_path, 'question_bank.db') if os.path.exists(os.path.join(app.instance_path, 'question_bank.db')) else 'question_bank.db'
    wal_path = db_path + '-wal'
    
    db_size_kb = round(os.path.getsize(db_path) / 1024, 2) if os.path.exists(db_path) else 0
    wal_size_kb = round(os.path.getsize(wal_path) / 1024, 2) if os.path.exists(wal_path) else 0
    
    return jsonify({
        'total_questions': Question.query.count(),
        'total_classes': ClassLevel.query.count(),
        'total_subjects': Subject.query.count(),
        'total_chapters': Chapter.query.count(),
        'total_topics': Topic.query.count(),
        'total_exam_papers': ExamPaper.query.count(),
        'db_file_size_kb': db_size_kb,
        'wal_file_size_kb': wal_size_kb,
        'journal_mode': 'WAL',
        'cache_size': '64 MB RAM',
        'mmap_size': '256 MB'
    })


@app.route('/api/docs')
def api_documentation_view():
    """Interactive Fast API Documentation & Live Speed Tester Playground"""
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('api_docs.html', classes=classes)


@app.route('/api/questions/import', methods=['POST'])
def api_questions_import():
    """Backward-compatible bulk import leveraging Fast Save Engine"""
    return api_v1_fast_save()


@app.route('/api/templates/download/<template_type>')
def api_download_template(template_type):
    """Download ready-to-use sample templates for teachers in JSON or CSV"""
    
    cq_sample_json = [
        {
            "question_type": "cq",
            "difficulty": "medium",
            "marks": 10.0,
            "topic_title": "সুভার স্বভাব ও নির্বাক প্রকৃতির সাথে সখ্য",
            "cq_stem": "দশম শ্রেণির ছাত্রী মিতু চোখে দেখে না। কিন্তু তার স্মৃতিশক্তি প্রখর এবং গানের গলা চমৎকার। পরিবারের সদস্যরা তাকে নিয়ে লজ্জিত না হয়ে তার সংগীত চর্চায় সর্বাত্মক সহায়তা করেন। ফলে মিতু জাতীয় পর্যায়ে শ্রেষ্ঠ সংগীতশিল্পী হিসেবে পুরস্কার অর্জন করে।",
            "cq_sub_ka": "সুভার পিতার নাম কী?",
            "cq_sub_kha": "‘সুভার একটি বিশেষ সুবিধা ছিল’—কথাটি দ্বারা কী বোঝানো হয়েছে?",
            "cq_sub_ga": "উদ্দীপকের মিতুর পারিবারিক পরিবেশ ‘সুভা’ গল্পের কোন ভিন্ন দিকটি উন্মোচন করে? ব্যাখ্যা কর।",
            "cq_sub_gha": "“মিতু অনুকূল পরিবেশ পেলেও সুভা তা থেকে বঞ্চিত ছিল”—মন্তব্যটি ‘সুভা’ গল্পের আলোকে বিশ্লেষণ কর।",
            "cq_solution": "ক) সুভার পিতার নাম বাণীকণ্ঠ।\nখ) অনুধাবনমূলক বিশদ আলোচনা।\nগ) উদ্দীপক ও পাঠ্যবইয়ের মেলবন্ধন।\nঘ) উচ্চতর দক্ষতামূলক তুলনামূলক সিদ্ধান্ত।"
        },
        {
            "question_type": "cq",
            "difficulty": "hard",
            "marks": 10.0,
            "topic_title": "বর্গ ও ঘন সংবলিত সূত্রাবলি",
            "cq_stem": "p = 3 + 2√2 এবং a² - 2√6a + 1 = 0 দুটি বীজগাণিতিক সম্পর্ক।",
            "cq_sub_ka": "1/p এর মান নির্ণয় কর।",
            "cq_sub_kha": "প্রমাণ কর যে, p√p - 1/(p√p) = 22√2",
            "cq_sub_ga": "a⁵ + 1/a⁵ এর মান নির্ণয় কর।",
            "cq_sub_gha": "যদি a² + 1/a² = k হয়, তবে দেখাও যে a³ + 1/a³ এর মান k এর মাধ্যমে প্রকাশযোগ্য।",
            "cq_solution": "ক) 1/p = 3 - 2√2\nখ) সূত্র প্রয়োগ করে প্রমাণ...\nগ) প্রদত্ত সমীকরণ হতে মান নির্ণয়..."
        }
    ]

    mcq_sample_json = [
        {
            "question_type": "mcq",
            "difficulty": "easy",
            "marks": 1.0,
            "topic_title": "সুভার স্বভাব ও নির্বাক প্রকৃতির সাথে সখ্য",
            "mcq_stem": "সুভার সাথে কার ঘনিষ্ঠ বন্ধুত্ব ছিল?",
            "option_a": "প্রতাপ",
            "option_b": "গোঁসাইদের ছোট ছেলে",
            "option_c": "সর্বশী ও পাঙ্গুলি নামের দুটি গাভী",
            "option_d": "গ্রামের সমবয়সী মেয়েরা",
            "correct_option": "গ",
            "explanation": "সুভার মূক প্রকৃতির সাথে বোবা প্রাণী দুটি অন্তরঙ্গ বন্ধু ছিল।"
        },
        {
            "question_type": "mcq",
            "difficulty": "medium",
            "marks": 1.0,
            "topic_title": "বর্গ ও ঘন সংবলিত সূত্রাবলি",
            "mcq_stem": "x + 1/x = 2 হলে, x³ + 1/x³ এর মান কত?",
            "option_a": "0",
            "option_b": "2",
            "option_c": "4",
            "option_d": "8",
            "correct_option": "খ",
            "explanation": "x³ + 1/x³ = (x + 1/x)³ - 3(x)(1/x)(x + 1/x) = 2³ - 6 = 2"
        }
    ]

    short_sample_json = [
        {
            "question_type": "short",
            "difficulty": "medium",
            "marks": 2.0,
            "topic_title": "সুভার স্বভাব ও নির্বাক প্রকৃতির সাথে সখ্য",
            "short_question": "সুভার মা কেন সুভাকে নিজের গর্ভের কলঙ্ক মনে করতেন?",
            "short_answer": "সাধারণত মায়েরা মেয়ের মধ্যে নিজের প্রতিচ্ছবি দেখতে চান। সুভা জন্মগতভাবে বাকপ্রতিবন্ধী হওয়ায় মা তাকে নিজের ত্রুটি ও গর্ভের কলঙ্ক মনে করতেন।"
        }
    ]

    if template_type == 'cq_json':
        resp = make_response(json.dumps(cq_sample_json, ensure_ascii=False, indent=2))
        resp.headers['Content-Disposition'] = 'attachment; filename=creative_questions_cq_template.json'
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp
        
    elif template_type == 'cq_csv':
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['question_type', 'difficulty', 'marks', 'topic_title', 'cq_stem', 'cq_sub_ka', 'cq_sub_kha', 'cq_sub_ga', 'cq_sub_gha', 'cq_solution'])
        for q in cq_sample_json:
            writer.writerow([
                q['question_type'], q['difficulty'], q['marks'], q['topic_title'],
                q['cq_stem'], q['cq_sub_ka'], q['cq_sub_kha'], q['cq_sub_ga'], q['cq_sub_gha'], q['cq_solution']
            ])
        output = make_response(si.getvalue().encode('utf-8-sig'))
        output.headers['Content-Disposition'] = 'attachment; filename=creative_questions_cq_template.csv'
        output.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return output

    elif template_type == 'mcq_json':
        resp = make_response(json.dumps(mcq_sample_json, ensure_ascii=False, indent=2))
        resp.headers['Content-Disposition'] = 'attachment; filename=mcq_questions_template.json'
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp

    elif template_type == 'mcq_csv':
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['question_type', 'difficulty', 'marks', 'topic_title', 'mcq_stem', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_option', 'explanation'])
        for q in mcq_sample_json:
            writer.writerow([
                q['question_type'], q['difficulty'], q['marks'], q['topic_title'],
                q['mcq_stem'], q['option_a'], q['option_b'], q['option_c'], q['option_d'], q['correct_option'], q['explanation']
            ])
        output = make_response(si.getvalue().encode('utf-8-sig'))
        output.headers['Content-Disposition'] = 'attachment; filename=mcq_questions_template.csv'
        output.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return output

    elif template_type == 'short_json':
        resp = make_response(json.dumps(short_sample_json, ensure_ascii=False, indent=2))
        resp.headers['Content-Disposition'] = 'attachment; filename=short_questions_template.json'
        resp.headers['Content-Type'] = 'application/json; charset=utf-8'
        return resp

    elif template_type == 'short_csv':
        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(['question_type', 'difficulty', 'marks', 'topic_title', 'short_question', 'short_answer'])
        for q in short_sample_json:
            writer.writerow([
                q['question_type'], q['difficulty'], q['marks'], q['topic_title'],
                q['short_question'], q['short_answer']
            ])
        output = make_response(si.getvalue().encode('utf-8-sig'))
        output.headers['Content-Disposition'] = 'attachment; filename=short_questions_template.csv'
        output.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return output

    # Default: Mixed all json
    mixed = cq_sample_json + mcq_sample_json + short_sample_json
    resp = make_response(json.dumps(mixed, ensure_ascii=False, indent=2))
    resp.headers['Content-Disposition'] = 'attachment; filename=all_types_questions_template.json'
    resp.headers['Content-Type'] = 'application/json; charset=utf-8'
    return resp


# ------------------------------------------
# QUESTION PAPER BUILDER & EXAM GENERATOR
# ------------------------------------------

@app.route('/exam-builder')
def exam_builder():
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    return render_template('exam/builder.html', classes=classes)


@app.route('/exam/preview', methods=['POST'])
def exam_preview():
    data = request.get_json() if request.is_json else request.form
    
    school_name = data.get('school_name', 'আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়')
    exam_name = data.get('exam_name', 'অর্ধ-বার্ষিক পরীক্ষা ২০২৬')
    class_name = data.get('class_name', '')
    subject_name = data.get('subject_name', '')
    time_allowed = data.get('time_allowed', '২ ঘণ্টা ৩০ মিনিট')
    total_marks = data.get('total_marks', '১০০')
    instructions = data.get('instructions', '[সকল প্রশ্নের উত্তর দেওয়া আবশ্যক। ডান পাশের সংখ্যা প্রশ্নের পূর্ণমান নির্দেশক]')
    
    question_ids = data.get('question_ids', [])
    if isinstance(question_ids, str):
        try:
            question_ids = json.loads(question_ids)
        except Exception:
            question_ids = [int(x) for x in question_ids.split(',') if x.strip().isdigit()]

    # Fetch selected questions
    questions = Question.query.filter(Question.id.in_(question_ids)).all() if question_ids else []
    
    # Sort into categories maintaining relative order
    mcq_questions = [q for q in questions if q.question_type == 'mcq']
    short_questions = [q for q in questions if q.question_type == 'short']
    cq_questions = [q for q in questions if q.question_type == 'cq']
    
    return render_template('exam/paper_template.html',
                           school_name=school_name,
                           exam_name=exam_name,
                           class_name=class_name,
                           subject_name=subject_name,
                           time_allowed=time_allowed,
                           total_marks=total_marks,
                           instructions=instructions,
                           mcq_questions=mcq_questions,
                           short_questions=short_questions,
                           cq_questions=cq_questions,
                           total_selected=len(questions))


@app.route('/exam/save', methods=['POST'])
def exam_save():
    payload = request.get_json()
    if not payload:
        return jsonify({'success': False, 'message': 'No data provided'}), 400
    
    paper_id = payload.get('id') or payload.get('paper_id')
    is_update = False
    if paper_id:
        paper = ExamPaper.query.get(paper_id)
        if paper:
            is_update = True
        else:
            paper = ExamPaper()
            db.session.add(paper)
    else:
        paper = ExamPaper()
        db.session.add(paper)
        
    paper.title = payload.get('title', 'সৃজনশীল প্রশ্নপত্র')
    paper.school_name = payload.get('school_name', 'আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়')
    paper.exam_name = payload.get('exam_name', 'অর্ধ-বার্ষিক পরীক্ষা')
    paper.class_id = payload.get('class_id')
    paper.subject_id = payload.get('subject_id')
    paper.time_allowed = payload.get('time_allowed', '২ ঘণ্টা ৩০ মিনিট')
    paper.total_marks = float(payload.get('total_marks', 100))
    paper.instructions = payload.get('instructions', '')
    
    q_ids = payload.get('question_ids', [])
    if isinstance(q_ids, list):
        clean_q_ids = [int(x) for x in q_ids if str(x).strip().isdigit()]
    else:
        clean_q_ids = [int(x) for x in str(q_ids).split(',') if x.strip().isdigit()]
    paper.questions_json = json.dumps(clean_q_ids)
    
    # Auto-infer class_id and subject_id from questions if missing
    if (not paper.class_id or not paper.subject_id) and clean_q_ids:
        first_q = Question.query.filter(Question.id.in_(clean_q_ids)).first()
        if first_q:
            if not paper.class_id:
                paper.class_id = first_q.class_id
            if not paper.subject_id:
                paper.subject_id = first_q.subject_id
    
    db.session.commit()
    return jsonify({
        'success': True,
        'paper_id': paper.id,
        'is_update': is_update,
        'message': 'প্রশ্নপত্রটি সফলভাবে আপডেট ও সংরক্ষিত হয়েছে!' if is_update else 'প্রশ্নপত্রটি সফলভাবে সংরক্ষিত হয়েছে!'
    })


@app.route('/exam/saved')
@app.route('/saved-papers')
def exam_saved_list():
    papers = ExamPaper.query.order_by(ExamPaper.created_at.desc()).all()
    classes = ClassLevel.query.order_by(ClassLevel.order_num, ClassLevel.id).all()
    subjects = Subject.query.order_by(Subject.order_num, Subject.id).all()
    chapters = Chapter.query.order_by(Chapter.order_num, Chapter.id).all()
    
    # Cache question-chapter mapping in one query for ultra-fast lookup
    all_q_tuples = db.session.query(Question.id, Question.chapter_id, Chapter.title, Chapter.chapter_no, Question.subject_id, Question.class_id)\
        .outerjoin(Chapter, Question.chapter_id == Chapter.id).all()
    q_meta_map = {q[0]: {'chapter_id': q[1], 'title': q[2], 'chapter_no': q[3], 'subject_id': q[4], 'class_id': q[5]} for q in all_q_tuples}
    
    papers_data = []
    for p in papers:
        q_ids = []
        try:
            raw = json.loads(p.questions_json or '[]')
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and 'id' in item:
                        q_ids.append(int(item['id']))
                    elif str(item).strip().isdigit():
                        q_ids.append(int(str(item).strip()))
            elif isinstance(raw, dict):
                q_list = raw.get('questions', []) or raw.get('question_ids', [])
                for item in q_list:
                    if isinstance(item, dict) and 'id' in item:
                        q_ids.append(int(item['id']))
                    elif str(item).strip().isdigit():
                        q_ids.append(int(str(item).strip()))
        except Exception:
            q_ids = []
            
        chapter_ids = []
        chapter_names = []
        inferred_subject_id = p.subject_id
        inferred_class_id = p.class_id
        
        for qid in q_ids:
            meta = q_meta_map.get(qid)
            if meta:
                if not inferred_class_id and meta['class_id']:
                    inferred_class_id = meta['class_id']
                if not inferred_subject_id and meta['subject_id']:
                    inferred_subject_id = meta['subject_id']
                if meta['chapter_id']:
                    cid = meta['chapter_id']
                    if cid not in chapter_ids:
                        chapter_ids.append(cid)
                        c_label = f"{meta['chapter_no'] + ': ' if meta['chapter_no'] else ''}{meta['title'] or ''}".strip()
                        if c_label and c_label not in chapter_names:
                            chapter_names.append(c_label)
                            
        # Resolve class and subject names dynamically
        class_obj = p.class_level or (ClassLevel.query.get(inferred_class_id) if inferred_class_id else None)
        subject_obj = p.subject or (Subject.query.get(inferred_subject_id) if inferred_subject_id else None)
        
        papers_data.append({
            'id': p.id,
            'title': p.title,
            'school_name': p.school_name,
            'exam_name': p.exam_name,
            'class_id': inferred_class_id,
            'class_name': class_obj.name if class_obj else '',
            'subject_id': inferred_subject_id,
            'subject_name': subject_obj.name if subject_obj else '',
            'time_allowed': p.time_allowed,
            'total_marks': p.total_marks,
            'instructions': p.instructions,
            'created_at': p.created_at.strftime('%d-%m-%Y') if p.created_at else '',
            'created_at_time': p.created_at.strftime('%I:%M %p') if p.created_at else '',
            'created_at_raw': p.created_at.isoformat() if p.created_at else '',
            'question_count': len(q_ids),
            'chapter_ids': chapter_ids,
            'chapter_names': chapter_names[:3],
            'total_chapters_count': len(chapter_names)
        })
        
    classes_data = [{
        'id': c.id,
        'name': c.name,
        'code': c.code,
        'order_num': c.order_num or 0,
        'paper_count': sum(1 for p in papers_data if p['class_id'] == c.id)
    } for c in classes]
    
    subjects_data = [{
        'id': s.id,
        'class_id': s.class_id,
        'class_name': s.class_level.name if s.class_level else '',
        'name': s.name,
        'code': s.code,
        'order_num': s.order_num or 0,
        'paper_count': sum(1 for p in papers_data if p['subject_id'] == s.id)
    } for s in subjects]
    
    chapters_data = [{
        'id': ch.id,
        'subject_id': ch.subject_id,
        'class_id': ch.subject.class_id if ch.subject else None,
        'class_name': ch.subject.class_level.name if (ch.subject and ch.subject.class_level) else '',
        'subject_name': ch.subject.name if ch.subject else '',
        'chapter_no': ch.chapter_no,
        'title': ch.title,
        'display_name': f"{ch.chapter_no + ': ' if ch.chapter_no else ''}{ch.title}",
        'order_num': ch.order_num or 0,
        'paper_count': sum(1 for p in papers_data if ch.id in p['chapter_ids'])
    } for ch in chapters]
    
    return render_template('exam/saved_list.html',
                           papers_json=json.dumps(papers_data, ensure_ascii=False),
                           classes_json=json.dumps(classes_data, ensure_ascii=False),
                           subjects_json=json.dumps(subjects_data, ensure_ascii=False),
                           chapters_json=json.dumps(chapters_data, ensure_ascii=False),
                           total_papers=len(papers_data))


@app.route('/api/saved-paper/<int:id>/delete', methods=['POST'])
@app.route('/api/exam/paper/<int:id>/delete', methods=['POST'])
def api_saved_paper_delete(id):
    paper = ExamPaper.query.get(id)
    if not paper:
        return jsonify({'success': False, 'message': 'প্রশ্নপত্রটি খুঁজে পাওয়া যায়নি'}), 404
        
    try:
        title = paper.title
        db.session.delete(paper)
        db.session.commit()
        return jsonify({'success': True, 'message': f'"{title}" প্রশ্নপত্রটি সফলভাবে মুছে ফেলা হয়েছে'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'মুছে ফেলতে সমস্যা হয়েছে: {str(e)}'}), 500


@app.route('/exam/<int:id>/view')
def exam_view_saved(id):
    paper = ExamPaper.query.get_or_404(id)
    try:
        q_ids = json.loads(paper.questions_json)
    except Exception:
        q_ids = []
    
    questions = Question.query.filter(Question.id.in_(q_ids)).all() if q_ids else []
    mcq_questions = [q for q in questions if q.question_type == 'mcq']
    short_questions = [q for q in questions if q.question_type == 'short']
    cq_questions = [q for q in questions if q.question_type == 'cq']
    
    return render_template('exam/paper_template.html',
                           school_name=paper.school_name,
                           exam_name=paper.exam_name,
                           class_name=paper.class_level.name if paper.class_level else '',
                           subject_name=paper.subject.name if paper.subject else '',
                           time_allowed=paper.time_allowed,
                           total_marks=to_bangla_number(paper.total_marks),
                           instructions=paper.instructions,
                           mcq_questions=mcq_questions,
                           short_questions=short_questions,
                           cq_questions=cq_questions,
                           total_selected=len(questions),
                           paper_id=paper.id)


# ==========================================
# REST API (Cascading dropdowns & Filters)
# ==========================================

@app.route('/api/classes')
def api_classes():
    classes = ClassLevel.query.order_by(ClassLevel.order_num, ClassLevel.id).all()
    return jsonify([c.to_dict() for c in classes])


@app.route('/api/subjects/<int:class_id>')
def api_subjects(class_id):
    subjects = Subject.query.filter_by(class_id=class_id).order_by(Subject.order_num, Subject.id).all()
    return jsonify([s.to_dict() for s in subjects])


@app.route('/api/chapters/<int:subject_id>')
def api_chapters(subject_id):
    chapters = Chapter.query.filter_by(subject_id=subject_id).order_by(Chapter.order_num, Chapter.id).all()
    return jsonify([ch.to_dict() for ch in chapters])


@app.route('/api/topics/<int:chapter_id>')
def api_topics(chapter_id):
    topics = Topic.query.filter_by(chapter_id=chapter_id).order_by(Topic.order_num, Topic.id).all()
    return jsonify([t.to_dict() for t in topics])


@app.route('/api/chapters-by-subjects')
def api_chapters_by_subjects():
    raw_subject_ids = request.args.getlist('subject_ids') or request.args.getlist('subject_ids[]')
    if not raw_subject_ids and request.args.get('subject_ids'):
        raw_subject_ids = [request.args.get('subject_ids')]
    subject_ids = []
    for s in raw_subject_ids:
        for part in str(s).split(','):
            if part.strip().isdigit():
                subject_ids.append(int(part.strip()))
    if not subject_ids:
        return jsonify([])
    
    chapters = Chapter.query.filter(Chapter.subject_id.in_(subject_ids)).order_by(Chapter.order_num, Chapter.id).all()
    results = []
    for ch in chapters:
        c_dict = ch.to_dict()
        c_dict['subject_name'] = ch.subject.name if ch.subject else ''
        results.append(c_dict)
    return jsonify(results)


@app.route('/api/topics-by-chapters')
def api_topics_by_chapters():
    raw_chapter_ids = request.args.getlist('chapter_ids') or request.args.getlist('chapter_ids[]')
    if not raw_chapter_ids and request.args.get('chapter_ids'):
        raw_chapter_ids = [request.args.get('chapter_ids')]
    chapter_ids = []
    for c in raw_chapter_ids:
        for part in str(c).split(','):
            if part.strip().isdigit():
                chapter_ids.append(int(part.strip()))
    if not chapter_ids:
        return jsonify([])
    
    topics = Topic.query.filter(Topic.chapter_id.in_(chapter_ids)).order_by(Topic.chapter_id, Topic.order_num, Topic.id).all()
    results = []
    for t in topics:
        t_dict = t.to_dict()
        ch = t.chapter
        t_dict['chapter_title'] = ch.title if ch else ''
        t_dict['chapter_no'] = ch.chapter_no if ch else ''
        t_dict['subject_name'] = ch.subject.name if (ch and ch.subject) else ''
        results.append(t_dict)
    return jsonify(results)


@app.route('/api/exams-by-chapters')
def api_exams_by_chapters():
    raw_chapter_ids = request.args.getlist('chapter_ids') or request.args.getlist('chapter_ids[]')
    if not raw_chapter_ids and request.args.get('chapter_ids'):
        raw_chapter_ids = [request.args.get('chapter_ids')]
    chapter_ids = []
    for c in raw_chapter_ids:
        for part in str(c).split(','):
            if part.strip().isdigit():
                chapter_ids.append(int(part.strip()))
                
    # If no explicit chapter_ids, try resolving via subject_ids
    if not chapter_ids:
        raw_subject_ids = request.args.getlist('subject_ids') or request.args.getlist('subject_ids[]')
        if not raw_subject_ids and request.args.get('subject_ids'):
            raw_subject_ids = [request.args.get('subject_ids')]
        sub_ids = []
        for s in raw_subject_ids:
            for part in str(s).split(','):
                if part.strip().isdigit():
                    sub_ids.append(int(part.strip()))
        if sub_ids:
            c_tuples = db.session.query(Chapter.id).filter(Chapter.subject_id.in_(sub_ids)).all()
            chapter_ids = [c[0] for c in c_tuples]
            
    if not chapter_ids:
        return jsonify([])
    
    # Exclude ongoing / active paper if specified
    exclude_paper_id = request.args.get('exclude_paper_id') or request.args.get('exclude_id')
    exclude_id = None
    if exclude_paper_id and str(exclude_paper_id).strip().isdigit():
        exclude_id = int(str(exclude_paper_id).strip())

    # Get all question IDs for these chapters
    chapter_q_tuples = db.session.query(Question.id).filter(Question.chapter_id.in_(chapter_ids)).all()
    if not chapter_q_tuples:
        return jsonify([])
    chapter_q_set = {q[0] for q in chapter_q_tuples}
    
    # Query all saved exam papers
    papers = ExamPaper.query.order_by(ExamPaper.created_at.desc()).all()
    results = []
    for p in papers:
        if exclude_id is not None and p.id == exclude_id:
            continue
        p_q_ids = set()
        try:
            raw = json.loads(p.questions_json or '[]')
            if isinstance(raw, list):
                for item in raw:
                    if isinstance(item, dict) and 'id' in item:
                        p_q_ids.add(int(item['id']))
                    elif str(item).strip().isdigit():
                        p_q_ids.add(int(str(item).strip()))
            elif isinstance(raw, dict):
                q_list = raw.get('questions', []) or raw.get('question_ids', [])
                for item in q_list:
                    if isinstance(item, dict) and 'id' in item:
                        p_q_ids.add(int(item['id']))
                    elif str(item).strip().isdigit():
                        p_q_ids.add(int(str(item).strip()))
        except Exception:
            p_q_ids = set()
        
        common_ids = chapter_q_set.intersection(p_q_ids)
        if common_ids:
            results.append({
                'id': p.id,
                'title': p.title,
                'exam_name': p.exam_name,
                'school_name': p.school_name,
                'class_name': p.class_level.name if p.class_level else '',
                'subject_name': p.subject.name if p.subject else '',
                'total_marks': p.total_marks,
                'created_at': p.created_at.strftime('%d/%m/%Y') if p.created_at else '',
                'matched_question_count': len(common_ids),
                'matched_question_ids': list(common_ids),
                'total_question_count': len(p_q_ids)
            })
            
    return jsonify(results)


@app.route('/api/questions')
def api_questions():
    class_id = request.args.get('class_id', type=int)
    topic_id = request.args.get('topic_id', type=int)
    q_type = request.args.get('question_type') or request.args.get('type')
    difficulty = request.args.get('difficulty')
    search = request.args.get('search', '').strip()

    # Multi-subject filtering support
    raw_subject_ids = request.args.getlist('subject_ids') or request.args.getlist('subject_ids[]')
    if not raw_subject_ids and request.args.get('subject_ids'):
        raw_subject_ids = request.args.get('subject_ids', '').split(',')
    subject_ids = []
    for s in raw_subject_ids:
        for part in str(s).split(','):
            if part.strip().isdigit():
                subject_ids.append(int(part.strip()))
    if not subject_ids:
        single_sub = request.args.get('subject_id', type=int)
        if single_sub:
            subject_ids.append(single_sub)

    # Multi-chapter filtering support
    raw_chapter_ids = request.args.getlist('chapter_ids') or request.args.getlist('chapter_ids[]')
    if not raw_chapter_ids and request.args.get('chapter_ids'):
        raw_chapter_ids = request.args.get('chapter_ids', '').split(',')
    chapter_ids = []
    for c in raw_chapter_ids:
        for part in str(c).split(','):
            if part.strip().isdigit():
                chapter_ids.append(int(part.strip()))
    if not chapter_ids:
        single_chap = request.args.get('chapter_id', type=int)
        if single_chap:
            chapter_ids.append(single_chap)

    # Multi-topic filtering support
    raw_topic_ids = request.args.getlist('topic_ids') or request.args.getlist('topic_ids[]')
    if not raw_topic_ids and request.args.get('topic_ids'):
        raw_topic_ids = request.args.get('topic_ids', '').split(',')
    topic_ids = []
    for t in raw_topic_ids:
        for part in str(t).split(','):
            if part.strip().isdigit():
                topic_ids.append(int(part.strip()))
    if not topic_ids and topic_id:
        topic_ids.append(topic_id)
    
    # Pagination parameters
    page = request.args.get('page', type=int)
    per_page = request.args.get('per_page', default=50, type=int)
    paginate_requested = request.args.get('paginate', default='').lower() in ['true', '1', 'yes'] or (page is not None)

    query = Question.query

    if class_id:
        query = query.filter(Question.class_id == class_id)
    if subject_ids:
        query = query.filter(Question.subject_id.in_(subject_ids))
    if chapter_ids:
        query = query.filter(Question.chapter_id.in_(chapter_ids))
    if q_type and q_type != 'all':
        type_list = [t.strip().lower() for t in q_type.split(',') if t.strip() and t.strip().lower() != 'all']
        if len(type_list) == 1:
            query = query.filter(Question.question_type == type_list[0])
        elif len(type_list) > 1:
            query = query.filter(Question.question_type.in_(type_list))
    if difficulty and difficulty != 'all':
        query = query.filter(Question.difficulty == difficulty)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Question.mcq_stem.ilike(search_pattern),
                Question.short_question.ilike(search_pattern),
                Question.cq_stem.ilike(search_pattern),
                Question.cq_sub_ka.ilike(search_pattern)
            )
        )

    # Order: 1. MCQ -> 2. Short Question -> 3. Creative Question (CQ)
    type_order = db.case(
        (Question.question_type == 'mcq', 1),
        (Question.question_type == 'short', 2),
        (Question.question_type == 'cq', 3),
        else_=4
    )
    query = query.order_by(type_order, Question.created_at.desc(), Question.id.desc())

    if paginate_requested:
        page_num = max(page or 1, 1)
        page_size = min(max(per_page, 1), 200)
        pagination = db.paginate(query, page=page_num, per_page=page_size, error_out=False)
        return jsonify({
            'items': [q.to_dict() for q in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num
        })

    questions = query.all()
    return jsonify([q.to_dict() for q in questions])


@app.route('/api/questions/<int:id>')
def api_question_detail(id):
    question = Question.query.get_or_404(id)
    return jsonify(question.to_dict())


# ==========================================
# SCHOOL / INSTITUTION PROFILE (MY প্রোফাইল)
# ==========================================

@app.route('/settings/school-profile', methods=['GET', 'POST'])
@app.route('/school-profile', methods=['GET', 'POST'])
def school_profile_view():
    profile = get_or_create_school_profile()
    if request.method == 'POST':
        data = request.form
        profile.school_name_bn = data.get('school_name_bn', profile.school_name_bn).strip()
        profile.school_name_en = data.get('school_name_en', profile.school_name_en).strip()
        profile.eiin_number = data.get('eiin_number', profile.eiin_number).strip()
        profile.school_code = data.get('school_code', profile.school_code).strip()
        profile.center_code = data.get('center_code', profile.center_code).strip()
        profile.board_name = data.get('board_name', profile.board_name).strip()
        profile.institute_type = data.get('institute_type', profile.institute_type).strip()
        profile.shift = data.get('shift', profile.shift).strip()
        profile.estd_year = data.get('estd_year', profile.estd_year).strip()
        profile.motto = data.get('motto', profile.motto).strip()
        profile.address = data.get('address', profile.address).strip()
        profile.post_office = data.get('post_office', profile.post_office).strip()
        profile.post_code = data.get('post_code', profile.post_code).strip()
        profile.upazila = data.get('upazila', profile.upazila).strip()
        profile.district = data.get('district', profile.district).strip()
        profile.division = data.get('division', profile.division).strip()
        profile.phone = data.get('phone', profile.phone).strip()
        profile.email = data.get('email', profile.email).strip()
        profile.website = data.get('website', profile.website).strip()
        profile.headmaster_name = data.get('headmaster_name', profile.headmaster_name).strip()
        profile.headmaster_title = data.get('headmaster_title', profile.headmaster_title).strip()
        profile.headmaster_phone = data.get('headmaster_phone', profile.headmaster_phone).strip()
        profile.headmaster_email = data.get('headmaster_email', profile.headmaster_email).strip()
        profile.signature_text = data.get('signature_text', profile.signature_text).strip()
        profile.default_exam_header = data.get('default_exam_header', profile.default_exam_header).strip()
        profile.default_time_allowed = data.get('default_time_allowed', profile.default_time_allowed).strip()
        profile.default_instructions = data.get('default_instructions', profile.default_instructions).strip()
        profile.watermark_text = data.get('watermark_text', profile.watermark_text).strip()
        
        # Check logo file upload if provided
        if 'logo_file' in request.files:
            file = request.files['logo_file']
            if file and file.filename:
                import os
                ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
                if ext in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
                    filename = f"school_logo_{int(time.time())}.{ext}"
                    upload_folder = os.path.join(app.root_path, 'static', 'img')
                    os.makedirs(upload_folder, exist_ok=True)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    profile.logo_path = f"/static/img/{filename}"

        db.session.commit()
        flash('বিদ্যালয় প্রোফাইলের তথ্য সফলভাবে সংরক্ষণ ও আপডেট করা হয়েছে!', 'success')
        return redirect(url_for('school_profile_view'))
        
    return render_template('school_profile.html', profile=profile)


@app.route('/api/school-profile/get')
def api_school_profile_get():
    profile = get_or_create_school_profile()
    return jsonify({'success': True, 'data': profile.to_dict()})


@app.route('/api/school-profile/save', methods=['POST'])
def api_school_profile_save():
    profile = get_or_create_school_profile()
    data = request.get_json(silent=True) or request.form.to_dict() or {}
    
    if not data:
        return jsonify({'success': False, 'message': 'কোনো তথ্য পাওয়া যায়নি'}), 400
        
    if 'school_name_bn' in data and data['school_name_bn'].strip():
        profile.school_name_bn = data['school_name_bn'].strip()
    if 'school_name_en' in data:
        profile.school_name_en = data['school_name_en'].strip()
    if 'eiin_number' in data:
        profile.eiin_number = data['eiin_number'].strip()
    if 'school_code' in data:
        profile.school_code = data['school_code'].strip()
    if 'center_code' in data:
        profile.center_code = data['center_code'].strip()
    if 'board_name' in data:
        profile.board_name = data['board_name'].strip()
    if 'institute_type' in data:
        profile.institute_type = data['institute_type'].strip()
    if 'shift' in data:
        profile.shift = data['shift'].strip()
    if 'estd_year' in data:
        profile.estd_year = data['estd_year'].strip()
    if 'motto' in data:
        profile.motto = data['motto'].strip()
    if 'address' in data:
        profile.address = data['address'].strip()
    if 'post_office' in data:
        profile.post_office = data['post_office'].strip()
    if 'post_code' in data:
        profile.post_code = data['post_code'].strip()
    if 'upazila' in data:
        profile.upazila = data['upazila'].strip()
    if 'district' in data:
        profile.district = data['district'].strip()
    if 'division' in data:
        profile.division = data['division'].strip()
    if 'phone' in data:
        profile.phone = data['phone'].strip()
    if 'email' in data:
        profile.email = data['email'].strip()
    if 'website' in data:
        profile.website = data['website'].strip()
    if 'headmaster_name' in data:
        profile.headmaster_name = data['headmaster_name'].strip()
    if 'headmaster_title' in data:
        profile.headmaster_title = data['headmaster_title'].strip()
    if 'headmaster_phone' in data:
        profile.headmaster_phone = data['headmaster_phone'].strip()
    if 'headmaster_email' in data:
        profile.headmaster_email = data['headmaster_email'].strip()
    if 'signature_text' in data:
        profile.signature_text = data['signature_text'].strip()
    if 'logo_path' in data and data['logo_path'].strip():
        profile.logo_path = data['logo_path'].strip()
    if 'default_exam_header' in data:
        profile.default_exam_header = data['default_exam_header'].strip()
    if 'default_time_allowed' in data:
        profile.default_time_allowed = data['default_time_allowed'].strip()
    if 'default_instructions' in data:
        profile.default_instructions = data['default_instructions'].strip()
    if 'watermark_text' in data:
        profile.watermark_text = data['watermark_text'].strip()

    # Handle direct logo file in multipart/form-data
    if 'logo_file' in request.files:
        file = request.files['logo_file']
        if file and file.filename:
            import os
            ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
            if ext in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
                filename = f"school_logo_{int(time.time())}.{ext}"
                upload_folder = os.path.join(app.root_path, 'static', 'img')
                os.makedirs(upload_folder, exist_ok=True)
                filepath = os.path.join(upload_folder, filename)
                file.save(filepath)
                profile.logo_path = f"/static/img/{filename}"

    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'বিদ্যালয়ের প্রোফাইল সফলভাবে ডাটাবেজে সংরক্ষিত ও আপডেট করা হয়েছে!',
            'data': profile.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'সংরক্ষণে ত্রুটি: {str(e)}'}), 500


@app.route('/api/school-profile/logo-upload', methods=['POST'])
def api_school_profile_logo_upload():
    if 'logo_file' not in request.files:
        return jsonify({'success': False, 'message': 'কোনো ফাইল নির্বাচন করা হয়নি'}), 400
    file = request.files['logo_file']
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'অকার্যকর ফাইল'}), 400
        
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'png'
    if ext not in ['png', 'jpg', 'jpeg', 'svg', 'webp']:
        return jsonify({'success': False, 'message': 'অনুমোদিত ফরম্যাট: PNG, JPG, JPEG, SVG, WEBP'}), 400
        
    filename = f"school_logo_{int(time.time())}.{ext}"
    upload_folder = os.path.join(app.root_path, 'static', 'img')
    os.makedirs(upload_folder, exist_ok=True)
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)
    
    profile = get_or_create_school_profile()
    profile.logo_path = f"/static/img/{filename}"
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'লোগো সফলভাবে আপলোড করা হয়েছে!',
        'logo_url': profile.logo_path
    })


# ==========================================
# SETTINGS & CURRICULUM MANAGEMENT
# ==========================================

@app.route('/settings')
def settings_view():
    classes = ClassLevel.query.order_by(ClassLevel.order_num, ClassLevel.id).all()
    total_classes = ClassLevel.query.count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_topics = Topic.query.count()
    total_questions = Question.query.count()
    
    return render_template('settings.html',
                           classes=classes,
                           total_classes=total_classes,
                           total_subjects=total_subjects,
                           total_chapters=total_chapters,
                           total_topics=total_topics,
                           total_questions=total_questions)


@app.route('/api/settings/summary')
def api_settings_summary():
    return jsonify({
        'total_classes': ClassLevel.query.count(),
        'total_subjects': Subject.query.count(),
        'total_chapters': Chapter.query.count(),
        'total_topics': Topic.query.count(),
        'total_questions': Question.query.count()
    })


# --- CLASS LEVEL CRUD ---

@app.route('/api/settings/classes')
def api_settings_get_classes():
    search = request.args.get('search', '').strip().lower()
    query = ClassLevel.query
    if search:
        query = query.filter(db.or_(
            ClassLevel.name.ilike(f"%{search}%"),
            ClassLevel.code.ilike(f"%{search}%")
        ))
    classes = query.order_by(ClassLevel.order_num, ClassLevel.id).all()
    
    result = []
    for c in classes:
        # Count total chapters and questions across subjects of this class
        sub_count = len(c.subjects)
        chap_count = sum(len(s.chapters) for s in c.subjects)
        q_count = len(c.questions)
        result.append({
            'id': c.id,
            'name': c.name,
            'code': c.code or '',
            'order_num': c.order_num or 0,
            'subject_count': sub_count,
            'chapter_count': chap_count,
            'question_count': q_count
        })
    return jsonify(result)


@app.route('/api/settings/class/create', methods=['POST'])
def api_settings_create_class():
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    order_num = data.get('order_num', 0)
    
    if not name:
        return jsonify({'success': False, 'message': 'শ্রেণির নাম অবশ্যই দিতে হবে'}), 400
        
    existing = ClassLevel.query.filter_by(name=name).first()
    if existing:
        return jsonify({'success': False, 'message': f'"{name}" নামে শ্রেণি ইতিমধ্যে বিদ্যমান আছে'}), 400
        
    try:
        order_num = int(order_num) if order_num else 0
    except ValueError:
        order_num = 0
        
    new_class = ClassLevel(name=name, code=code, order_num=order_num)
    db.session.add(new_class)
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{name}" শ্রেণি সফলভাবে যুক্ত হয়েছে', 'data': new_class.to_dict()})


@app.route('/api/settings/class/<int:id>/update', methods=['POST'])
def api_settings_update_class(id):
    c = ClassLevel.query.get_or_404(id)
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    order_num = data.get('order_num')
    
    if not name:
        return jsonify({'success': False, 'message': 'শ্রেণির নাম খালি রাখা যাবে না'}), 400
        
    existing = ClassLevel.query.filter(ClassLevel.name == name, ClassLevel.id != id).first()
    if existing:
        return jsonify({'success': False, 'message': f'"{name}" নামে অন্য একটি শ্রেণি বিদ্যমান আছে'}), 400
        
    c.name = name
    c.code = code
    if order_num is not None:
        try:
            c.order_num = int(order_num)
        except ValueError:
            pass
            
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{name}" শ্রেণির তথ্য আপডেট হয়েছে', 'data': c.to_dict()})


@app.route('/api/settings/class/<int:id>/delete', methods=['POST'])
def api_settings_delete_class(id):
    c = ClassLevel.query.get_or_404(id)
    name = c.name
    sub_count = len(c.subjects)
    q_count = len(c.questions)
    
    db.session.delete(c)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': f'"{name}" শ্রেণি এবং এর অন্তর্ভুক্ত {sub_count}টি বিষয় ও {q_count}টি প্রশ্ন সফলভাবে মুছে ফেলা হয়েছে'
    })


# --- REORDER API (CLASSES, SUBJECTS, CHAPTERS, TOPICS) ---

@app.route('/api/settings/reorder', methods=['POST'])
def api_settings_reorder():
    """
    ⚡ Reorder items (classes, subjects, chapters, topics)
    Payload: {
        "type": "class" | "subject" | "chapter" | "topic",
        "orders": [{"id": 1, "order_num": 1}, ...],
        "ordered_ids": [1, 2, 3, ...]
    }
    """
    data = request.get_json(force=True) or {}
    item_type = data.get('type')
    orders = data.get('orders', [])
    ordered_ids = data.get('ordered_ids', [])
    
    if ordered_ids and not orders:
        orders = [{'id': item_id, 'order_num': idx + 1} for idx, item_id in enumerate(ordered_ids)]
        
    if not item_type or not orders:
        return jsonify({'success': False, 'message': 'অকার্যকর ডাটা পাঠানো হয়েছে'}), 400
        
    model_map = {
        'class': ClassLevel,
        'subject': Subject,
        'chapter': Chapter,
        'topic': Topic
    }
    
    model = model_map.get(item_type)
    if not model:
        return jsonify({'success': False, 'message': 'অজানা আইটেম টাইপ'}), 400
        
    try:
        for item in orders:
            item_id = item.get('id')
            order_val = item.get('order_num', 0)
            if item_id is not None:
                record = model.query.get(item_id)
                if record:
                    record.order_num = int(order_val)
                    
        db.session.commit()
        return jsonify({'success': True, 'message': 'ক্রম সফলভাবে সাজানো হয়েছে'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ক্রম সংরক্ষণে সমস্যা: {str(e)}'}), 500


# --- SUBJECT CRUD ---

@app.route('/api/settings/subjects')
def api_settings_get_subjects():
    class_id = request.args.get('class_id', type=int)
    search = request.args.get('search', '').strip().lower()
    
    query = Subject.query
    if class_id:
        query = query.filter(Subject.class_id == class_id)
    if search:
        query = query.filter(db.or_(
            Subject.name.ilike(f"%{search}%"),
            Subject.code.ilike(f"%{search}%")
        ))
        
    subjects = query.join(ClassLevel).order_by(ClassLevel.order_num, Subject.order_num, Subject.id).all()
    
    result = []
    for s in subjects:
        top_count = sum(len(ch.topics) for ch in s.chapters)
        result.append({
            'id': s.id,
            'class_id': s.class_id,
            'class_name': s.class_level.name if s.class_level else '',
            'name': s.name,
            'code': s.code or '',
            'order_num': s.order_num or 0,
            'chapter_count': len(s.chapters),
            'topic_count': top_count,
            'question_count': len(s.questions)
        })
    return jsonify(result)


@app.route('/api/settings/subject/create', methods=['POST'])
def api_settings_create_subject():
    data = request.get_json() or request.form
    class_id = data.get('class_id')
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    order_num = data.get('order_num', 0)
    
    if not (class_id and name):
        return jsonify({'success': False, 'message': 'শ্রেণি এবং বিষয়ের নাম অবশ্যই নির্বাচন করতে হবে'}), 400
        
    try:
        class_id = int(class_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'অকার্যকর শ্রেণি আইডি'}), 400
        
    cls = ClassLevel.query.get(class_id)
    if not cls:
        return jsonify({'success': False, 'message': 'নির্বাচিত শ্রেণি পাওয়া যায়নি'}), 404
        
    existing = Subject.query.filter_by(class_id=class_id, name=name).first()
    if existing:
        return jsonify({'success': False, 'message': f'"{cls.name}" শ্রেণিতে "{name}" বিষয় ইতিমধ্যে বিদ্যমান'}), 400
        
    try:
        order_num = int(order_num) if order_num else 0
    except ValueError:
        order_num = 0

    new_sub = Subject(class_id=class_id, name=name, code=code, order_num=order_num)
    db.session.add(new_sub)
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{name}" বিষয় সফলভাবে যুক্ত হয়েছে', 'data': new_sub.to_dict()})


@app.route('/api/settings/subject/<int:id>/update', methods=['POST'])
def api_settings_update_subject(id):
    s = Subject.query.get_or_404(id)
    data = request.get_json() or request.form
    name = data.get('name', '').strip()
    code = data.get('code', '').strip()
    class_id = data.get('class_id')
    order_num = data.get('order_num')
    
    if not name:
        return jsonify({'success': False, 'message': 'বিষয়ের নাম খালি রাখা যাবে না'}), 400
        
    if class_id:
        try:
            class_id = int(class_id)
            if class_id != s.class_id:
                cls = ClassLevel.query.get(class_id)
                if cls:
                    s.class_id = class_id
        except ValueError:
            pass
            
    existing = Subject.query.filter(Subject.class_id == s.class_id, Subject.name == name, Subject.id != id).first()
    if existing:
        return jsonify({'success': False, 'message': f'এই শ্রেণিতে "{name}" নামে আরেকটি বিষয় বিদ্যমান আছে'}), 400
        
    s.name = name
    s.code = code
    if order_num is not None:
        try:
            s.order_num = int(order_num)
        except ValueError:
            pass

    db.session.commit()
    return jsonify({'success': True, 'message': f'"{name}" বিষয়ের তথ্য আপডেট হয়েছে', 'data': s.to_dict()})


@app.route('/api/settings/subject/<int:id>/delete', methods=['POST'])
def api_settings_delete_subject(id):
    s = Subject.query.get_or_404(id)
    name = s.name
    chap_count = len(s.chapters)
    q_count = len(s.questions)
    
    db.session.delete(s)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': f'"{name}" বিষয় এবং এর অধীনস্থ {chap_count}টি অধ্যায় ও {q_count}টি প্রশ্ন সফলভাবে মুছে ফেলা হয়েছে'
    })


# --- CHAPTER CRUD ---

@app.route('/api/settings/chapters')
def api_settings_get_chapters():
    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    search = request.args.get('search', '').strip().lower()
    
    query = Chapter.query.join(Subject).join(ClassLevel)
    if subject_id:
        query = query.filter(Chapter.subject_id == subject_id)
    elif class_id:
        query = query.filter(Subject.class_id == class_id)
        
    if search:
        query = query.filter(db.or_(
            Chapter.title.ilike(f"%{search}%"),
            Chapter.chapter_no.ilike(f"%{search}%")
        ))
        
    chapters = query.order_by(ClassLevel.order_num, Subject.order_num, Chapter.order_num, Chapter.id).all()
    
    result = []
    for ch in chapters:
        result.append({
            'id': ch.id,
            'subject_id': ch.subject_id,
            'subject_name': ch.subject.name if ch.subject else '',
            'class_id': ch.subject.class_id if ch.subject else None,
            'class_name': ch.subject.class_level.name if (ch.subject and ch.subject.class_level) else '',
            'chapter_no': ch.chapter_no or '',
            'title': ch.title,
            'order_num': ch.order_num or 0,
            'display_name': ch.to_dict().get('display_name', ch.title),
            'topic_count': len(ch.topics),
            'question_count': len(ch.questions)
        })
    return jsonify(result)


@app.route('/api/settings/chapter/create', methods=['POST'])
def api_settings_create_chapter():
    data = request.get_json() or request.form
    subject_id = data.get('subject_id')
    chapter_no = data.get('chapter_no', '').strip()
    title = data.get('title', '').strip()
    order_num = data.get('order_num', 0)
    
    if not (subject_id and title):
        return jsonify({'success': False, 'message': 'বিষয় এবং অধ্যায়ের নাম অবশ্যই দিতে হবে'}), 400
        
    try:
        subject_id = int(subject_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'অকার্যকর বিষয় আইডি'}), 400
        
    sub = Subject.query.get(subject_id)
    if not sub:
        return jsonify({'success': False, 'message': 'নির্বাচিত বিষয় পাওয়া যায়নি'}), 404
        
    try:
        order_num = int(order_num) if order_num else 0
    except ValueError:
        order_num = 0

    new_ch = Chapter(subject_id=subject_id, chapter_no=chapter_no, title=title, order_num=order_num)
    db.session.add(new_ch)
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{title}" অধ্যায় সফলভাবে যুক্ত হয়েছে', 'data': new_ch.to_dict()})


@app.route('/api/settings/chapter/<int:id>/update', methods=['POST'])
def api_settings_update_chapter(id):
    ch = Chapter.query.get_or_404(id)
    data = request.get_json() or request.form
    chapter_no = data.get('chapter_no', '').strip()
    title = data.get('title', '').strip()
    subject_id = data.get('subject_id')
    order_num = data.get('order_num')
    
    if not title:
        return jsonify({'success': False, 'message': 'অধ্যায়ের নাম খালি রাখা যাবে না'}), 400
        
    if subject_id:
        try:
            subject_id = int(subject_id)
            if subject_id != ch.subject_id:
                sub = Subject.query.get(subject_id)
                if sub:
                    ch.subject_id = subject_id
        except ValueError:
            pass
            
    ch.chapter_no = chapter_no
    ch.title = title
    if order_num is not None:
        try:
            ch.order_num = int(order_num)
        except ValueError:
            pass

    db.session.commit()
    return jsonify({'success': True, 'message': f'"{title}" অধ্যায়ের তথ্য আপডেট হয়েছে', 'data': ch.to_dict()})


@app.route('/api/settings/chapter/<int:id>/delete', methods=['POST'])
def api_settings_delete_chapter(id):
    ch = Chapter.query.get_or_404(id)
    title = ch.title
    top_count = len(ch.topics)
    q_count = len(ch.questions)
    
    db.session.delete(ch)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': f'"{title}" অধ্যায় এবং এর অধীনস্থ {top_count}টি টপিক ও {q_count}টি প্রশ্ন সফলভাবে মুছে ফেলা হয়েছে'
    })


# --- TOPIC / LESSON CRUD ---

@app.route('/api/settings/topics')
def api_settings_get_topics():
    class_id = request.args.get('class_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    chapter_id = request.args.get('chapter_id', type=int)
    search = request.args.get('search', '').strip().lower()
    
    query = Topic.query.join(Chapter).join(Subject)
    if chapter_id:
        query = query.filter(Topic.chapter_id == chapter_id)
    elif subject_id:
        query = query.filter(Chapter.subject_id == subject_id)
    elif class_id:
        query = query.filter(Subject.class_id == class_id)
        
    if search:
        query = query.filter(Topic.title.ilike(f"%{search}%"))
        
    topics = query.order_by(Chapter.id, Topic.order_num, Topic.id).all()
    
    result = []
    for t in topics:
        ch = t.chapter
        sub = ch.subject if ch else None
        cls = sub.class_level if sub else None
        result.append({
            'id': t.id,
            'chapter_id': t.chapter_id,
            'chapter_name': ch.title if ch else '',
            'chapter_no': ch.chapter_no if ch else '',
            'subject_id': sub.id if sub else None,
            'subject_name': sub.name if sub else '',
            'class_id': cls.id if cls else None,
            'class_name': cls.name if cls else '',
            'title': t.title,
            'order_num': t.order_num or 0,
            'question_count': len(t.questions)
        })
    return jsonify(result)


@app.route('/api/settings/topic/create', methods=['POST'])
def api_settings_create_topic():
    data = request.get_json() or request.form
    chapter_id = data.get('chapter_id')
    title = data.get('title', '').strip()
    order_num = data.get('order_num', 0)
    
    if not (chapter_id and title):
        return jsonify({'success': False, 'message': 'অধ্যায় এবং টপিক/পাঠের নাম অবশ্যই দিতে হবে'}), 400
        
    try:
        chapter_id = int(chapter_id)
    except ValueError:
        return jsonify({'success': False, 'message': 'অকার্যকর অধ্যায় আইডি'}), 400
        
    ch = Chapter.query.get(chapter_id)
    if not ch:
        return jsonify({'success': False, 'message': 'নির্বাচিত অধ্যায় পাওয়া যায়নি'}), 404
        
    try:
        order_num = int(order_num) if order_num else 0
    except ValueError:
        order_num = 0
        
    new_t = Topic(chapter_id=chapter_id, title=title, order_num=order_num)
    db.session.add(new_t)
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{title}" টপিক/পাঠ সফলভাবে যুক্ত হয়েছে', 'data': new_t.to_dict()})


@app.route('/api/settings/topic/<int:id>/update', methods=['POST'])
def api_settings_update_topic(id):
    t = Topic.query.get_or_404(id)
    data = request.get_json() or request.form
    title = data.get('title', '').strip()
    order_num = data.get('order_num')
    chapter_id = data.get('chapter_id')
    
    if not title:
        return jsonify({'success': False, 'message': 'টপিক/পাঠের নাম খালি রাখা যাবে না'}), 400
        
    if chapter_id:
        try:
            chapter_id = int(chapter_id)
            if chapter_id != t.chapter_id:
                ch = Chapter.query.get(chapter_id)
                if ch:
                    t.chapter_id = chapter_id
        except ValueError:
            pass
            
    t.title = title
    if order_num is not None:
        try:
            t.order_num = int(order_num)
        except ValueError:
            pass
            
    db.session.commit()
    return jsonify({'success': True, 'message': f'"{title}" টপিক/পাঠের তথ্য আপডেট হয়েছে', 'data': t.to_dict()})


@app.route('/api/settings/topic/<int:id>/delete', methods=['POST'])
def api_settings_delete_topic(id):
    t = Topic.query.get_or_404(id)
    title = t.title
    q_count = len(t.questions)
    
    db.session.delete(t)
    db.session.commit()
    return jsonify({
        'success': True, 
        'message': f'"{title}" টপিক এবং এর সাথে যুক্ত {q_count}টি প্রশ্ন সফলভাবে মুছে ফেলা হয়েছে'
    })


# Backward compatible quick create routes
@app.route('/api/classes/create', methods=['POST'])
def api_create_class():
    data = request.get_json()
    name = data.get('name')
    if not name:
        return jsonify({'error': 'Name is required'}), 400
    new_class = ClassLevel(name=name, code=data.get('code', ''))
    db.session.add(new_class)
    db.session.commit()
    return jsonify(new_class.to_dict())


@app.route('/api/subjects/create', methods=['POST'])
def api_create_subject():
    data = request.get_json()
    class_id = data.get('class_id')
    name = data.get('name')
    if not (class_id and name):
        return jsonify({'error': 'class_id and name are required'}), 400
    new_subject = Subject(class_id=class_id, name=name, code=data.get('code', ''))
    db.session.add(new_subject)
    db.session.commit()
    return jsonify(new_subject.to_dict())


@app.route('/api/chapters/create', methods=['POST'])
def api_create_chapter():
    data = request.get_json()
    subject_id = data.get('subject_id')
    title = data.get('title')
    chapter_no = data.get('chapter_no', '')
    if not (subject_id and title):
        return jsonify({'error': 'subject_id and title are required'}), 400
    new_chapter = Chapter(subject_id=subject_id, chapter_no=chapter_no, title=title)
    db.session.add(new_chapter)
    db.session.commit()
    return jsonify(new_chapter.to_dict())


@app.route('/api/topics/create', methods=['POST'])
def api_create_topic():
    data = request.get_json()
    chapter_id = data.get('chapter_id')
    title = data.get('title')
    if not (chapter_id and title):
        return jsonify({'error': 'chapter_id and title are required'}), 400
    new_topic = Topic(chapter_id=chapter_id, title=title)
    db.session.add(new_topic)
    db.session.commit()
    return jsonify(new_topic.to_dict())


if __name__ == '__main__':
    seed_database()
    app.run(debug=True, port=5000)

