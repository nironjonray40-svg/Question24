import os
import io
import csv
import json
import time
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from markupsafe import Markup
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Response, make_response, session
from sqlalchemy import event
from sqlalchemy.engine import Engine
from models import db, ClassLevel, Subject, Chapter, Topic, Question, ExamPaper, SchoolProfile, User, RolePermissionConfig

app = Flask(__name__)
app.config['SECRET_KEY'] = 'bangladesh-school-question-bank-secret-2026'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///question_bank.db'
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

# Helper function to normalize Bengali/English mobile numbers into clean digit string
def normalize_mobile_number(mobile_str):
    if not mobile_str:
        return ""
    bn_to_en = {'০': '0', '১': '1', '২': '2', '৩': '3', '৪': '4', '৫': '5', '৬': '6', '৭': '7', '৮': '8', '৯': '9'}
    cleaned = ''.join(bn_to_en.get(char, char) for char in str(mobile_str).strip())
    # Keep only digits and plus
    cleaned = re.sub(r'[^\d+]', '', cleaned)
    # Remove leading +88 or 88 if present
    if cleaned.startswith('+8801'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('8801'):
        cleaned = cleaned[2:]
    elif cleaned.startswith('+88'):
        cleaned = cleaned[3:]
    elif cleaned.startswith('88'):
        cleaned = cleaned[2:]
    return cleaned.strip()

# ==========================================
# USER SUBSCRIPTION & ACTIVE VALIDITY SYSTEM
# ==========================================
SUBSCRIPTION_EXPIRED_MESSAGE = "আপনার স্বস্ক্রিবশনের মেয়াদ শেষ হয়েছে। পুনরায় স্বস্ক্রিবশনের জন্য যোগাযোগ: 01741697205. ধন্যবাদ"

def get_now_dhaka():
    """Returns current date and time in Bangladesh Standard Time (UTC+6) as a naive datetime"""
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=6))).replace(tzinfo=None)

def parse_datetime_input(val):
    """Parses various datetime input strings (HTML datetime-local, ISO, etc.) into naive datetime"""
    if not val:
        return None
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ['none', 'null', '']:
        return None
    for fmt in ['%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M', '%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d']:
        try:
            return datetime.strptime(val_str, fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(val_str.replace('Z', ''))
    except Exception:
        return None

def check_user_subscription(user):
    """
    Validates whether the user is permitted to log in according to access_start and access_end.
    Returns (is_active: bool, error_message: str)
    Super Admin accounts are always unrestricted.
    """
    if not user:
        return False, "ইউজার পাওয়া যায়নি।"
    if user.is_super_admin_user or str(user.mobile or '').strip() in ['01794918384', '01700000000']:
        return True, None
        
    now = get_now_dhaka()
    
    # Check if currently outside the allowed scheduled time window
    is_outside = False
    if user.access_start and now < user.access_start:
        is_outside = True
    if user.access_end and now > user.access_end:
        is_outside = True
        
    if is_outside:
        return False, SUBSCRIPTION_EXPIRED_MESSAGE
        
    return True, None

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


def is_current_user_super_admin():
    """Checks whether current session user is authenticated as Super Admin (প্রধান অ্যাডমিন)"""
    sess_user = session.get('user')
    if not sess_user:
        return False
    # Check primary super admin mobile numbers
    if str(sess_user.get('mobile') or '').strip() in ['01794918384', '01700000000']:
        return True
    # Check role in session
    role_lower = str(sess_user.get('role') or '').lower()
    if 'সুপার' in role_lower or 'super admin' in role_lower or 'superadmin' in role_lower:
        return True
    # Cross-verify with database record if user ID is present
    user_id = sess_user.get('id')
    if user_id:
        try:
            db_user = db.session.get(User, user_id)
            if db_user and db_user.is_super_admin_user:
                return True
        except Exception:
            pass
    return False


# ==========================================
# INSTITUTIONAL ROLE PERMISSION SYSTEM
# ==========================================

DEFAULT_ROLE_PERMISSIONS = {
    "সুপার অ্যাডমিন": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": True,
        "can_view_users": True,
        "can_manage_users": True,
        "can_access_admin_hub": True,
        "can_download_backup": True,
    },
    "অধ্যক্ষ / প্রধান শিক্ষক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": True,
        "can_view_users": True,
        "can_manage_users": True,
        "can_access_admin_hub": True,
        "can_download_backup": True,
    },
    "সহকারী প্রধান শিক্ষক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": True,
        "can_view_users": True,
        "can_manage_users": True,
        "can_access_admin_hub": True,
        "can_download_backup": False,
    },
    "পরীক্ষা নিয়ন্ত্রক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": False,
        "can_view_users": True,
        "can_manage_users": False,
        "can_access_admin_hub": True,
        "can_download_backup": True,
    },
    "বিভাগীয় প্রধান (Head of Dept)": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
    "সিনিয়র শিক্ষক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": False,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
    "সহকারী শিক্ষক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": False,
        "can_view_saved_exams": True,
        "can_manage_curriculum": False,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
    "খণ্ডকালীন / অতিথি শিক্ষক": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": False,
        "can_view_saved_exams": True,
        "can_manage_curriculum": False,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
    "অফিস সহকারী / ডাটা এন্ট্রি অপারেটর": {
        "can_create_exam": False,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": False,
        "can_view_saved_exams": True,
        "can_manage_curriculum": False,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
    "আইটি অ্যাডমিন / মডারেটর": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": True,
        "can_view_saved_exams": True,
        "can_manage_curriculum": True,
        "can_manage_school_profile": True,
        "can_view_users": True,
        "can_manage_users": True,
        "can_access_admin_hub": True,
        "can_download_backup": True,
    },
    "শিক্ষক / ব্যবহারকারী": {
        "can_create_exam": True,
        "can_view_questions": True,
        "can_add_question": True,
        "can_edit_question": False,
        "can_view_saved_exams": True,
        "can_manage_curriculum": False,
        "can_manage_school_profile": False,
        "can_view_users": False,
        "can_manage_users": False,
        "can_access_admin_hub": False,
        "can_download_backup": False,
    },
}

PERMISSION_FIELD_KEYS = [
    'can_create_exam',
    'can_view_questions',
    'can_add_question',
    'can_edit_question',
    'can_view_saved_exams',
    'can_manage_curriculum',
    'can_manage_school_profile',
    'can_view_users',
    'can_manage_users',
    'can_access_admin_hub',
    'can_download_backup'
]

def seed_default_role_permissions(force=False):
    """
    Ensures all institutional roles have default permission matrix configured in database.
    Only seeds if the table is completely empty, or if force=True (e.g. factory reset).
    NEVER re-inserts deleted roles during normal startup or page requests.
    """
    try:
        # If not forced and configs already exist, do NOT re-insert deleted roles
        if not force and RolePermissionConfig.query.count() > 0:
            return

        for role_name, perms in DEFAULT_ROLE_PERMISSIONS.items():
            existing = RolePermissionConfig.query.filter_by(role_name=role_name).first()
            if not existing:
                cfg = RolePermissionConfig(role_name=role_name, **perms)
                db.session.add(cfg)
            elif force:
                for k, v in perms.items():
                    setattr(existing, k, v)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[ROLE PERMISSION SEED NOTE] {e}")

def get_permissions_for_role(role_name):
    """Retrieves current permissions for a given role from database or defaults"""
    if not role_name:
        role_name = "সহকারী শিক্ষক"
    try:
        cfg = RolePermissionConfig.query.filter_by(role_name=role_name).first()
        if cfg:
            return cfg.to_dict()
    except Exception:
        pass
    
    # If role was deleted from DB, fall back to "সহকারী শিক্ষক" from DB
    try:
        fallback_cfg = RolePermissionConfig.query.filter_by(role_name="সহকারী শিক্ষক").first()
        if fallback_cfg:
            res = fallback_cfg.to_dict()
            res['role_name'] = role_name
            return res
    except Exception:
        pass

    # Generic fallback dictionary only if database is completely empty/unreachable
    if role_name in DEFAULT_ROLE_PERMISSIONS:
        res = {'role_name': role_name}
        res.update(DEFAULT_ROLE_PERMISSIONS[role_name])
        return res
        
    # Generic fallback based on role name keywords
    role_lower = str(role_name).lower()
    is_admin_like = any(t in role_lower for t in ['admin', 'অ্যাডমিন', 'এডমিন', 'প্রধান শিক্ষক', 'সুপার'])
    return {
        'role_name': role_name,
        'can_create_exam': True,
        'can_view_questions': True,
        'can_add_question': is_admin_like,
        'can_edit_question': is_admin_like,
        'can_view_saved_exams': True,
        'can_manage_curriculum': is_admin_like,
        'can_manage_school_profile': is_admin_like,
        'can_view_users': is_admin_like,
        'can_manage_users': is_admin_like,
        'can_access_admin_hub': is_admin_like,
        'can_download_backup': is_admin_like
    }

def get_current_user_permissions():
    """Computes real-time permission mapping for the currently logged-in session user"""
    if is_current_user_super_admin():
        return {
            'role_name': 'সুপার অ্যাডমিন',
            'can_create_exam': True,
            'can_view_questions': True,
            'can_add_question': True,
            'can_edit_question': True,
            'can_view_saved_exams': True,
            'can_manage_curriculum': True,
            'can_manage_school_profile': True,
            'can_view_users': True,
            'can_manage_users': True,
            'can_access_admin_hub': True,
            'can_download_backup': True,
            'is_super_admin': True
        }
    sess_user = session.get('user')
    if not sess_user:
        return {
            'role_name': 'অতিথি',
            'can_create_exam': True,
            'can_view_questions': True,
            'can_add_question': False,
            'can_edit_question': False,
            'can_view_saved_exams': False,
            'can_manage_curriculum': False,
            'can_manage_school_profile': False,
            'can_view_users': False,
            'can_manage_users': False,
            'can_access_admin_hub': False,
            'can_download_backup': False,
            'is_super_admin': False
        }
    user_role = sess_user.get('role') or 'সহকারী শিক্ষক'
    perms = get_permissions_for_role(user_role)
    perms['is_super_admin'] = False
    return perms


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
    current_user = session.get('user')
    is_super_admin = is_current_user_super_admin()
    user_perms = get_current_user_permissions()
    return dict(
        global_classes=classes,
        school_profile=school_profile,
        current_user=current_user,
        is_super_admin=is_super_admin,
        user_perms=user_perms,
        now_dhaka=get_now_dhaka()
    )


from curriculum_data import seed_nctb_curriculum

def ensure_schema_migrations():
    """Ensure newly added columns like order_num and is_admin exist in existing SQLite database tables"""
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
                
            # Check users table
            res3 = conn.execute(db.text("PRAGMA table_info(users)")).fetchall()
            cols3 = [r[1] for r in res3]
            if cols3:
                if 'is_admin' not in cols3:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0"))
                if 'raw_password_display' not in cols3:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN raw_password_display VARCHAR(100)"))
                if 'access_start' not in cols3:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN access_start DATETIME"))
                if 'access_end' not in cols3:
                    conn.execute(db.text("ALTER TABLE users ADD COLUMN access_end DATETIME"))
                    
            conn.commit()
    except Exception as e:
        print(f"[SCHEMA MIGRATION NOTE] {e}")


# Automatically ensure database schema migrations on startup
try:
    with app.app_context():
        ensure_schema_migrations()
except Exception as _mig_err:
    print(f"[STARTUP SCHEMA MIGRATION ERROR] {_mig_err}")


# ==========================================
# SEED INITIAL DATA (Bangladeshi Curriculum)
# ==========================================
def seed_database():
    with app.app_context():
        db.create_all()
        ensure_schema_migrations()
        # NOTE: NCTB curriculum auto-sync is PERMANENTLY DISABLED.
        # All user updates, customizations, renamings, additions and deletions
        # in "সিলেবাস ও পাঠ্যসূচি সেটিংস" (ClassLevel, Subject, Chapter, Topic)
        # remain permanently saved in SQLite and will NEVER be overwritten or re-synced by NCTB.

        # Seed or ensure super admin user exists
        try:
            SUPER_ADMIN_MOBILE = "01794918384"
            legacy_admin = User.query.filter_by(mobile="01700000000").first()
            admin_user = User.query.filter_by(mobile=SUPER_ADMIN_MOBILE).first()
            
            if legacy_admin and not admin_user:
                legacy_admin.mobile = SUPER_ADMIN_MOBILE
                legacy_admin.is_admin = True
                legacy_admin.role = "সুপার অ্যাডমিন"
                db.session.commit()
                admin_user = legacy_admin
            elif legacy_admin and admin_user:
                db.session.delete(legacy_admin)
                db.session.commit()

            if not admin_user:
                admin_user = User(
                    name="প্রধান অ্যাডমিন (Super Admin)",
                    mobile=SUPER_ADMIN_MOBILE,
                    role="সুপার অ্যাডমিন",
                    status="active",
                    is_admin=True,
                    created_at=datetime.utcnow()
                )
                admin_user.set_password("admin123")
                db.session.add(admin_user)
                db.session.commit()
            else:
                admin_user.is_admin = True
                admin_user.role = "সুপার অ্যাডমিন"
                admin_user.status = "active"
                db.session.commit()
        except Exception as e:
            print(f"[USER SEED NOTE] {e}")

        # Seed default institutional role permissions
        seed_default_role_permissions()

        print("[SUCCESS] Database successfully initialized with user-customized curriculum and role permissions!")


