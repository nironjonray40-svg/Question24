import sys, json, os
sys.path.insert(0, os.path.abspath('.'))
sys.stdout.reconfigure(encoding='utf-8')
import app
with app.app.app_context():
    def get_exams_for_chaps(chapter_ids):
        q_tuples = app.db.session.query(app.Question.id).filter(app.Question.chapter_id.in_(chapter_ids)).all()
        q_set = {q[0] for q in q_tuples}
        papers = app.ExamPaper.query.order_by(app.ExamPaper.created_at.desc()).all()
        matches = []
        for p in papers:
            try:
                p_q_ids = set(json.loads(p.questions_json or '[]'))
            except:
                p_q_ids = set()
            common = q_set.intersection(p_q_ids)
            if common:
                matches.append({
                    'id': p.id,
                    'exam_name': p.exam_name,
                    'title': p.title,
                    'matched_count': len(common)
                })
        return matches

    print('For chaps [5, 7]:', get_exams_for_chaps([5, 7]))
    print('For chaps [1]:', get_exams_for_chaps([1]))
    print('For chaps [98]:', get_exams_for_chaps([98]))
    print('For chaps [9999]:', get_exams_for_chaps([9999]))

