from flask import Blueprint, render_template, request
from app.models import 排课
from app.utils.scheduler import check_triple_conflict

main_bp = Blueprint('main', __name__)

@main_bp.route('/schedule', methods=['GET', 'POST'])
def manage_schedule():
    if request.method == 'POST':
        # 获取表单数据
        teacher_id = request.form['teacher_id']
        classroom_id = request.form['classroom_id']
        
        # 调用冲突检测
        conflicts = check_triple_conflict(
            teacher_id, classroom_id, 
            request.form['week'], 
            request.form['day'], 
            request.form['period']
        )
        
        if "无冲突" in conflicts:
            new_schedule = 排课(...)
            db.session.add(new_schedule)
            db.session.commit()
            return render_template('schedule.html', success=True)
        
        return render_template('schedule.html', conflicts=conflicts)
    
    return render_template('schedule.html')