# ==========================================
# AUTH & LANDING & CORE ROUTES
# ==========================================

@app.route('/')
def index():
    if session.get('user'):
        return redirect(url_for('dashboard'))
    return redirect(url_for('landing'))


@app.route('/landing')
def landing():
    total_classes = ClassLevel.query.count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_questions = Question.query.count()
    
    mcq_count = Question.query.filter_by(question_type='mcq').count()
    short_count = Question.query.filter_by(question_type='short').count()
    cq_count = Question.query.filter_by(question_type='cq').count()
    
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    school_profile = get_or_create_school_profile()
    
    # Pre-fetch sample real questions from DB for live demo
    sample_cqs = Question.query.filter_by(question_type='cq').limit(6).all()
    sample_mcqs = Question.query.filter_by(question_type='mcq').limit(10).all()
    sample_shorts = Question.query.filter_by(question_type='short').limit(6).all()
    
    # Fetch dynamic institutional roles configured by Super Admin
    role_configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()
    if not role_configs:
        seed_default_role_permissions()
        role_configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()
    registration_roles = [r.to_dict() for r in role_configs if 'সুপার' not in (r.role_name or '')]
    
    return render_template('landing.html',
                           total_classes=total_classes,
                           total_subjects=total_subjects,
                           total_chapters=total_chapters,
                           total_questions=total_questions,
                           mcq_count=mcq_count,
                           short_count=short_count,
                           cq_count=cq_count,
                           classes=classes,
                           school_profile=school_profile,
                           demo_cqs=[q.to_dict() for q in sample_cqs],
                           demo_mcqs=[q.to_dict() for q in sample_mcqs],
                           demo_shorts=[q.to_dict() for q in sample_shorts],
                           registration_roles=registration_roles)


@app.route('/dashboard')
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
# SINGLE SIGN-ON (SSO) & OAUTH AUTHENTICATION
# ------------------------------------------

@app.route('/api/auth/sso-login', methods=['POST'])
def api_sso_login():
    """
    Handles Single Sign-On (SSO) and OAuth 2.0 logins:
    - Google One-Tap / OAuth SSO
    - Passwordless 1-Click Teacher Instant Login
    - Custom Institution SSO
    """
    try:
        data = request.get_json(force=True, silent=True) or {}
        provider = data.get('provider', 'google')
        user_name = (data.get('name') or '').strip()
        user_email = (data.get('email') or '').strip()
        user_role = (data.get('role') or 'সিনিয়র শিক্ষক / পরীক্ষা কমিটি').strip()
        school_name = (data.get('school_name') or 'আলহেরা এডুকেয়ার হোম').strip()
        avatar = (data.get('avatar') or '').strip()
        
        if not user_email:
            user_email = 'teacher@gmail.com'
        if not user_name:
            user_name = user_email.split('@')[0].replace('.', ' ').title()
        
        if not avatar:
            # Clean SVG avatar placeholder
            avatar = f"https://api.dicebear.com/7.x/initials/svg?seed={user_name}&backgroundColor=0284c7,059669,7c3aed"

        is_super = bool('01794918384' in user_email or '01700000000' in user_email or 'সুপার' in user_role)
        is_adm = bool(is_super or any(t in user_role.lower() for t in ['admin', 'অ্যাডমিন', 'এডমিন', 'প্রধান শিক্ষক']))
        user_obj = {
            'name': user_name,
            'email': user_email,
            'role': user_role,
            'school_name': school_name,
            'provider': provider,
            'avatar': avatar,
            'is_admin': is_adm,
            'is_super_admin': is_super,
            'authenticated_at': time.strftime('%Y-%m-%d %I:%M %p')
        }
        
        session['user'] = user_obj
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': f'স্বাগতম, {user_name}! সফলভাবে আপনার অ্যাকাউন্ট ({user_email}) যুক্ত হয়েছে।',
            'redirect_url': url_for('dashboard'),
            'user': user_obj
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'লগইনে সমস্যা হয়েছে: {str(e)}'}), 500


@app.route('/auth/google/popup')
def google_auth_popup():
    """Renders Google Sign-In verification popup"""
    return render_template('google_auth_popup.html')


@app.route('/logout')
def logout():
    """Clears user session and redirects back to landing page"""
    session.pop('user', None)
    flash('আপনি সফলভাবে লগআউট হয়েছেন।', 'info')
    return redirect(url_for('landing'))


# ------------------------------------------
# USER REGISTRATION & MOBILE AUTHENTICATION
# ------------------------------------------

@app.route('/api/roles/available')
def api_roles_available():
    """
    Returns available institutional roles and their dynamic permission levels
    for account registration and display.
    Continuously reflects RolePermissionConfig managed by Super Admin.
    """
    try:
        role_configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()
        if not role_configs:
            seed_default_role_permissions()
            role_configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()

        roles_list = [r.to_dict() for r in role_configs if 'সুপার' not in (r.role_name or '')]
        return jsonify({
            'success': True,
            'roles': roles_list
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'roles': []}), 500


@app.route('/api/auth/register', methods=['POST'])
def api_auth_register():
    """
    Handles new user registration with:
    1. Name (নাম)
    2. Mobile Number (মোবাইল নম্বর)
    3. Password (পাসওয়ার্ড)
    4. Institutional Role (প্রাতিষ্ঠানিক ভূমিকা ও স্বয়ংক্রিয় পারমিশন স্তর)
    """
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        name = (data.get('name') or '').strip()
        mobile_raw = (data.get('mobile') or '').strip()
        password = (data.get('password') or '').strip()
        role_requested = (data.get('role') or 'সহকারী শিক্ষক').strip()
        
        # Validate role against dynamic RolePermissionConfig
        cfg = RolePermissionConfig.query.filter_by(role_name=role_requested).first()
        if not cfg or ('সুপার' in role_requested or 'super admin' in role_requested.lower()):
            # Guard: Root super admin cannot be assigned via public self-registration
            role = 'সহকারী শিক্ষক'
            cfg = RolePermissionConfig.query.filter_by(role_name=role).first()
        else:
            role = role_requested

        is_admin_flag = False
        if cfg and cfg.can_access_admin_hub:
            is_admin_flag = True

        mobile = normalize_mobile_number(mobile_raw)
        
        if not name:
            return jsonify({'success': False, 'message': 'দয়া করে আপনার পুরো নাম লিখুন।'}), 400
        if not mobile or len(mobile) < 10:
            return jsonify({'success': False, 'message': 'সঠিক মোবাইল নম্বর প্রদান করুন (কমপক্ষে ১১ ডিজিট)।'}), 400
        if not password or len(password) < 4:
            return jsonify({'success': False, 'message': 'পাসওয়ার্ড কমপক্ষে ৪ অক্ষরের হতে হবে।'}), 400
            
        # Check if user with this mobile already exists
        existing_user = User.query.filter((User.mobile == mobile) | (User.mobile == mobile_raw)).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': f'এই মোবাইল নম্বর ({mobile_raw}) দিয়ে ইতিমধ্যে একটি একাউন্ট খোলা আছে। অনুগ্রহ করে লগইন করুন।'
            }), 409
            
        new_user = User(
            name=name,
            mobile=mobile,
            role=role,
            is_admin=is_admin_flag,
            status='active',
            created_at=datetime.utcnow(),
            last_login=datetime.utcnow()
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        avatar = f"https://api.dicebear.com/7.x/initials/svg?seed={name}&backgroundColor=0284c7,059669,7c3aed"
        user_obj = {
            'id': new_user.id,
            'name': new_user.name,
            'mobile': new_user.mobile,
            'role': new_user.role,
            'is_admin': new_user.is_admin_user,
            'is_super_admin': new_user.is_super_admin_user,
            'school_name': 'আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়',
            'avatar': avatar,
            'authenticated_at': time.strftime('%Y-%m-%d %I:%M %p')
        }
        
        session['user'] = user_obj
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': f'অভিনন্দন {name}! আপনার একাউন্ট সফলভাবে তৈরি হয়েছে এবং স্বয়ংক্রিয়ভাবে লগইন করা হয়েছে।',
            'redirect_url': url_for('dashboard'),
            'user': user_obj
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'রেজিস্ট্রেশনে সমস্যা হয়েছে: {str(e)}'}), 500


@app.route('/api/auth/login', methods=['POST'])
def api_auth_login():
    """
    Handles user login using:
    - Mobile Number (মোবাইল নম্বর)
    - Password (পাসওয়ার্ড)
    """
    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        mobile_raw = (data.get('mobile') or '').strip()
        password = (data.get('password') or '').strip()
        
        mobile = normalize_mobile_number(mobile_raw)
        
        if not mobile and not mobile_raw:
            return jsonify({'success': False, 'message': 'মোবাইল নম্বর প্রদান করুন।'}), 400
        if not password:
            return jsonify({'success': False, 'message': 'পাসওয়ার্ড প্রদান করুন।'}), 400
            
        # Search by normalized mobile or raw input
        user = User.query.filter((User.mobile == mobile) | (User.mobile == mobile_raw)).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'ভুল মোবাইল নম্বর অথবা পাসওয়ার্ড! সঠিক তথ্য দিয়ে পুনরায় চেষ্টা করুন।'
            }), 401
            
        # Validate active subscription date & time window
        is_sub_valid, sub_msg = check_user_subscription(user)
        if not is_sub_valid:
            return jsonify({
                'success': False,
                'message': sub_msg
            }), 403

        if user.status == 'inactive':
            return jsonify({
                'success': False,
                'message': 'আপনার একাউন্টটি সাময়িকভাবে নিষ্ক্রিয় রয়েছে। অনুগ্রহ করে এডমিনের সাথে যোগাযোগ করুন।'
            }), 403
            
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        avatar = f"https://api.dicebear.com/7.x/initials/svg?seed={user.name}&backgroundColor=0284c7,059669,7c3aed"
        user_obj = {
            'id': user.id,
            'name': user.name,
            'mobile': user.mobile,
            'role': user.role,
            'is_admin': user.is_admin_user,
            'is_super_admin': user.is_super_admin_user,
            'school_name': 'আলহেরা এডুকেয়ার হোম উচ্চ বিদ্যালয়',
            'avatar': avatar,
            'authenticated_at': time.strftime('%Y-%m-%d %I:%M %p')
        }
        
        session['user'] = user_obj
        session.permanent = True
        
        return jsonify({
            'success': True,
            'message': f'স্বাগতম, {user.name}! সফলভাবে লগইন সম্পন্ন হয়েছে।',
            'redirect_url': url_for('dashboard'),
            'user': user_obj
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'লগইনে সমস্যা হয়েছে: {str(e)}'}), 500


# ------------------------------------------
# USER MANAGEMENT (SETTINGS SUB-OPTION)
# ------------------------------------------

@app.route('/settings/users')
@app.route('/users')
def user_management_view():
    """Renders registered users management page under Settings sub-options"""
    user_perms = get_current_user_permissions()
    if not is_current_user_super_admin() and not user_perms.get('can_view_users'):
        flash('আপনার প্রাতিষ্ঠানিক ভূমিকা অনুযায়ী ইউজার তালিকা দেখার অনুমতি নেই।', 'warning')
        return redirect(url_for('dashboard'))

    users = User.query.order_by(User.created_at.desc()).all()
    total_users = len(users)
    active_users = sum(1 for u in users if u.status == 'active')
    inactive_users = total_users - active_users
    return render_template('user_management.html',
                           users=users,
                           total_users=total_users,
                           active_users=active_users,
                           inactive_users=inactive_users)


