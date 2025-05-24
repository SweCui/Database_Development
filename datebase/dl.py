from flask import Blueprint, request, session
from werkzeug.security import generate_password_hash

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    
    # 根据角色查询不同表
    if request.form['role'] == 'teacher':
        user = 教师.query.filter_by(教师号=username).first()
    elif request.form['role'] == 'student':
        user = 学生.query.filter_by(学号=username).first()
    
    if user and check_password(user.password, password):
        session['user_id'] = user.id
        session['role'] = request.form['role']
        return redirect('/')
    
    return "认证失败", 401