@app.route('/api/users/list')
def api_users_list():
    """Returns JSON list of registered users with optional search"""
    user_perms = get_current_user_permissions()
    if not is_current_user_super_admin() and not user_perms.get('can_view_users'):
        return jsonify({'success': False, 'message': 'অননুমোদিত এক্সেস! ইউজার তালিকা দেখার পারমিশন নেই।', 'users': []}), 403

    search = request.args.get('search', '').strip().lower()
    query = User.query
    if search:
        query = query.filter(db.or_(
            User.name.ilike(f"%{search}%"),
            User.mobile.ilike(f"%{search}%"),
            User.role.ilike(f"%{search}%")
        ))
    users = query.order_by(User.created_at.desc()).all()
    return jsonify({
        'success': True,
        'users': [u.to_dict() for u in users],
        'total': len(users),
        'active_count': sum(1 for u in users if u.status == 'active')
    })


@app.route('/api/users/add', methods=['POST'])
def api_users_add():
    """Adds a new user directly from the settings management panel"""
    user_perms = get_current_user_permissions()
    if not is_current_user_super_admin() and not user_perms.get('can_manage_users'):
        return jsonify({'success': False, 'message': 'অননুমোদিত এক্সেস! নতুন ইউজার তৈরি করার পারমিশন নেই।'}), 403

    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        name = (data.get('name') or '').strip()
        mobile_raw = (data.get('mobile') or '').strip()
        password = (data.get('password') or '').strip()
        role = (data.get('role') or 'সহকারী শিক্ষক').strip()
        status = (data.get('status') or 'active').strip()
        
        mobile = normalize_mobile_number(mobile_raw)
        
        if not name or not mobile or not password:
            return jsonify({'success': False, 'message': 'নাম, মোবাইল নম্বর এবং পাসওয়ার্ড পূরণ করা আবশ্যক।'}), 400
            
        existing = User.query.filter((User.mobile == mobile) | (User.mobile == mobile_raw)).first()
        if existing:
            return jsonify({'success': False, 'message': f'এই মোবাইল নম্বর ({mobile_raw}) দিয়ে ইতিমধ্যে একাউন্ট রয়েছে।'}), 409
        
        # Only Super Admin can assign administrative / super admin roles during creation
        role_lower = role.lower()
        if any(term in role_lower for term in ['admin', 'অ্যাডমিন', 'এডমিন', 'সুপার']):
            if not is_current_user_super_admin():
                role = 'সহকারী শিক্ষক'
            
        user = User(
            name=name,
            mobile=mobile,
            role=role,
            status=status,
            created_at=datetime.utcnow()
        )
        user.set_password(password)
        if any(term in role_lower for term in ['admin', 'অ্যাডমিন', 'এডমিন', 'সুপার']) and is_current_user_super_admin():
            user.is_admin = True
        db.session.add(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f'ইউজার {name} সফলভাবে তৈরি করা হয়েছে!', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ইউজার তৈরিতে সমস্যা: {str(e)}'}), 500


@app.route('/api/users/edit/<int:user_id>', methods=['POST'])
def api_users_edit(user_id):
    """Updates user information or resets password with Super Admin role enforcement"""
    user_perms = get_current_user_permissions()
    current_sess_user = session.get('user')
    is_self = current_sess_user and current_sess_user.get('id') == user_id
    if not is_self and not is_current_user_super_admin() and not user_perms.get('can_manage_users'):
        return jsonify({'success': False, 'message': 'অননুমোদিত এক্সেস! ইউজার তথ্য সম্পাদনা করার পারমিশন নেই।'}), 403

    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        
        name = (data.get('name') or '').strip()
        mobile_raw = (data.get('mobile') or '').strip()
        password = (data.get('password') or '').strip()
        role = (data.get('role') or '').strip()
        status = (data.get('status') or '').strip()
        
        if name:
            user.name = name
        if mobile_raw:
            mobile = normalize_mobile_number(mobile_raw)
            existing = User.query.filter(User.mobile == mobile, User.id != user.id).first()
            if existing:
                return jsonify({'success': False, 'message': f'এই মোবাইল নম্বর ({mobile_raw}) অন্য একাউন্টে ব্যবহৃত হচ্ছে।'}), 409
            user.mobile = mobile
        if password:
            user.set_password(password)
            
        # Role modification is strictly guarded for Super Admin only
        if role and role != user.role:
            if not is_current_user_super_admin():
                return jsonify({
                    'success': False,
                    'message': 'ইউজারের "ভূমিকা (Role)" পরিবর্তন করার অনুমতি শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
                }), 403
            if user.mobile in ['01794918384', '01700000000'] and 'সুপার' not in role:
                return jsonify({'success': False, 'message': 'প্রধান সুপার অ্যাডমিনের ভূমিকা পরিবর্তন করা যাবে না।'}), 400
            user.role = role
            role_lower = role.lower()
            if any(term in role_lower for term in ['admin', 'অ্যাডমিন', 'এডমিন', 'প্রধান শিক্ষক', 'সুপার']):
                user.is_admin = True
            else:
                user.is_admin = False

        if status in ['active', 'inactive']:
            user.status = status
            
        db.session.commit()
        
        # If currently logged-in user edited their own info, sync session
        current_sess_user = session.get('user')
        if current_sess_user and current_sess_user.get('id') == user.id:
            current_sess_user['name'] = user.name
            current_sess_user['mobile'] = user.mobile
            current_sess_user['role'] = user.role
            current_sess_user['is_admin'] = user.is_admin_user
            current_sess_user['is_super_admin'] = user.is_super_admin_user
            session['user'] = current_sess_user
            session.modified = True

        return jsonify({'success': True, 'message': 'ইউজারের তথ্য সফলভাবে আপডেট করা হয়েছে!', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ইউজার আপডেটে সমস্যা: {str(e)}'}), 500


@app.route('/api/users/delete/<int:user_id>', methods=['POST', 'DELETE'])
def api_users_delete(user_id):
    """Deletes a registered user"""
    user_perms = get_current_user_permissions()
    if not is_current_user_super_admin() and not user_perms.get('can_manage_users'):
        return jsonify({'success': False, 'message': 'অননুমোদিত এক্সেস! ইউজার মুছে ফেলার পারমিশন নেই।'}), 403

    try:
        user = User.query.get_or_404(user_id)
        if user.mobile in ['01794918384', '01700000000'] or user.role == 'সুপার অ্যাডমিন' or user.is_super_admin_user:
            return jsonify({'success': False, 'message': 'প্রধান অ্যাডমিন একাউন্ট মোছা সম্ভব নয়।'}), 400
        user_name = user.name
        db.session.delete(user)
        db.session.commit()
        return jsonify({'success': True, 'message': f'ইউজার "{user_name}" সফলভাবে মুছে ফেলা হয়েছে!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ইউজার মুছতে সমস্যা: {str(e)}'}), 500


# ------------------------------------------
# ADMIN CONTROL PANEL & SYSTEM ADMINISTRATION
# ------------------------------------------

@app.route('/admin')
@app.route('/admin/panel')
def admin_panel_view():
    """Renders the comprehensive Super Admin Control Panel"""
    user_perms = get_current_user_permissions()
    if not is_current_user_super_admin() and not user_perms.get('can_access_admin_hub'):
        flash('আপনার প্রাতিষ্ঠানিক ভূমিকা অনুযায়ী অ্যাডমিন হাব ব্যবহারের অনুমতি নেই।', 'warning')
        return redirect(url_for('dashboard'))

    total_users = User.query.count()
    admin_users = User.query.filter((User.is_admin == True) | (User.role.ilike('%admin%')) | (User.role.ilike('%প্রধান%'))).count()
    total_questions = Question.query.count()
    total_mcq = Question.query.filter(Question.question_type == 'mcq').count()
    total_creative = Question.query.filter(Question.question_type.in_(['cq', 'creative', 'short', 'descriptive'])).count()
    total_exams = ExamPaper.query.count()
    total_classes = ClassLevel.query.count()
    total_subjects = Subject.query.count()
    total_chapters = Chapter.query.count()
    total_topics = Topic.query.count()
    
    users = User.query.order_by(User.created_at.desc()).all()
    school_profile = get_or_create_school_profile()
    recent_exams = ExamPaper.query.order_by(ExamPaper.created_at.desc()).limit(5).all()
    
    role_permissions = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()
    if not role_permissions:
        seed_default_role_permissions()
        role_permissions = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()

    # Enrich role permissions with assigned users and counts
    enriched_role_perms = []
    role_permission_map = {}
    for rp in role_permissions:
        rp_data = rp.to_dict()
        role_name = (rp.role_name or '').strip()
        matched_users = [
            u.to_dict() for u in users
            if (u.role or '').strip() == role_name or ('সুপার' in role_name and u.is_super_admin_user)
        ]
        rp_data['users_count'] = len(matched_users)
        rp_data['users'] = matched_users
        enriched_role_perms.append(rp_data)
        role_permission_map[role_name] = rp_data
    
    return render_template(
        'admin_panel.html',
        total_users=total_users,
        admin_users=admin_users,
        total_questions=total_questions,
        total_mcq=total_mcq,
        total_creative=total_creative,
        total_exams=total_exams,
        total_classes=total_classes,
        total_subjects=total_subjects,
        total_chapters=total_chapters,
        total_topics=total_topics,
        users=users,
        school_profile=school_profile,
        recent_exams=recent_exams,
        role_permissions=enriched_role_perms,
        role_permission_map=role_permission_map
    )


@app.route('/api/admin/update-role/<int:user_id>', methods=['POST'])
def api_admin_update_role(user_id):
    """
    Updates a user's role (ভূমিকা) and admin privileges.
    STRICTLY AUTHORIZED ONLY FOR 'প্রধান অ্যাডমিন (Super Admin)'.
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! ইউজারদের "ভূমিকা (Role)" পরিবর্তন ও নিয়ন্ত্রণ করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        new_role = (data.get('role') or '').strip()
        is_admin_override = data.get('is_admin')

        if not new_role:
            return jsonify({'success': False, 'message': 'দয়া করে একটি বৈধ ভূমিকা (Role) নির্বাচন করুন বা লিখুন।'}), 400

        # Protect root super admin accounts from accidental demotion
        if user.mobile in ['01794918384', '01700000000'] and new_role != 'সুপার অ্যাডমিন' and 'সুপার' not in new_role:
            return jsonify({
                'success': False,
                'message': 'প্রধান মূল সুপার অ্যাডমিন (01794918384) একাউন্টটির ভূমিকা পরিবর্তন বা ডিমোট করা যাবে না।'
            }), 400

        old_role = user.role or 'শিক্ষক'
        user.role = new_role

        # Admin privilege handling
        if is_admin_override is not None:
            user.is_admin = bool(is_admin_override)
        else:
            # Auto-assign is_admin based on role hierarchy
            role_lower = new_role.lower()
            if any(term in role_lower for term in ['admin', 'অ্যাডমিন', 'এডমিন', 'প্রধান শিক্ষক', 'সুপার']):
                user.is_admin = True
            else:
                user.is_admin = False

        if 'access_start' in data:
            user.access_start = parse_datetime_input(data.get('access_start'))
        if 'access_end' in data:
            user.access_end = parse_datetime_input(data.get('access_end'))

        db.session.commit()

        # If currently logged-in user modified their own role, synchronize their session
        current_sess_user = session.get('user')
        if current_sess_user and current_sess_user.get('id') == user.id:
            current_sess_user['role'] = user.role
            current_sess_user['is_admin'] = user.is_admin_user
            current_sess_user['is_super_admin'] = user.is_super_admin_user
            session['user'] = current_sess_user
            session.modified = True

        return jsonify({
            'success': True,
            'message': f'ইউজার "{user.name}" এর ভূমিকা সফলভাবে "{old_role}" থেকে "{new_role}" এ আপডেট করা হয়েছে!',
            'user': user.to_dict(),
            'role': user.role,
            'is_admin': user.is_admin_user,
            'is_super_admin': user.is_super_admin_user
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ভূমিকা আপডেটে সমস্যা হয়েছে: {str(e)}'}), 500


@app.route('/api/admin/update-validity/<int:user_id>', methods=['POST'])
def api_admin_update_validity(user_id):
    """
    Updates a user's subscription active date & time window (access_start & access_end).
    STRICTLY AUTHORIZED ONLY FOR 'প্রধান অ্যাডমিন (Super Admin)'.
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! ইউজারদের "সাবস্ক্রিপশন মেয়াদ" পরিবর্তন করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        
        raw_start = data.get('access_start')
        raw_end = data.get('access_end')
        
        user.access_start = parse_datetime_input(raw_start)
        user.access_end = parse_datetime_input(raw_end)
        
        # If user was marked inactive and a valid future subscription is set, auto-activate
        now = get_now_dhaka()
        if user.access_end and user.access_end > now and user.status == 'inactive':
            user.status = 'active'
            
        db.session.commit()
        
        start_str = user.access_start.strftime('%d-%m-%Y %I:%M %p') if user.access_start else 'শুরু থেকেই সক্রিয়'
        end_str = user.access_end.strftime('%d-%m-%Y %I:%M %p') if user.access_end else 'আজীবন / আনলিমিটেড'
        
        return jsonify({
            'success': True,
            'message': f'ইউজার "{user.name}" এর সক্রিয় সাবস্ক্রিপশন মেয়াদ সফলভাবে আপডেট করা হয়েছে!\n(শুরু: {start_str} | শেষ: {end_str})',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'মেয়াদ আপডেটে সমস্যা হয়েছে: {str(e)}'}), 500


@app.before_request
def check_session_validity():
    """Ensures actively logged-in users with expired subscriptions cannot browse the app"""
    path = request.path or ''
    if path.startswith('/static') or path in ['/logout', '/', '/landing'] or path.startswith('/api/auth') or path.startswith('/auth/'):
        return None
        
    sess_user = session.get('user')
    if not sess_user or not sess_user.get('id'):
        return None
        
    # Super Admin is always unrestricted
    if sess_user.get('is_super_admin') or str(sess_user.get('mobile') or '').strip() in ['01794918384', '01700000000']:
        return None
        
    try:
        user = db.session.get(User, sess_user.get('id'))
        if user:
            is_valid, msg = check_user_subscription(user)
            if not is_valid:
                session.pop('user', None)
                if request.is_json or path.startswith('/api/'):
                    return jsonify({'success': False, 'message': msg, 'expired': True}), 403
                flash(msg, 'error')
                return redirect(url_for('landing'))
    except Exception:
        pass



@app.route('/api/admin/toggle-role/<int:user_id>', methods=['POST'])
def api_admin_toggle_role(user_id):
    """Toggles user admin status. STRICTLY authorized for Super Admin only."""
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! ইউজারদের "ভূমিকা (Role)" পরিবর্তন ও নিয়ন্ত্রণ করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        user = User.query.get_or_404(user_id)
        if (user.mobile in ['01794918384', '01700000000'] or user.role == 'সুপার অ্যাডমিন' or user.is_super_admin_user) and user.is_admin:
            return jsonify({'success': False, 'message': 'মূল সুপার অ্যাডমিন একাউন্টের রোল পরিবর্তন করা যাবে না।'}), 400
            
        user.is_admin = not bool(user.is_admin)
        if user.is_admin:
            user.role = 'অ্যাডমিন / পরিচালক' if 'অ্যাডমিন' not in (user.role or '') else user.role
        else:
            if 'অ্যাডমিন' in (user.role or ''):
                user.role = 'সহকারী শিক্ষক'
                
        db.session.commit()
        status_text = 'অ্যাডমিন ক্ষমতা প্রদান করা হয়েছে' if user.is_admin else 'সাধারণ শিক্ষক করা হয়েছে'
        return jsonify({
            'success': True,
            'message': f'ইউজার "{user.name}"-কে সফলভাবে {status_text}!',
            'is_admin': user.is_admin_user,
            'is_super_admin': user.is_super_admin_user,
            'role': user.role,
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'অ্যাডমিন রোল পরিবর্তনে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/toggle-status/<int:user_id>', methods=['POST'])
def api_admin_toggle_status(user_id):
    """Toggles user active / inactive status"""
    try:
        user = User.query.get_or_404(user_id)
        if user.mobile in ['01794918384', '01700000000'] or user.role == 'সুপার অ্যাডমিন':
            return jsonify({'success': False, 'message': 'প্রধান অ্যাডমিন একাউন্ট নিষ্ক্রিয় করা সম্ভব নয়।'}), 400
            
        user.status = 'inactive' if user.status == 'active' else 'active'
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'ইউজার "{user.name}" এখন {"সক্রিয় (Active)" if user.status == "active" else "নিষ্ক্রিয় (Inactive)"}।',
            'status': user.status,
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'স্ট্যাটাস পরিবর্তনে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/reset-user-password/<int:user_id>', methods=['POST'])
def api_admin_reset_user_password(user_id):
    """Resets user password from Admin Control Hub"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        new_password = (data.get('password') or '').strip()
        
        if not new_password or len(new_password) < 4:
            return jsonify({'success': False, 'message': 'পাসওয়ার্ড কমপক্ষে ৪ অক্ষরের হতে হবে।'}), 400
            
        user.set_password(new_password)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'ইউজার "{user.name}" এর পাসওয়ার্ড সফলভাবে আপডেট করা হয়েছে!',
            'raw_password': new_password
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'পাসওয়ার্ড পরিবর্তনে সমস্যা: {str(e)}'}), 500


# ------------------------------------------
# DYNAMIC ROLE PERMISSION CONFIGURATION API
# STRICTLY SUPER ADMIN CONTROLLED
# ------------------------------------------

@app.route('/api/admin/role-permissions', methods=['GET'])
def api_admin_get_role_permissions():
    """
    Returns the complete list of institutional roles and their current dynamic permission configurations.
    Strictly restricted to Super Admin.
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! ভূমিকার পারমিশন দেখার ও পরিবর্তন করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()
        if not configs:
            seed_default_role_permissions()
            configs = RolePermissionConfig.query.order_by(RolePermissionConfig.id).all()

        all_users = User.query.all()
        result_list = []
        for c in configs:
            c_data = c.to_dict()
            role_name = (c.role_name or '').strip()
            matched_users = [
                u.to_dict() for u in all_users
                if (u.role or '').strip() == role_name or ('সুপার' in role_name and u.is_super_admin_user)
            ]
            c_data['users_count'] = len(matched_users)
            c_data['users'] = matched_users
            result_list.append(c_data)

        return jsonify({
            'success': True,
            'role_permissions': result_list,
            'total_roles': len(result_list)
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'পারমিশন তথ্য আনতে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/role-permissions/create', methods=['POST'])
def api_admin_create_role_permission():
    """
    Creates a new institutional role (ভূমিকা) with customized permission levels.
    STRICTLY AUTHORIZED ONLY FOR 'প্রধান অ্যাডমিন (Super Admin)'.
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! নতুন "ভূমিকা (Role)" তৈরি করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        role_name = (data.get('role_name') or '').strip()

        if not role_name:
            return jsonify({'success': False, 'message': 'দয়া করে নতুন ভূমিকার (Role Name) নাম লিখুন।'}), 400

        if len(role_name) < 2:
            return jsonify({'success': False, 'message': 'ভূমিকার নাম কমপক্ষে ২ অক্ষরের হতে হবে।'}), 400

        # Check for duplicates
        existing = RolePermissionConfig.query.filter_by(role_name=role_name).first()
        if existing:
            return jsonify({'success': False, 'message': f'"{role_name}" নামে ইতিমধ্যে একটি ভূমিকা সিস্টেমে বিদ্যমান রয়েছে।'}), 409

        new_role = RolePermissionConfig(role_name=role_name)
        for key in PERMISSION_FIELD_KEYS:
            if key in data:
                val = data.get(key)
                if isinstance(val, str):
                    val = val.lower() in ['true', '1', 'yes', 'on']
                setattr(new_role, key, bool(val))
            else:
                # Default permissions for newly added role: basic teacher privileges
                if key in ['can_create_exam', 'can_view_questions', 'can_add_question', 'can_view_saved_exams']:
                    setattr(new_role, key, True)
                else:
                    setattr(new_role, key, False)

        new_role.updated_at = datetime.utcnow()
        db.session.add(new_role)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'নতুন ভূমিকা "{role_name}" সফলভাবে যুক্ত করা হয়েছে!',
            'role_permission': new_role.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'নতুন ভূমিকা তৈরিতে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/role-permissions/delete', methods=['POST', 'DELETE'])
def api_admin_delete_role_permission():
    """
    Permanently deletes an existing role configuration from the database.
    Safely migrates all existing users in this role to 'সহকারী শিক্ষক'.
    STRICTLY AUTHORIZED ONLY FOR 'প্রধান অ্যাডমিন (Super Admin)'.
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! "ভূমিকা (Role)" ডিলিট করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        role_name = (data.get('role_name') or '').strip()

        if not role_name:
            return jsonify({'success': False, 'message': 'মুছে ফেলার জন্য ভূমিকার নাম প্রদান করুন।'}), 400

        # Safety Guard: Root protected roles
        role_lower = role_name.lower()
        if 'সুপার' in role_name or 'super admin' in role_lower or 'superadmin' in role_lower:
            return jsonify({'success': False, 'message': 'সিস্টেমের মূল "সুপার অ্যাডমিন" ভূমিকা ডিলিট করা সম্পূর্ণ নিষিদ্ধ।'}), 400

        if role_name == 'সহকারী শিক্ষক':
            return jsonify({'success': False, 'message': 'সিস্টেমের মূল ফলব্যাক ভূমিকা "সহকারী শিক্ষক" ডিলিট করা যাবে না।'}), 400

        # Find and permanently delete the role config from the database
        cfgs = RolePermissionConfig.query.filter(
            (RolePermissionConfig.role_name == role_name) |
            (RolePermissionConfig.role_name == role_name.strip())
        ).all()
        if not cfgs:
            cfgs = [c for c in RolePermissionConfig.query.all() if (c.role_name or '').strip().lower() == role_name.lower()]

        for cfg in cfgs:
            db.session.delete(cfg)

        # Migrate all existing users in this role to default 'সহকারী শিক্ষক'
        all_users = User.query.all()
        migrated_count = 0
        for u in all_users:
            if (u.role or '').strip() == role_name or (u.role or '').strip().lower() == role_name.lower():
                u.role = 'সহকারী শিক্ষক'
                if not u.is_super_admin_user:
                    u.is_admin = False
                migrated_count += 1

        db.session.commit()

        user_msg = f' এবং {migrated_count} জন ব্যবহারকারীকে "সহকারী শিক্ষক" ভূমিকায় স্থানান্তর করা হয়েছে' if migrated_count else ''
        return jsonify({
            'success': True,
            'message': f'"{role_name}" পদবি / ভূমিকাটি মূল ডাটাবেজ থেকে স্থায়ীভাবে মুছে ফেলা হয়েছে{user_msg}!',
            'migrated_users_count': migrated_count
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ভূমিকা মুছতে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/role-permissions/update', methods=['POST'])
def api_admin_update_role_permissions():
    """
    Updates or creates dynamic permission settings for a specific institutional role.
    Strictly authorized ONLY for Super Admin (প্রধান অ্যাডমিন).
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! স্বয়ংক্রিয় পারমিশন স্তর পরিবর্তন করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        role_name = (data.get('role_name') or '').strip()
        
        if not role_name:
            return jsonify({'success': False, 'message': 'দয়া করে ভূমিকার (Role) নাম উল্লেখ করুন।'}), 400

        # Protect root super admin role configuration integrity
        if role_name == 'সুপার অ্যাডমিন' and not data.get('can_access_admin_hub', True):
            return jsonify({'success': False, 'message': 'প্রধান সুপার অ্যাডমিন ভূমিকার অ্যাডমিন এক্সেস বন্ধ করা যাবে না।'}), 400

        cfg = RolePermissionConfig.query.filter_by(role_name=role_name).first()
        if not cfg:
            cfg = RolePermissionConfig(role_name=role_name)
            db.session.add(cfg)

        # Update each permission flag if provided
        for key in PERMISSION_FIELD_KEYS:
            if key in data:
                val = data.get(key)
                if isinstance(val, str):
                    val = val.lower() in ['true', '1', 'yes', 'on']
                setattr(cfg, key, bool(val))

        cfg.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'"{role_name}" ভূমিকার স্বয়ংক্রিয় পারমিশন স্তর সফলভাবে আপডেট করা হয়েছে!',
            'role_permission': cfg.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'পারমিশন স্তর আপডেটে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/role-permissions/reset-defaults', methods=['POST'])
def api_admin_reset_role_permissions():
    """
    Resets one or all roles back to system default permissions.
    Strictly restricted to Super Admin (প্রধান অ্যাডমিন).
    """
    if not is_current_user_super_admin():
        return jsonify({
            'success': False,
            'message': 'অননুমোদিত এক্সেস! পারমিশন রিস্টোর করার ক্ষমতা শুধুমাত্র "প্রধান অ্যাডমিন (Super Admin)"-এর রয়েছে।'
        }), 403

    try:
        data = request.get_json(force=True, silent=True) or request.form.to_dict() or {}
        target_role = (data.get('role_name') or '').strip()

        if target_role:
            if target_role not in DEFAULT_ROLE_PERMISSIONS:
                return jsonify({'success': False, 'message': f'"{target_role}" ভূমিকার কোন ডিফল্ট পারমিশন পাওয়া যায়নি।'}), 404
            
            cfg = RolePermissionConfig.query.filter_by(role_name=target_role).first()
            if not cfg:
                cfg = RolePermissionConfig(role_name=target_role)
                db.session.add(cfg)
            
            for key, val in DEFAULT_ROLE_PERMISSIONS[target_role].items():
                setattr(cfg, key, val)
            cfg.updated_at = datetime.utcnow()
            db.session.commit()
            msg = f'"{target_role}" ভূমিকার পারমিশন সফলভাবে ফ্যাক্টরি ডিফল্টে রিস্টোর করা হয়েছে!'
        else:
            # Reset all roles
            for r_name, defaults in DEFAULT_ROLE_PERMISSIONS.items():
                cfg = RolePermissionConfig.query.filter_by(role_name=r_name).first()
                if not cfg:
                    cfg = RolePermissionConfig(role_name=r_name)
                    db.session.add(cfg)
                for key, val in defaults.items():
                    setattr(cfg, key, val)
                cfg.updated_at = datetime.utcnow()
            db.session.commit()
            msg = 'সকল প্রাতিষ্ঠানিক ভূমিকার পারমিশন সফলভাবে ফ্যাক্টরি ডিফল্টে রিস্টোর করা হয়েছে!'

        return jsonify({'success': True, 'message': msg})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'ডিফল্ট পারমিশন রিস্টোরে সমস্যা: {str(e)}'}), 500


@app.route('/api/admin/system-stats')
def api_admin_system_stats():
    """Returns real-time aggregate stats for the entire website data"""
    try:
        return jsonify({
            'success': True,
            'stats': {
                'total_users': User.query.count(),
                'active_users': User.query.filter_by(status='active').count(),
                'admin_users': User.query.filter((User.is_admin == True) | (User.role.ilike('%admin%')) | (User.role.ilike('%প্রধান%'))).count(),
                'total_questions': Question.query.count(),
                'mcq_questions': Question.query.filter(Question.question_type == 'mcq').count(),
                'creative_questions': Question.query.filter(Question.question_type.in_(['cq', 'creative', 'short', 'descriptive'])).count(),
                'saved_exams': ExamPaper.query.count(),
                'classes': ClassLevel.query.count(),
                'subjects': Subject.query.count(),
                'chapters': Chapter.query.count(),
                'topics': Topic.query.count()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/backup-data')
def api_admin_backup_data():
    """Generates and downloads a comprehensive JSON backup of all website data"""
    try:
        profile = SchoolProfile.query.first()
        users = User.query.all()
        classes = ClassLevel.query.all()
        subjects = Subject.query.all()
        chapters = Chapter.query.all()
        topics = Topic.query.all()
        questions = Question.query.all()
        saved_exams = ExamPaper.query.all()
        
        backup_payload = {
            'system_name': 'আলহেরা এডুকেয়ার হোম প্রশ্নপত্র প্রণয়ন ও পরীক্ষা নিয়ন্ত্রণ প্ল্যাটফর্ম',
            'exported_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'),
            'school_profile': profile.to_dict() if profile else {},
            'summary': {
                'users_count': len(users),
                'classes_count': len(classes),
                'subjects_count': len(subjects),
                'chapters_count': len(chapters),
                'topics_count': len(topics),
                'questions_count': len(questions),
                'saved_exams_count': len(saved_exams)
            },
            'users': [u.to_dict() for u in users],
            'classes': [c.to_dict() for c in classes],
            'subjects': [s.to_dict() for s in subjects],
            'chapters': [ch.to_dict() for ch in chapters],
            'topics': [t.to_dict() for t in topics],
            'questions_sample': [q.to_dict() for q in questions[:100]],
            'saved_exams': [e.to_dict() for e in saved_exams]
        }
        
        response = jsonify(backup_payload)
        filename = f"alhera_system_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    except Exception as e:
        return jsonify({'success': False, 'message': f'ব্যাকআপ তৈরিতে সমস্যা: {str(e)}'}), 500


# ------------------------------------------
# QUESTION BANK (View, Filter, Add, Edit, Delete)
# ------------------------------------------

@app.route('/questions')
def question_list():
    if not is_current_user_super_admin():
        flash('"প্রশ্ন সম্ভার" অপশনটি শুধুমাত্র "সুপার অ্যাডমিন" প্রোফাইলের জন্য সংরক্ষিত।', 'warning')
        return redirect(url_for('dashboard'))
    classes = ClassLevel.query.order_by(ClassLevel.order_num).all()
    dup_ids = get_duplicate_question_id_set()
    total_db_duplicates = len(dup_ids)
    return render_template('questions/list.html', classes=classes, total_db_duplicates=total_db_duplicates)


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
        elif question_type in ('cq', 'descriptive'):
            if question_type == 'descriptive':
                new_q.cq_stem = request.form.get('descriptive_stem') or request.form.get('cq_stem') or None
                new_q.cq_sub_ka = request.form.get('descriptive_sub_ka') or request.form.get('cq_sub_ka')
                new_q.cq_sub_kha = request.form.get('descriptive_sub_kha') or request.form.get('cq_sub_kha')
                new_q.cq_sub_ga = request.form.get('descriptive_sub_ga') or request.form.get('cq_sub_ga') or None
                new_q.cq_sub_gha = request.form.get('descriptive_sub_gha') or request.form.get('cq_sub_gha') or None
                
                ans_ka = (request.form.get('descriptive_ans_ka') or '').strip()
                ans_kha = (request.form.get('descriptive_ans_kha') or '').strip()
                ans_ga = (request.form.get('descriptive_ans_ga') or '').strip()
                ans_gha = (request.form.get('descriptive_ans_gha') or '').strip()
                parts = []
                if ans_ka: parts.append(f"ক) {ans_ka}")
                if ans_kha: parts.append(f"খ) {ans_kha}")
                if ans_ga: parts.append(f"গ) {ans_ga}")
                if ans_gha: parts.append(f"ঘ) {ans_gha}")
                new_q.cq_solution = "\n\n".join(parts) if parts else request.form.get('cq_solution')
            else:
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
        elif question.question_type in ('cq', 'descriptive'):
            if question.question_type == 'descriptive':
                question.cq_stem = request.form.get('descriptive_stem') or request.form.get('cq_stem') or None
                question.cq_sub_ka = request.form.get('descriptive_sub_ka') or request.form.get('cq_sub_ka')
                question.cq_sub_kha = request.form.get('descriptive_sub_kha') or request.form.get('cq_sub_kha')
                question.cq_sub_ga = request.form.get('descriptive_sub_ga') or request.form.get('cq_sub_ga') or None
                question.cq_sub_gha = request.form.get('descriptive_sub_gha') or request.form.get('cq_sub_gha') or None
                
                ans_ka = (request.form.get('descriptive_ans_ka') or '').strip()
                ans_kha = (request.form.get('descriptive_ans_kha') or '').strip()
                ans_ga = (request.form.get('descriptive_ans_ga') or '').strip()
                ans_gha = (request.form.get('descriptive_ans_gha') or '').strip()
                parts = []
                if ans_ka: parts.append(f"ক) {ans_ka}")
                if ans_kha: parts.append(f"খ) {ans_kha}")
                if ans_ga: parts.append(f"গ) {ans_ga}")
                if ans_gha: parts.append(f"ঘ) {ans_gha}")
                question.cq_solution = "\n\n".join(parts) if parts else request.form.get('cq_solution')
            else:
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


@app.route('/api/questions/bulk-delete', methods=['POST'])
def api_questions_bulk_delete():
    data = request.get_json(force=True) or {}
    question_ids = data.get('question_ids', [])
    
    if not question_ids or not isinstance(question_ids, list):
        return jsonify({'success': False, 'message': 'কোনো প্রশ্ন নির্বাচন করা হয়নি।'}), 400
        
    try:
        valid_ids = [int(qid) for qid in question_ids if str(qid).isdigit()]
        if not valid_ids:
            return jsonify({'success': False, 'message': 'অকার্যকর প্রশ্ন আইডি তালিকা।'}), 400
            
        deleted_count = Question.query.filter(Question.id.in_(valid_ids)).delete(synchronize_session=False)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'message': f'নির্বাচিত {to_bangla_number(deleted_count)}টি প্রশ্ন সফলভাবে মুছে ফেলা হয়েছে।'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'মুছে ফেলতে সমস্যা হয়েছে: {str(e)}'}), 500


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
    elif raw_type in ['descriptive', 'বর্ণনামূলক', 'রচনামূলক']:
        q_type = 'descriptive'
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
        marks = float(item.get('marks') or item.get('পূর্ণমান') or (10.0 if q_type in ('cq', 'descriptive') else (2.0 if q_type == 'short' else 1.0)))
    except (ValueError, TypeError):
        marks = 10.0 if q_type in ('cq', 'descriptive') else (2.0 if q_type == 'short' else 1.0)

    q = Question(
        class_id=item.get('class_id') or default_class_id,
        subject_id=item.get('subject_id') or default_subject_id,
        chapter_id=item.get('chapter_id') or default_chapter_id,
        topic_id=topic_id,
        question_type=q_type,
        difficulty=difficulty,
        marks=marks
    )

    if q_type in ('cq', 'descriptive'):
        q.cq_stem = str(item.get('descriptive_stem') or item.get('cq_stem') or item.get('stem') or item.get('উদ্দীপক') or item.get('দৃশ্যকল্প') or '').strip()
        q.cq_sub_ka = str(item.get('descriptive_sub_ka') or item.get('cq_sub_ka') or item.get('sub_ka') or item.get('ka') or item.get('ক') or item.get('ক)') or '').strip()
        q.cq_sub_kha = str(item.get('descriptive_sub_kha') or item.get('cq_sub_kha') or item.get('sub_kha') or item.get('kha') or item.get('খ') or item.get('খ)') or '').strip()
        q.cq_sub_ga = str(item.get('descriptive_sub_ga') or item.get('cq_sub_ga') or item.get('sub_ga') or item.get('ga') or item.get('গ') or item.get('গ)') or '').strip()
        q.cq_sub_gha = str(item.get('descriptive_sub_gha') or item.get('cq_sub_gha') or item.get('sub_gha') or item.get('gha') or item.get('ঘ') or item.get('ঘ)') or '').strip()
        if q_type == 'descriptive':
            ans_ka = str(item.get('descriptive_ans_ka') or '').strip()
            ans_kha = str(item.get('descriptive_ans_kha') or '').strip()
            ans_ga = str(item.get('descriptive_ans_ga') or '').strip()
            ans_gha = str(item.get('descriptive_ans_gha') or '').strip()
            parts = []
            if ans_ka: parts.append(f"ক) {ans_ka}")
            if ans_kha: parts.append(f"খ) {ans_kha}")
            if ans_ga: parts.append(f"গ) {ans_ga}")
            if ans_gha: parts.append(f"ঘ) {ans_gha}")
            if parts:
                q.cq_solution = "\n\n".join(parts)
            else:
                q.cq_solution = str(item.get('cq_solution') or item.get('solution') or item.get('সমাধান') or item.get('উত্তর') or '').strip()
        else:
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


def extract_text_from_pdf_stream(stream):
    """
    Extracts text from a PDF file stream using pypdf.
    Cleans up formatting glitches, page numbers, and excess blank lines.
    """
    import pypdf
    try:
        reader = pypdf.PdfReader(stream)
        pages_text = []
        for page_idx, page in enumerate(reader.pages):
            txt = page.extract_text() or ''
            txt = txt.replace('\u200b', '').replace('\ufeff', '').replace('\xa0', ' ')
            lines = [line.strip() for line in txt.splitlines()]
            filtered_lines = []
            for line in lines:
                if not line:
                    continue
                # Ignore standalone page numbers
                if re.match(r'^(?:পৃষ্ঠা|page)\s*[\d০-৯]+(?:\s*(?:of|\/)\s*[\d০-৯]+)?$', line, re.IGNORECASE):
                    continue
                filtered_lines.append(line)
            cleaned_page = '\n'.join(filtered_lines).strip()
            if cleaned_page:
                pages_text.append(cleaned_page)
        return '\n\n\n'.join(pages_text)
    except Exception as e:
        print(f"[PDF EXTRACTION ERROR] {e}")
        raise


def parse_structured_text_questions(raw_text):
    """Parse human-formatted Bengali question text containing CQ, MCQ, or Short questions"""
    questions = []
    text = raw_text.replace('\r\n', '\n').replace('\r', '\n').strip()
    if not text:
        return []

    # Merge bracket header with following question number: e.g. "[সৃজনশীল ১]\n১।" -> "[সৃজনশীল ১] "
    text = re.sub(r'(\[(?:সৃজনশীল|বহুনির্বাচনি|নৈর্ব্যক্তিক|সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\])\s*\n+\s*([\d০-৯]+\s*[\.\।\)\-])', r'\1 \2', text)

    # Check if text already has distinct blocks via triple newlines
    blocks = [b.strip() for b in text.split('\n\n\n') if b.strip()]
    if len(blocks) <= 1:
        # Split on question boundaries
        pattern = r'\n(?=(?:\[(?:সৃজনশীল|বহুনির্বাচনি|নৈর্ব্যক্তিক|সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]|^সৃজনশীল\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^বহুনির্বাচনি\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^সংক্ষিপ্ত\s*(?:প্রশ্ন)?\s*[\d০-৯]+|^[\d০-৯]+\s*[\.\।\)\-]\s+|^প্রশ্ন\s*[\d০-৯]*\s*[:\-]))'
        blocks = [b.strip() for b in re.split(pattern, text, flags=re.MULTILINE) if b.strip()]
    
    if len(blocks) <= 1:
        # Fallback split by double newlines
        double_split = [b.strip() for b in text.split('\n\n') if b.strip()]
        if len(double_split) > 1:
            blocks = double_split

    ans_map = {'a': 'ক', 'b': 'খ', 'c': 'গ', 'd': 'ঘ', '1': 'ক', '2': 'খ', '3': 'গ', '4': 'ঘ', 'ক': 'ক', 'খ': 'খ', 'গ': 'গ', 'ঘ': 'ঘ'}

    for block in blocks:
        lines = [l.strip() for l in block.split('\n') if l.strip()]
        if not lines:
            continue
            
        block_text = '\n'.join(lines)
        
        # Check answer indicator with a single letter (indicates MCQ)
        m_ans_single = re.search(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ|সঠিক)\s*[:\-]\s*[\(\[]?([কখগঘabcdABCD1234])[\)\]]?(?:\s|$|\.|\;|\n)', block_text)
        
        has_desc_explicit = any(k in block_text for k in ['[বর্ণনামূলক', 'বর্ণনামূলক প্রশ্ন', 'বর্ণনামূলক'])
        has_cq_explicit = any(k in block_text for k in ['[সৃজনশীল', 'সৃজনশীল প্রশ্ন', 'উদ্দীপক:', 'উদ্দীপক -', 'দৃশ্যকল্প:'])
        has_sub_ka = bool(re.search(r'(?:^|\n)\s*(?:ক\)|ক\.|\(ক\)|ক\s*[:\-])', block_text))
        has_sub_kha = bool(re.search(r'(?:^|\n)\s*(?:খ\)|খ\.|\(খ\)|খ\s*[:\-])', block_text))
        has_sub_ga = bool(re.search(r'(?:^|\n)\s*(?:গ\)|গ\.|\(গ\)|গ\s*[:\-])', block_text))
        has_sub_gha = bool(re.search(r'(?:^|\n)\s*(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-])', block_text))

        # Check Descriptive vs CQ vs MCQ
        is_desc = (has_desc_explicit and has_sub_ka and has_sub_kha) or (has_sub_ka and has_sub_kha and not has_sub_ga and not has_sub_gha and not m_ans_single and not any(k in block_text for k in ['[সৃজনশীল', 'উদ্দীপক:']))
        is_cq = not is_desc and ((has_cq_explicit and has_sub_ka and has_sub_kha) or (has_sub_ka and has_sub_kha and has_sub_ga and has_sub_gha and not m_ans_single))
        
        # Distinct MCQ check: has options and either answer or single-line 4 options or explicit mcq tag
        has_mcq_options = bool(re.search(r'[\(\[]?[কA1][\)\]\.\-:]', block_text)) and bool(re.search(r'[\(\[]?[খB2][\)\]\.\-:]', block_text))
        is_mcq = not is_cq and not is_desc and has_mcq_options

        if is_cq or is_desc:
            stem = ""
            ka, kha, ga, gha, sol = "", "", "", "", ""
            current_field = 'stem'
            
            for line in lines:
                # Strip bracket headers like [সৃজনশীল ১], [বর্ণনামূলক ১] or [১]
                if re.match(r'^\[(?:সৃজনশীল|বর্ণনামূলক|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                    continue
                # Also strip standalone question numbers at the start of line like "১। " or "১. "
                clean_line = re.sub(r'^(?:(?:সৃজনশীল|বর্ণনামূলক)\s*(?:প্রশ্ন)?\s*[\d০-৯]+[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                
                m_ka = re.match(r'^(?:ক\)|ক\.|\(ক\)|ক\s*[:\-])\s*(.*)', clean_line)
                m_kha = re.match(r'^(?:খ\)|খ\.|\(খ\)|খ\s*[:\-])\s*(.*)', clean_line)
                m_ga = re.match(r'^(?:গ\)|গ\.|\(গ\)|গ\s*[:\-])\s*(.*)', clean_line)
                m_gha = re.match(r'^(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-])\s*(.*)', clean_line)
                m_sol = re.match(r'^(?:সমাধান|উত্তর|নির্দেশনা|Ans)\s*[:\-]\s*(.*)', clean_line)
                m_stem = re.match(r'^(?:উদ্দীপক|দৃশ্যকল্প|অনুচ্ছেদ)\s*[:\-]\s*(.*)', clean_line)
                
                if m_stem:
                    current_field = 'stem'
                    val = m_stem.group(1).strip()
                    if val:
                        stem += val + "\n"
                elif m_ka:
                    current_field = 'ka'
                    ka = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_ka.group(1)).strip()
                elif m_kha:
                    current_field = 'kha'
                    kha = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_kha.group(1)).strip()
                elif m_ga:
                    current_field = 'ga'
                    ga = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_ga.group(1)).strip()
                elif m_gha:
                    current_field = 'gha'
                    gha = re.sub(r'\s*\[[\d০-৯]+\]$', '', m_gha.group(1)).strip()
                elif m_sol:
                    current_field = 'sol'
                    sol += m_sol.group(1).strip() + "\n"
                else:
                    if current_field == 'stem':
                        stem += clean_line + "\n"
                    elif current_field == 'ka':
                        ka += " " + clean_line
                    elif current_field == 'kha':
                        kha += " " + clean_line
                    elif current_field == 'ga':
                        ga += " " + clean_line
                    elif current_field == 'gha':
                        gha += " " + clean_line
                    elif current_field == 'sol':
                        sol += clean_line + "\n"
            
            # Clean marks markers e.g. [১], [২], [৩], [৪]
            ka = re.sub(r'\s*\[[\d০-৯]+\]$', '', ka).strip()
            kha = re.sub(r'\s*\[[\d০-৯]+\]$', '', kha).strip()
            ga = re.sub(r'\s*\[[\d০-৯]+\]$', '', ga).strip()
            gha = re.sub(r'\s*\[[\d০-৯]+\]$', '', gha).strip()
            
            target_type = 'descriptive' if is_desc else 'cq'
            questions.append({
                'type': target_type,
                'question_type': target_type,
                'cq_stem': stem.strip(),
                'cq_sub_ka': ka.strip(),
                'cq_sub_kha': kha.strip(),
                'cq_sub_ga': ga.strip(),
                'cq_sub_gha': gha.strip(),
                'cq_solution': sol.strip(),
                'marks': 10.0,
                'difficulty': 'medium'
            })
            continue

        if is_mcq:
            q_stem = ""
            opt_a, opt_b, opt_c, opt_d = "", "", "", ""
            ans, exp = "", ""
            stem_lines = []
            
            for line in lines:
                if re.match(r'^\[(?:বহুনির্বাচনি|নৈর্ব্যক্তিক|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                    continue
                    
                # Answer line?
                m_ans = re.search(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ|সঠিক)\s*[:\-]\s*[\(\[]?([কখগঘabcdABCD1234])[\)\]]?', line)
                if m_ans:
                    raw_a = m_ans.group(1).lower()
                    ans = ans_map.get(raw_a, raw_a)
                    if 'ব্যাখ্যা' in line:
                        exp_part = line.split('ব্যাখ্যা', 1)[-1].lstrip(':- ')
                        if exp_part:
                            exp = exp_part.strip()
                    continue
                
                # Explanation line?
                m_exp = re.search(r'(?:ব্যাখ্যা|Exp(?:lanation)?)\s*[:\-]\s*(.*)', line)
                if m_exp:
                    exp = m_exp.group(1).strip()
                    continue
                
                # Check for 4 options in a single line
                m_4opts = re.search(
                    r'[\(\[]?([কA1a])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([খB2b])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([গC3c])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([ঘD4d])[\]\)\.\-:]\s*(.*)',
                    line
                )
                if m_4opts:
                    opt_a = m_4opts.group(2).strip()
                    opt_b = m_4opts.group(4).strip()
                    opt_c = m_4opts.group(6).strip()
                    opt_d = m_4opts.group(8).strip()
                    if any(k in opt_d for k in ['উত্তর:', 'Ans:', 'সঠিক উত্তর:']):
                        parts = re.split(r'(?:সঠিক\s*উত্তর|উত্তর|Ans|উত্তরঃ)\s*[:\-]', opt_d, 1)
                        opt_d = parts[0].strip()
                        if len(parts) > 1:
                            m_sub_ans = re.search(r'[\(\[]?([কখগঘabcdABCD1234])[\)\]]?', parts[1])
                            if m_sub_ans:
                                ans = ans_map.get(m_sub_ans.group(1).lower(), m_sub_ans.group(1))
                    continue
                
                # Check for 2 options in a single line: (ক) ... (খ) ...
                m_2opts_ab = re.search(r'[\(\[]?([কA1a])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([খB2b])[\]\)\.\-:]\s*(.*)', line)
                if m_2opts_ab:
                    opt_a = m_2opts_ab.group(2).strip()
                    opt_b = m_2opts_ab.group(4).strip()
                    continue
                # (গ) ... (ঘ) ...
                m_2opts_cd = re.search(r'[\(\[]?([গC3c])[\]\)\.\-:]\s*(.*?)\s+[\(\[]?([ঘD4d])[\]\)\.\-:]\s*(.*)', line)
                if m_2opts_cd:
                    opt_c = m_2opts_cd.group(2).strip()
                    opt_d = m_2opts_cd.group(4).strip()
                    continue
                
                # Check single option per line
                m_opt_a = re.match(r'^(?:ক\)|ক\.|\(ক\)|ক\s*[:\-]|\(A\)|A\)|A\.)\s*(.*)', line)
                m_opt_b = re.match(r'^(?:খ\)|খ\.|\(খ\)|খ\s*[:\-]|\(B\)|B\)|B\.)\s*(.*)', line)
                m_opt_c = re.match(r'^(?:গ\)|গ\.|\(গ\)|গ\s*[:\-]|\(C\)|C\)|C\.)\s*(.*)', line)
                m_opt_d = re.match(r'^(?:ঘ\)|ঘ\.|\(ঘ\)|ঘ\s*[:\-]|\(D\)|D\)|D\.)\s*(.*)', line)
                
                if m_opt_a:
                    opt_a = m_opt_a.group(1).strip()
                elif m_opt_b:
                    opt_b = m_opt_b.group(1).strip()
                elif m_opt_c:
                    opt_c = m_opt_c.group(1).strip()
                elif m_opt_d:
                    opt_d = m_opt_d.group(1).strip()
                else:
                    # Line belongs to question stem
                    clean_line = re.sub(r'^(?:প্রশ্ন\s*[\d০-৯]*\s*[:\.\-]?\s*|Q\s*[\d০-৯]*\s*[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                    stem_lines.append(clean_line)
            
            q_stem = ' '.join(stem_lines).strip()
            
            questions.append({
                'type': 'mcq',
                'question_type': 'mcq',
                'mcq_stem': q_stem,
                'option_a': opt_a,
                'option_b': opt_b,
                'option_c': opt_c,
                'option_d': opt_d,
                'correct_option': ans,
                'explanation': exp,
                'marks': 1.0,
                'difficulty': 'medium'
            })
            continue

        # 3. SHORT QUESTION (সংক্ষিপ্ত প্রশ্ন)
        q_lines = []
        a_lines = []
        is_ans = False
        
        for line in lines:
            if re.match(r'^\[(?:সংক্ষিপ্ত|প্রশ্ন)?\s*[\d০-৯a-zA-Z]+\]$', line):
                continue
            m_a = re.match(r'^(?:উত্তর|সমাধান|Ans|উত্তরঃ)\s*[:\-]\s*(.*)', line)
            if m_a:
                is_ans = True
                val = m_a.group(1).strip()
                if val:
                    a_lines.append(val)
            elif is_ans:
                a_lines.append(line)
            else:
                clean_line = re.sub(r'^(?:প্রশ্ন\s*[\d০-৯]*\s*[:\.\-]?\s*|Q\s*[\d০-৯]*\s*[:\.\-]?\s*|[\d০-৯]+\s*[\.\।\)\-]\s+)', '', line).strip()
                q_lines.append(clean_line)
                
        q_text = ' '.join(q_lines).strip()
        a_text = '\n'.join(a_lines).strip()
        
        if q_text:
            questions.append({
                'type': 'short',
                'question_type': 'short',
                'short_question': q_text,
                'short_answer': a_text,
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

@app.route('/api/parse-pdf', methods=['POST'])
def api_parse_pdf():
    """
    Endpoint to upload and parse questions directly from a PDF file.
    Returns:
    - success: bool
    - count: number of parsed questions
    - raw_text: extracted clean text from the PDF
    - questions: structured list of normalized question dicts
    - message: localized feedback message
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': 'কোনো ফাইল পাওয়া যায়নি।'}), 400
        
        file = request.files['file']
        if not file or not file.filename:
            return jsonify({'success': False, 'message': 'অবৈধ বা খালি ফাইল।'}), 400

        filename = file.filename.lower()
        if not filename.endswith('.pdf'):
            return jsonify({'success': False, 'message': 'শুধুমাত্র .pdf ফাইল গ্রহণযোগ্য।'}), 400

        file_bytes = io.BytesIO(file.read())
        raw_text = extract_text_from_pdf_stream(file_bytes)

        if not raw_text.strip():
            return jsonify({
                'success': False,
                'count': 0,
                'raw_text': '',
                'questions': [],
                'message': 'PDF ফাইলটিতে কোনো পড়ার মতো টেক্সট পাওয়া যায়নি। ফাইলটি স্ক্যান করা ছবি হলে দয়া করে টেক্সটযুক্ত PDF বা সরাসরি টেক্সট পেস্ট অপশন ব্যবহার করুন।'
            }), 400

        parsed_items = parse_structured_text_questions(raw_text)

        normalized = []
        for item in parsed_items:
            q_type = item.get('question_type') or item.get('type') or 'short'
            if q_type == 'cq':
                normalized.append({
                    'question_type': 'cq',
                    'difficulty': item.get('difficulty', 'medium'),
                    'marks': float(item.get('marks', 10.0)),
                    'topic_title': item.get('topic_title', ''),
                    'cq_stem': item.get('cq_stem', ''),
                    'cq_sub_ka': item.get('cq_sub_ka', ''),
                    'cq_sub_kha': item.get('cq_sub_kha', ''),
                    'cq_sub_ga': item.get('cq_sub_ga', ''),
                    'cq_sub_gha': item.get('cq_sub_gha', ''),
                    'cq_solution': item.get('cq_solution', '')
                })
            elif q_type == 'mcq':
                normalized.append({
                    'question_type': 'mcq',
                    'difficulty': item.get('difficulty', 'medium'),
                    'marks': float(item.get('marks', 1.0)),
                    'topic_title': item.get('topic_title', ''),
                    'mcq_stem': item.get('mcq_stem', ''),
                    'option_a': item.get('option_a', ''),
                    'option_b': item.get('option_b', ''),
                    'option_c': item.get('option_c', ''),
                    'option_d': item.get('option_d', ''),
                    'correct_option': item.get('correct_option', ''),
                    'explanation': item.get('explanation', '')
                })
            else:
                normalized.append({
                    'question_type': 'short',
                    'difficulty': item.get('difficulty', 'medium'),
                    'marks': float(item.get('marks', 2.0)),
                    'topic_title': item.get('topic_title', ''),
                    'short_question': item.get('short_question', ''),
                    'short_answer': item.get('short_answer', '')
                })

        return jsonify({
            'success': True,
            'count': len(normalized),
            'raw_text': raw_text,
            'questions': normalized,
            'message': f'PDF থেকে মোট {to_bangla_number(len(normalized))}টি প্রশ্ন সফলভাবে প্রস্তুত করা হয়েছে।' if normalized else 'PDF থেকে টেক্সট পাওয়া গেছে, কিন্তু কোনো প্রশ্ন ফরম্যাটে মেলেনি। নিচের টেক্সট বক্সে এডিট করে নিন।'
        })
    except Exception as e:
        print(f"[API PARSE PDF ERROR] {e}")
        return jsonify({
            'success': False,
            'message': f'PDF পার্স করার সময় ত্রুটি ঘটেছে: {str(e)}'
        }), 500


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

        if (request.content_type and 'multipart/form-data' in request.content_type) or request.form:
            class_id = request.form.get('class_id', type=int)
            subject_id = request.form.get('subject_id', type=int)
            chapter_id = request.form.get('chapter_id', type=int)
            topic_id = request.form.get('topic_id', type=int) or None
            
            if 'file' in request.files:
                file = request.files['file']
                filename = file.filename.lower()
                if filename.endswith('.pdf'):
                    pdf_bytes = io.BytesIO(file.read())
                    pdf_text = extract_text_from_pdf_stream(pdf_bytes)
                    questions_raw = parse_structured_text_questions(pdf_text)
                elif filename.endswith('.json'):
                    content = file.read().decode('utf-8-sig', errors='replace')
                    data = json.loads(content)
                    questions_raw = data if isinstance(data, list) else data.get('questions', [])
                elif filename.endswith(('.csv', '.tsv')):
                    content = file.read().decode('utf-8-sig', errors='replace')
                    delimiter = '\t' if filename.endswith('.tsv') else ','
                    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
                    questions_raw = list(reader)
                else:
                    content = file.read().decode('utf-8-sig', errors='replace')
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
        
        new_class_id = payload.get('class_id')
        if new_class_id:
            try:
                paper.class_id = int(new_class_id)
            except (ValueError, TypeError):
                pass
        new_subject_id = payload.get('subject_id')
        if new_subject_id:
            try:
                paper.subject_id = int(new_subject_id)
            except (ValueError, TypeError):
                pass

        paper.time_allowed = payload.get('time_allowed', '২ ঘণ্টা ৩০ মিনিট')
        paper.total_marks = float(payload.get('total_marks', 100))
        paper.instructions = payload.get('instructions', '')
        
        q_ids = payload.get('question_ids', [])
        clean_q_ids = q_ids if isinstance(q_ids, list) else [int(x) for x in str(q_ids).split(',') if x.strip().isdigit()]
        paper.questions_json = json.dumps(clean_q_ids)

        # Auto-infer class_id and subject_id from questions if still missing
        if (not paper.class_id or not paper.subject_id) and clean_q_ids:
            first_q = Question.query.filter(Question.id.in_(clean_q_ids)).first()
            if first_q:
                if not paper.class_id and first_q.class_id:
                    paper.class_id = first_q.class_id
                if not paper.subject_id and first_q.subject_id:
                    paper.subject_id = first_q.subject_id

        if paper.subject and (' - —' in paper.title or paper.title.endswith(' - ')):
            paper.title = f"{paper.exam_name} - {paper.subject.name}"
        
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
    
    paper_id = data.get('paper_id') or data.get('id')
    class_id = data.get('class_id')
    subject_id = data.get('subject_id')

    question_ids = data.get('question_ids', [])
    if isinstance(question_ids, str):
        try:
            question_ids = json.loads(question_ids)
        except Exception:
            question_ids = [int(x) for x in question_ids.split(',') if x.strip().isdigit()]

    # Fetch selected questions and preserve exact sequence
    raw_questions = Question.query.filter(Question.id.in_(question_ids)).all() if question_ids else []
    q_map = {q.id: q for q in raw_questions}
    questions = [q_map[qid] for qid in question_ids if qid in q_map]
    
    # Sort into categories maintaining relative order
    mcq_questions = [q for q in questions if q.question_type == 'mcq']
    short_questions = [q for q in questions if q.question_type == 'short']
    cq_questions = [q for q in questions if q.question_type in ('cq', 'descriptive')]

    # Auto-infer class_name, subject_name, class_id, subject_id if missing or '—'
    if questions:
        if (not class_name or class_name.strip() in ('', '—')) or not class_id:
            for q in questions:
                if q.class_level:
                    if not class_name or class_name.strip() in ('', '—'):
                        class_name = q.class_level.name
                    if not class_id:
                        class_id = q.class_id
                    break
        if (not subject_name or subject_name.strip() in ('', '—')) or not subject_id:
            unique_subjects = list(dict.fromkeys(q.subject.name for q in questions if q.subject and q.subject.name))
            if unique_subjects:
                if not subject_name or subject_name.strip() in ('', '—'):
                    subject_name = ' ও '.join(unique_subjects) if len(unique_subjects) == 2 else ', '.join(unique_subjects)
                if not subject_id and len(unique_subjects) == 1:
                    first_q = next((q for q in questions if q.subject_id), None)
                    if first_q:
                        subject_id = first_q.subject_id
    
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
                           total_selected=len(questions),
                           paper_id=paper_id,
                           class_id=class_id,
                           subject_id=subject_id)


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
    
    new_class_id = payload.get('class_id')
    if new_class_id:
        try:
            paper.class_id = int(new_class_id)
        except (ValueError, TypeError):
            pass
    new_subject_id = payload.get('subject_id')
    if new_subject_id:
        try:
            paper.subject_id = int(new_subject_id)
        except (ValueError, TypeError):
            pass

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

    if paper.subject and (' - —' in paper.title or paper.title.endswith(' - ')):
        paper.title = f"{paper.exam_name} - {paper.subject.name}"
    
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
    
    raw_questions = Question.query.filter(Question.id.in_(q_ids)).all() if q_ids else []
    q_map = {q.id: q for q in raw_questions}
    questions = [q_map[qid] for qid in q_ids if qid in q_map]

    mcq_questions = [q for q in questions if q.question_type == 'mcq']
    short_questions = [q for q in questions if q.question_type == 'short']
    cq_questions = [q for q in questions if q.question_type in ('cq', 'descriptive')]

    # Auto-infer and heal class and subject if missing or invalid
    needs_db_save = False
    if questions:
        if not paper.class_id or not paper.class_level:
            for q in questions:
                if q.class_id and q.class_level:
                    paper.class_id = q.class_id
                    needs_db_save = True
                    break
        if not paper.subject_id or not paper.subject:
            for q in questions:
                if q.subject_id and q.subject:
                    paper.subject_id = q.subject_id
                    needs_db_save = True
                    break

    class_name = paper.class_level.name if paper.class_level else ''
    if not class_name and questions:
        for q in questions:
            if q.class_level and q.class_level.name:
                class_name = q.class_level.name
                break

    subject_name = paper.subject.name if paper.subject else ''
    if not subject_name and questions:
        unique_subjects = list(dict.fromkeys(q.subject.name for q in questions if q.subject and q.subject.name))
        if unique_subjects:
            subject_name = ' ও '.join(unique_subjects) if len(unique_subjects) == 2 else ', '.join(unique_subjects)

    if needs_db_save or (subject_name and (' - —' in paper.title or paper.title.endswith(' - '))):
        try:
            if subject_name and (' - —' in paper.title or paper.title.endswith(' - ')):
                paper.title = f"{paper.exam_name} - {subject_name}"
            db.session.commit()
        except Exception:
            db.session.rollback()
    
    return render_template('exam/paper_template.html',
                           school_name=paper.school_name,
                           exam_name=paper.exam_name,
                           class_name=class_name,
                           subject_name=subject_name,
                           time_allowed=paper.time_allowed,
                           total_marks=to_bangla_number(int(paper.total_marks) if paper.total_marks and paper.total_marks == int(paper.total_marks) else paper.total_marks),
                           instructions=paper.instructions,
                           mcq_questions=mcq_questions,
                           short_questions=short_questions,
                           cq_questions=cq_questions,
                           total_selected=len(questions),
                           paper_id=paper.id,
                           class_id=paper.class_id,
                           subject_id=paper.subject_id)


@app.route('/api/questions/<int:id>/quick-update', methods=['POST'])
def api_question_quick_update(id):
    """Update question content directly from preview paper"""
    try:
        question = Question.query.get(id)
        if not question:
            return jsonify({'success': False, 'message': 'প্রশ্ন পাওয়া যায়নি'}), 404
        
        payload = request.get_json(force=True) or {}
        
        if 'marks' in payload:
            try:
                question.marks = float(payload['marks'])
            except (ValueError, TypeError):
                pass
                
        if question.question_type == 'mcq':
            if 'mcq_stem' in payload:
                question.mcq_stem = payload['mcq_stem']
            if 'option_a' in payload:
                question.option_a = payload['option_a']
            if 'option_b' in payload:
                question.option_b = payload['option_b']
            if 'option_c' in payload:
                question.option_c = payload['option_c']
            if 'option_d' in payload:
                question.option_d = payload['option_d']
            if 'correct_option' in payload:
                question.correct_option = payload['correct_option']
            if 'explanation' in payload:
                question.explanation = payload['explanation']
        elif question.question_type == 'short':
            if 'short_question' in payload:
                question.short_question = payload['short_question']
            if 'short_answer' in payload:
                question.short_answer = payload['short_answer']
        elif question.question_type in ('cq', 'descriptive'):
            if 'cq_stem' in payload:
                question.cq_stem = payload['cq_stem']
            if 'cq_sub_ka' in payload:
                question.cq_sub_ka = payload['cq_sub_ka']
            if 'cq_sub_kha' in payload:
                question.cq_sub_kha = payload['cq_sub_kha']
            if 'cq_sub_ga' in payload:
                question.cq_sub_ga = payload['cq_sub_ga']
            if 'cq_sub_gha' in payload:
                question.cq_sub_gha = payload['cq_sub_gha']
            if 'cq_solution' in payload:
                question.cq_solution = payload['cq_solution']
                
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'প্রশ্ন সফলভাবে আপডেট করা হয়েছে',
            'data': question.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/questions/quick-create', methods=['POST'])
def api_question_quick_create():
    """Create a new custom question directly from preview paper"""
    try:
        payload = request.get_json(force=True) or {}
        q_type = payload.get('question_type', 'mcq')
        
        class_id = payload.get('class_id')
        subject_id = payload.get('subject_id')
        chapter_id = payload.get('chapter_id')
        
        if not class_id:
            c = ClassLevel.query.first()
            class_id = c.id if c else 1
            
        if not subject_id:
            s = Subject.query.filter_by(class_id=class_id).first() or Subject.query.first()
            subject_id = s.id if s else 1
            
        if not chapter_id:
            ch = Chapter.query.filter_by(subject_id=subject_id).first() or Chapter.query.first()
            chapter_id = ch.id if ch else 1

        q = Question(
            question_type=q_type,
            class_id=class_id,
            subject_id=subject_id,
            chapter_id=chapter_id,
            marks=float(payload.get('marks', 1.0 if q_type == 'mcq' else (2.0 if q_type == 'short' else 10.0))),
            difficulty=payload.get('difficulty', 'medium')
        )
        
        if q_type == 'mcq':
            q.mcq_stem = payload.get('mcq_stem', 'নতুন বহুনির্বাচনি প্রশ্ন')
            q.option_a = payload.get('option_a', 'অপশন ১')
            q.option_b = payload.get('option_b', 'অপশন ২')
            q.option_c = payload.get('option_c', 'অপশন ৩')
            q.option_d = payload.get('option_d', 'অপশন ৪')
            q.correct_option = payload.get('correct_option', 'ক')
            q.explanation = payload.get('explanation', '')
        elif q_type == 'short':
            q.short_question = payload.get('short_question', 'নতুন সংক্ষিপ্ত প্রশ্ন')
            q.short_answer = payload.get('short_answer', '')
        elif q_type in ('cq', 'descriptive'):
            q.cq_stem = payload.get('cq_stem', 'উদ্দীপক এখানে লিখুন...')
            q.cq_sub_ka = payload.get('cq_sub_ka', 'জ্ঞানমূলক প্রশ্ন')
            q.cq_sub_kha = payload.get('cq_sub_kha', 'অনুধাবনমূলক প্রশ্ন')
            q.cq_sub_ga = payload.get('cq_sub_ga', 'প্রয়োগমূলক প্রশ্ন')
            q.cq_sub_gha = payload.get('cq_sub_gha', 'উচ্চতর দক্ষতামূলক প্রশ্ন')
            q.cq_solution = payload.get('cq_solution', '')
            
        db.session.add(q)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'নতুন প্রশ্ন সফলভাবে তৈরি হয়েছে',
            'id': q.id,
            'data': q.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


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


@app.route('/api/chapter/<int:chapter_id>/next-serial')
def api_chapter_next_serial(chapter_id):
    """
    Returns the next automatic serial number for questions in the given chapter.
    If type=descriptive, returns the count of descriptive questions + 1.
    """
    q_type = request.args.get('type', 'descriptive')
    type_count = Question.query.filter_by(chapter_id=chapter_id, question_type=q_type).count()
    total_count = Question.query.filter_by(chapter_id=chapter_id).count()
    next_serial = type_count + 1
    
    return jsonify({
        'success': True,
        'chapter_id': chapter_id,
        'type': q_type,
        'type_count': type_count,
        'total_count': total_count,
        'next_serial': next_serial,
        'next_serial_bn': to_bangla_number(next_serial),
        'next_serial_label': f"{to_bangla_number(next_serial)} নং প্রশ্ন"
    })


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


def get_duplicate_question_id_set():
    """
    Identifies all duplicate question IDs across the database.
    Normalizes board tags, whitespace, punctuation and case.
    """
    all_questions = Question.query.with_entities(
        Question.id, Question.question_type, Question.mcq_stem, 
        Question.short_question, Question.cq_stem, Question.cq_sub_ka, Question.cq_sub_kha
    ).all()
    
    key_map = defaultdict(list)
    for q_id, q_type, mcq_stem, short_q, cq_stem, cq_ka, cq_kha in all_questions:
        if q_type == 'mcq':
            cleaned = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', mcq_stem or '', flags=re.I)
            cleaned = re.sub(r'\(\s*[^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি)[^\)]*\)', '', cleaned, flags=re.I)
            norm = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', cleaned).strip().lower()
            key = ('mcq', norm)
        elif q_type == 'short':
            cleaned = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', short_q or '', flags=re.I)
            cleaned = re.sub(r'\(\s*[^\)]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি)[^\)]*\)', '', cleaned, flags=re.I)
            norm = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', cleaned).strip().lower()
            key = ('short', norm)
        elif q_type == 'cq':
            c_stem = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_stem or '', flags=re.I)
            c_stem = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_stem).strip().lower()
            c_ka = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_ka or '', flags=re.I)
            c_ka = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_ka).strip().lower()
            c_kha = re.sub(r'\[\s*[^\]]*(?:বোর্ড|বোর্র্ড|Board|মাদ্রাসা|স্কুল|কলেজ|ক্যাডেট|মডেল|এনসিটিবি|পরীক্ষা|২০[০-৯]{2}|১৯[০-৯]{2})[^\]]*\]', '', cq_kha or '', flags=re.I)
            c_kha = re.sub(r'[\s\?।,;:\'\"“”‘’\(\)\[\]\-_/\\।!@#$%^&*`~]+', ' ', c_kha).strip().lower()
            key = ('cq', c_stem, c_ka, c_kha)
        else:
            key = (q_type, '')
        
        if key[1]:
            key_map[key].append(q_id)
            
    dup_ids = set()
    for k, ids in key_map.items():
        if len(ids) > 1:
            dup_ids.update(ids)
    return dup_ids


@app.route('/api/questions')
def api_questions():
    # Direct IDs filtering support (preserves requested sequence)
    raw_ids = request.args.getlist('ids') or request.args.getlist('ids[]') or request.args.getlist('q_ids') or request.args.getlist('q_ids[]')
    if not raw_ids and (request.args.get('ids') or request.args.get('q_ids')):
        raw_ids = (request.args.get('ids') or request.args.get('q_ids')).split(',')
    target_ids = []
    for x in raw_ids:
        for part in str(x).split(','):
            if part.strip().isdigit():
                target_ids.append(int(part.strip()))
    
    if target_ids:
        raw_qs = Question.query.filter(Question.id.in_(target_ids)).all()
        q_map = {q.id: q for q in raw_qs}
        ordered_qs = [q_map[qid] for qid in target_ids if qid in q_map]
        return jsonify([q.to_dict() for q in ordered_qs])

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

    only_duplicates = request.args.get('only_duplicates', default='').lower() in ['true', '1', 'yes']
    dup_ids = get_duplicate_question_id_set()

    if only_duplicates:
        query = query.filter(Question.id.in_(dup_ids if dup_ids else [-1]))

    # Order: 1. MCQ -> 2. Short Question -> 3. Creative Question (CQ) -> 4. Descriptive
    type_order = db.case(
        (Question.question_type == 'mcq', 1),
        (Question.question_type == 'short', 2),
        (Question.question_type == 'cq', 3),
        (Question.question_type == 'descriptive', 4),
        else_=5
    )
    query = query.order_by(type_order, Question.created_at.desc(), Question.id.desc())

    def serialize_q(q):
        d = q.to_dict()
        d['is_duplicate'] = bool(q.id in dup_ids)
        return d

    if paginate_requested:
        page_num = max(page or 1, 1)
        page_size = min(max(per_page, 1), 200)
        pagination = db.paginate(query, page=page_num, per_page=page_size, error_out=False)
        return jsonify({
            'items': [serialize_q(q) for q in pagination.items],
            'total': pagination.total,
            'page': pagination.page,
            'per_page': pagination.per_page,
            'pages': pagination.pages,
            'has_prev': pagination.has_prev,
            'has_next': pagination.has_next,
            'prev_num': pagination.prev_num,
            'next_num': pagination.next_num,
            'total_db_duplicates': len(dup_ids)
        })

    questions = query.all()
    return jsonify([serialize_q(q) for q in questions])


@app.route('/api/questions/<int:id>')
def api_question_detail(id):
    question = Question.query.get_or_404(id)
    return jsonify(question.to_dict())


@app.route('/api/exam/paper/<int:id>')
def api_exam_paper_detail(id):
    paper = ExamPaper.query.get_or_404(id)
    try:
        q_ids = json.loads(paper.questions_json)
    except Exception:
        q_ids = []
    
    raw_questions = Question.query.filter(Question.id.in_(q_ids)).all() if q_ids else []
    q_map = {q.id: q for q in raw_questions}
    ordered_qs = [q_map[qid].to_dict() for qid in q_ids if qid in q_map]

    class_id = paper.class_id
    class_name = paper.class_level.name if paper.class_level else ''
    subject_id = paper.subject_id
    subject_name = paper.subject.name if paper.subject else ''

    if (not class_name or not subject_name) and raw_questions:
        for q in raw_questions:
            if not class_name and q.class_level:
                class_name = q.class_level.name
                class_id = q.class_id
            if not subject_name and q.subject:
                subject_name = q.subject.name
                subject_id = q.subject_id
            if class_name and subject_name:
                break
    
    return jsonify({
        'id': paper.id,
        'title': paper.title,
        'school_name': paper.school_name,
        'exam_name': paper.exam_name,
        'class_id': class_id,
        'class_name': class_name,
        'subject_id': subject_id,
        'subject_name': subject_name,
        'time_allowed': paper.time_allowed,
        'total_marks': paper.total_marks,
        'instructions': paper.instructions,
        'question_ids': q_ids,
        'questions': ordered_qs
    })



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
    if not is_current_user_super_admin():
        flash('"সেটিংস" অপশনটি শুধুমাত্র "সুপার অ্যাডমিন" প্রোফাইলের জন্য সংরক্ষিত।', 'warning')
        return redirect(url_for('dashboard'))
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
    if os.environ.get('SHOW_ERRORS_ONLY') == '1' or os.environ.get('WERKZEUG_LOG_LEVEL') == 'ERROR':
        import logging
        from flask import cli
        cli.show_server_banner = lambda *args: None
        logging.getLogger('werkzeug').setLevel(logging.ERROR)
    seed_database()
    app.run(debug=True, port=5000)

