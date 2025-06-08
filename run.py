# from app import create_app
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import os
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_123456789'  # 使用固定的密钥，避免每次重启服务器时密钥变化
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['SESSION_COOKIE_NAME'] = 'education_system_session'
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # 本地开发环境设为False，生产环境应设为True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 会话有效期为1小时
app.config['SESSION_PERMANENT'] = True  # 设置会话为永久性

# 配置选项
DB_INIT_ENABLED = True  # 设置为True启用数据库初始化，False则不初始化

# 数据库连接函数
def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="123456",
            database="student"
        )
        return conn
    except mysql.connector.Error as err:
        print(f"数据库连接错误: {err}")
        return None

# 初始化数据库
def init_db():
    try:
        # 连接MySQL服务器
        conn = mysql.connector.connect(
            host="127.0.0.1",
            user="root",
            password="123456"
        )
        cursor = conn.cursor()
        
        # 创建数据库（如果不存在）
        cursor.execute("CREATE DATABASE IF NOT EXISTS student")
        cursor.execute("USE student")
        
        # 创建用户表（如果不存在）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(20) DEFAULT 'student',
            real_id VARCHAR(50) DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 检查real_id字段是否存在，如果不存在则添加
        cursor.execute("SHOW COLUMNS FROM user LIKE 'real_id'")
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE user ADD COLUMN real_id VARCHAR(50) DEFAULT NULL")
            print("已添加real_id字段到user表")
        
        # 创建管理员日志表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            admin_id INT NOT NULL,
            operation_content TEXT NOT NULL,
            operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES user(id) ON DELETE CASCADE
        )
        """)
        
        # 创建学院表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS college (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # 创建专业表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS major (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            college_id INT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES college(id) ON DELETE CASCADE
        )
        """)
        
        # 创建班级表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS class (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            major_id INT NOT NULL,
            grade INT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (major_id) REFERENCES major(id) ON DELETE CASCADE
        )
        """)
        
        # 创建学生表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(50) NOT NULL,
            gender ENUM('男', '女') NOT NULL,
            birth_date DATE,
            id_card VARCHAR(18),
            class_id INT,
            enrollment_date DATE,
            status ENUM('在读', '休学', '退学', '毕业') DEFAULT '在读',
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (class_id) REFERENCES class(id) ON DELETE SET NULL
        )
        """)
        
        # 创建学籍变更记录表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS student_status_change (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            old_status VARCHAR(20),
            new_status VARCHAR(20) NOT NULL,
            old_class_id INT,
            new_class_id INT,
            reason TEXT,
            change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            operator_id INT,
            FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
            FOREIGN KEY (operator_id) REFERENCES user(id) ON DELETE SET NULL
        )
        """)
        
        # 创建课程表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            credit DECIMAL(3,1) NOT NULL,
            hours INT NOT NULL,
            college_id INT NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (college_id) REFERENCES college(id) ON DELETE CASCADE
        )
        """)
        
        # 创建教学任务表（课程开设表）
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS teaching_task (
            id INT AUTO_INCREMENT PRIMARY KEY,
            course_id INT NOT NULL,
            semester VARCHAR(20) NOT NULL,
            class_ids TEXT NOT NULL,
            max_students INT DEFAULT 100,
            status ENUM('未开始', '进行中', '已结束') DEFAULT '未开始',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (course_id) REFERENCES course(id) ON DELETE CASCADE
        )
        """)
        
        # 创建选课表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS course_selection (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            task_id INT NOT NULL,
            selection_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('已选', '退选') DEFAULT '已选',
            FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES teaching_task(id) ON DELETE CASCADE,
            UNIQUE KEY (student_id, task_id)
        )
        """)
        
        # 创建成绩表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade (
            id INT AUTO_INCREMENT PRIMARY KEY,
            student_id INT NOT NULL,
            task_id INT NOT NULL,
            usual_score DECIMAL(5,2),
            exam_score DECIMAL(5,2),
            final_score DECIMAL(5,2),
            gpa DECIMAL(3,2),
            comment TEXT,
            input_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            input_by INT,
            FOREIGN KEY (student_id) REFERENCES student(id) ON DELETE CASCADE,
            FOREIGN KEY (task_id) REFERENCES teaching_task(id) ON DELETE CASCADE,
            FOREIGN KEY (input_by) REFERENCES user(id) ON DELETE SET NULL,
            UNIQUE KEY (student_id, task_id)
        )
        """)
        
        # 插入默认学院数据
        cursor.execute("INSERT IGNORE INTO college (id, name) VALUES (1, '计算机学院'), (2, '数学学院'), (3, '物理学院')")
        
        # 插入默认专业数据
        cursor.execute("INSERT IGNORE INTO major (id, name, college_id) VALUES (1, '计算机科学与技术', 1), (2, '软件工程', 1), (3, '数据科学', 2)")
        
        # 插入默认班级数据
        cursor.execute("INSERT IGNORE INTO class (id, name, major_id, grade) VALUES (1, '计算机2101', 1, 2021), (2, '软工2101', 2, 2021), (3, '数据2101', 3, 2021)")
        
        conn.commit()
        print("数据库初始化成功")
    except mysql.connector.Error as err:
        print(f"数据库初始化错误: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

# 初始化测试用户
def init_test_user():
    try:
        db = get_db_connection()
        if not db:
            print("数据库连接错误，无法初始化测试用户")
            return
            
        cursor = db.cursor(dictionary=True)
        
        # 检查测试用户是否已存在
        cursor.execute("SELECT * FROM user WHERE username = 'admin'")
        if cursor.fetchone():
            print("测试用户已存在，无需重复创建")
            return
            
        # 创建测试用户
        hashed_password = generate_password_hash('123456')
        cursor.execute(
            "INSERT INTO user (username, password, role, real_id) VALUES (%s, %s, %s, %s)",
            ('admin', hashed_password, 'admin', 'admin001')
        )
        db.commit()
        print("测试用户创建成功: admin/123456")
        
        # 验证管理员用户是否创建成功
        cursor.execute("SELECT * FROM user WHERE username = 'admin'")
        admin = cursor.fetchone()
        if admin:
            print(f"管理员用户信息: {admin}")
        else:
            print("管理员用户创建失败")
        
    except mysql.connector.Error as err:
        print(f"创建测试用户错误: {err}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals() and db:
            db.close()

# 仅当配置启用时初始化数据库
if DB_INIT_ENABLED:
    print("正在初始化数据库...")
    init_db()
else:
    print("数据库初始化已禁用，使用现有数据库")

# 初始化测试用户
init_test_user()

# 登录验证装饰器
def login_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        print(f"访问需要登录的页面: {request.path}")
        print(f"当前会话内容: {session}")
        print(f"当前请求Cookie: {request.cookies}")
        
        if 'user_id' not in session:
            print("用户未登录，重定向到登录页面")
            return redirect(url_for('login_page'))
            
        print(f"已登录用户访问: {session.get('username')}, user_id: {session.get('user_id')}, role: {session.get('role')}")
        return f(*args, **kwargs)
    return decorated_function

# 角色验证装饰器
def role_required(roles):
    from functools import wraps
    def decorated_function(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash('您没有权限访问此页面')
                return redirect(url_for('dashboard_page'))
            return f(*args, **kwargs)
        return wrapper
    return decorated_function

@app.route('/')
def user_auth():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin_dashboard'))
        elif role == 'student':
            return redirect(url_for('student_dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            
            if not username or not password:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'code': 1, 'msg': '请填写完整的登录信息'})
                flash('请填写完整的登录信息')
                return redirect(url_for('login_page'))
            
            db = get_db_connection()
            if not db:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'code': 1, 'msg': '数据库连接错误'})
                flash('数据库连接错误，请稍后重试')
                return redirect(url_for('login_page'))
            
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['real_id'] = user['real_id']
                session['login_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # 记录管理员登录日志
                if user['role'] == 'admin':
                    cursor.execute("""
                        INSERT INTO admin_log (admin_id, operation_content, operation_time)
                        VALUES (%s, %s, NOW())
                    """, (user['id'], "管理员登录系统"))
                    db.commit()
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'code': 0, 'msg': '登录成功'})
                
                if user['role'] == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('student_dashboard'))
            else:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'code': 1, 'msg': '用户名或密码错误'})
                flash('用户名或密码错误')
                return redirect(url_for('login_page'))
                
        except mysql.connector.Error as err:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'code': 1, 'msg': f'数据库错误: {err}'})
            flash(f'数据库错误: {err}')
            return redirect(url_for('login_page'))
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()
    
    return redirect(url_for('login_page'))
    
@app.route('/register', methods=['GET', 'POST'])
def register_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            return jsonify({'code': 1, 'msg': '请填写完整的注册信息'})
        
        try:
            db = get_db_connection()
            if not db:
                return jsonify({'code': 1, 'msg': '数据库连接错误，请稍后重试'})
                
            cursor = db.cursor(dictionary=True)
            
            # 检查用户名是否已存在
            cursor.execute("SELECT * FROM user WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'code': 1, 'msg': '该用户名已被注册'})
            
            # 创建新用户
            hashed_password = generate_password_hash(password)
            # 生成real_id：使用时间戳和随机数组合
            real_id = f"STU{int(datetime.now().timestamp())}"
            cursor.execute(
                "INSERT INTO user (username, password, role, real_id) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, 'student', real_id)
            )
            db.commit()
            
            return jsonify({'code': 0, 'msg': '注册成功'})
                
        except mysql.connector.Error as err:
            print(f"数据库错误: {err}")
            return jsonify({'code': 1, 'msg': '数据库连接错误，请稍后重试'})
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/admin/dashboard')
@login_required
@role_required(['admin'])
def admin_dashboard():
    try:
        # 获取统计数据
        stats = {
            'student_count': get_student_count(),
            'teacher_count': get_teacher_count(),
            'course_count': get_course_count(),
            'class_count': get_class_count()
        }
        
        return render_template('admin/dashboard.html',
                             user_data=session.get('user_data'),
                             stats=stats,
                             current_time=datetime.now().strftime('%Y年%m月%d日'))
    except Exception as e:
        flash(f'加载仪表板失败：{str(e)}', 'error')
        return redirect(url_for('login'))

@app.route('/student/dashboard')
@login_required
@role_required(['student'])
def student_dashboard():
    try:
        return render_template('student/dashboard.html',
                             user_data=session.get('user_data'),
                             current_time=datetime.now().strftime('%Y年%m月%d日'))
    except Exception as e:
        flash(f'加载仪表板失败：{str(e)}', 'error')
        return redirect(url_for('login'))

def get_student_count():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM student")
                return cursor.fetchone()[0]
    except Exception:
        return 0

def get_teacher_count():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM teacher")
                return cursor.fetchone()[0]
    except Exception:
        return 0

def get_course_count():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM course")
                return cursor.fetchone()[0]
    except Exception:
        return 0

def get_class_count():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM class")
                return cursor.fetchone()[0]
    except Exception:
        return 0

@app.route('/dashboard')
@login_required
def dashboard_page():
    user_role = session.get('role', '')
    user_name = session.get('name', session.get('username', ''))
    
    print(f"Dashboard访问 - 用户角色: {user_role}, 用户名: {user_name}")
    
    # 根据用户角色重定向到相应的仪表板
    if user_role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif user_role == 'student':
        return redirect(url_for('student_dashboard'))
    else:
        flash('未知的用户角色')
        return redirect(url_for('login_page'))

# 个人信息相关路由
@app.route('/profile')
@login_required
def profile_page():
    try:
        db = get_db_connection()
        if not db:
            flash('数据库连接错误，请稍后重试')
            return redirect(url_for('dashboard_page'))
            
        cursor = db.cursor(dictionary=True)
        user_id = session.get('user_id')
        role = session.get('role')
        real_id = session.get('real_id')
        
        user_data = {
            'username': session.get('username'),
            'role': role,
            'name': session.get('name', session.get('username'))
        }
        
        try:
            if role == 'student' and real_id:
                # 获取学生基本信息
                cursor.execute("""
                    SELECT s.*, c.name as class_name, m.name as major_name, col.name as college_name 
                    FROM student s
                    LEFT JOIN class c ON s.class_id = c.id
                    LEFT JOIN major m ON c.major_id = m.id
                    LEFT JOIN college col ON m.college_id = col.id
                    WHERE s.student_id = %s
                """, (real_id,))
                student_data = cursor.fetchone()
                if student_data:
                    user_data.update(student_data)
                
                # 获取学生成绩统计
                cursor.execute("""
                    SELECT 
                        COUNT(DISTINCT g.task_id) as course_count,
                        SUM(c.credit) as total_credits,
                        AVG(g.gpa) as gpa
                    FROM grade g
                    JOIN teaching_task tt ON g.task_id = tt.id
                    JOIN course c ON tt.course_id = c.id
                    WHERE g.student_id = (SELECT id FROM student WHERE student_id = %s)
                """, (real_id,))
                stats = cursor.fetchone()
                if stats:
                    user_data.update(stats)
                
                return render_template('student/profile.html', user_data=user_data)
            
            elif role == 'admin':
                # 管理员用户的基本信息
                user_data.update({
                    'admin_id': real_id or 'admin001',
                    'admin_level': '超级管理员',
                    'permissions': '全部权限',
                    'last_login': session.get('login_time')
                })
                
                # 获取系统统计数据
                user_data.update({
                    'student_count': get_student_count(),
                    'teacher_count': get_teacher_count(),
                    'course_count': get_course_count()
                })
                
                # 获取最近操作记录
                cursor.execute("""
                    SELECT 
                        operation_time as time,
                        operation_content as content
                    FROM admin_log
                    WHERE admin_id = %s
                    ORDER BY operation_time DESC
                    LIMIT 5
                """, (user_id,))
                user_data['recent_logs'] = cursor.fetchall()
                
                return render_template('admin/profile.html', user_data=user_data)
            else:
                flash('未知的用户角色')
                return redirect(url_for('dashboard_page'))
                
        except Exception as e:
            print(f"获取用户资料错误: {e}")
            flash('获取用户资料时发生错误')
            return redirect(url_for('dashboard_page'))
        
    except mysql.connector.Error as err:
        flash(f'数据库错误: {err}')
        return redirect(url_for('dashboard_page'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            db = get_db_connection()
            if not db:
                return jsonify({'code': 1, 'msg': '数据库连接错误'})
                
            cursor = db.cursor(dictionary=True)
            user_id = session.get('user_id')
            role = session.get('role')
            real_id = session.get('real_id')
            
            if role == 'student':
                # 获取表单数据
                address = request.form.get('address')
                
                # 更新学生信息
                cursor.execute("""
                    UPDATE student 
                    SET address = %s
                    WHERE student_id = %s
                """, (address, real_id))
                
                # 记录操作日志
                cursor.execute("""
                    INSERT INTO admin_log (admin_id, operation_content, operation_time)
                    VALUES (%s, %s, NOW())
                """, (user_id, f"更新学生 {real_id} 的地址信息"))
                
                db.commit()
                return jsonify({'code': 0, 'msg': '个人信息修改成功'})
                
            elif role == 'admin':
                # 管理员只能修改基本信息
                address = request.form.get('address')
                
                # 更新管理员信息（使用admin_log表记录地址）
                cursor.execute("""
                    INSERT INTO admin_log (admin_id, operation_content, operation_time)
                    VALUES (%s, %s, NOW())
                """, (user_id, f"更新管理员地址为: {address}"))
                
                db.commit()
                return jsonify({'code': 0, 'msg': '个人信息修改成功'})
            else:
                return jsonify({'code': 1, 'msg': '未知的用户角色'})
                
        except mysql.connector.Error as err:
            return jsonify({'code': 1, 'msg': f'数据库错误: {err}'})
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()
    
    # GET请求根据角色返回不同的模板
    role = session.get('role')
    if role == 'admin':
        return render_template('admin/edit_profile.html')
    elif role == 'student':
        return render_template('student/edit_profile.html')
    else:
        flash('未知的用户角色')
        return redirect(url_for('dashboard_page'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        try:
            old_password = request.form.get('old_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            if not old_password or not new_password or not confirm_password:
                return jsonify({'code': 1, 'msg': '请填写完整的密码信息'})
                
            if new_password != confirm_password:
                return jsonify({'code': 1, 'msg': '两次输入的新密码不一致'})
                
            db = get_db_connection()
            if not db:
                return jsonify({'code': 1, 'msg': '数据库连接错误'})
                
            cursor = db.cursor(dictionary=True)
            user_id = session.get('user_id')
            role = session.get('role')
            
            # 验证旧密码
            cursor.execute("SELECT password FROM user WHERE id = %s", (user_id,))
            user = cursor.fetchone()
            
            if not check_password_hash(user['password'], old_password):
                return jsonify({'code': 1, 'msg': '原密码错误'})
                
            # 更新密码
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE user SET password = %s WHERE id = %s", (hashed_password, user_id))
            
            # 记录操作日志
            if role == 'admin':
                cursor.execute("""
                    INSERT INTO admin_log (admin_id, operation_content, operation_time)
                    VALUES (%s, %s, NOW())
                """, (user_id, "修改管理员密码"))
            
            db.commit()
            return jsonify({'code': 0, 'msg': '密码修改成功，请重新登录'})
            
        except mysql.connector.Error as err:
            return jsonify({'code': 1, 'msg': f'数据库错误: {err}'})
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()
    
    # GET请求根据角色返回不同的模板
    role = session.get('role')
    if role == 'admin':
        return render_template('admin/change_password.html')
    else:
        return render_template('student/change_password.html')

# 学生功能路由
@app.route('/student/courses')
@login_required
def student_courses():
    if session.get('role') != 'student':
        flash('您没有权限访问此页面')
        return redirect(url_for('dashboard_page'))
    
    try:
        db = get_db_connection()
        if not db:
            flash('数据库连接错误，请稍后重试')
            return redirect(url_for('dashboard_page'))
            
        cursor = db.cursor(dictionary=True)
        student_id = session.get('real_id')
        
        # 获取学生已选课程
        cursor.execute("""
            SELECT cs.id, c.course_id, c.name, c.credit, c.hours, 
                   t.name as teacher_name, tt.semester, cs.status
            FROM course_selection cs
            JOIN teaching_task tt ON cs.task_id = tt.id
            JOIN course c ON tt.course_id = c.id
            JOIN teacher t ON tt.teacher_id = t.id
            WHERE cs.student_id = (SELECT id FROM student WHERE student_id = %s)
              AND cs.status = '已选'
        """, (student_id,))
        selected_courses = cursor.fetchall()
        
        # 获取可选课程
        cursor.execute("""
            SELECT tt.id as task_id, c.course_id, c.name, c.credit, c.hours, 
                   t.name as teacher_name, tt.semester, tt.status
            FROM teaching_task tt
            JOIN course c ON tt.course_id = c.id
            JOIN teacher t ON tt.teacher_id = t.id
            WHERE tt.status = '进行中'
            AND tt.id NOT IN (
                SELECT task_id FROM course_selection 
                WHERE student_id = (SELECT id FROM student WHERE student_id = %s)
                AND status = '已选'
            )
        """, (student_id,))
        available_courses = cursor.fetchall()
        
        return render_template('student/courses.html', 
                              selected_courses=selected_courses,
                              available_courses=available_courses)
        
    except mysql.connector.Error as err:
        flash(f'数据库错误: {err}')
        return redirect(url_for('dashboard_page'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/student/select_course/<int:task_id>', methods=['POST'])
@login_required
def select_course(task_id):
    if session.get('role') != 'student':
        return jsonify({'code': 1, 'msg': '您没有权限执行此操作'})
    
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'code': 1, 'msg': '数据库连接错误，请稍后重试'})
            
        cursor = db.cursor(dictionary=True)
        student_id = session.get('real_id')
        
        # 获取学生ID
        cursor.execute("SELECT id FROM student WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'code': 1, 'msg': '学生信息不存在'})
        
        # 检查课程是否存在
        cursor.execute("SELECT * FROM teaching_task WHERE id = %s", (task_id,))
        task = cursor.fetchone()
        if not task:
            return jsonify({'code': 1, 'msg': '课程不存在'})
        
        # 检查是否已选
        cursor.execute("""
            SELECT * FROM course_selection 
            WHERE student_id = %s AND task_id = %s AND status = '已选'
        """, (student['id'], task_id))
        if cursor.fetchone():
            return jsonify({'code': 1, 'msg': '您已经选择了该课程'})
        
        # 添加选课记录
        cursor.execute("""
            INSERT INTO course_selection (student_id, task_id) 
            VALUES (%s, %s)
        """, (student['id'], task_id))
        db.commit()
        
        return jsonify({'code': 0, 'msg': '选课成功'})
        
    except mysql.connector.Error as err:
        return jsonify({'code': 1, 'msg': f'数据库错误: {err}'})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/student/drop_course/<int:selection_id>', methods=['POST'])
@login_required
def drop_course(selection_id):
    if session.get('role') != 'student':
        return jsonify({'code': 1, 'msg': '您没有权限执行此操作'})
    
    try:
        db = get_db_connection()
        if not db:
            return jsonify({'code': 1, 'msg': '数据库连接错误，请稍后重试'})
            
        cursor = db.cursor(dictionary=True)
        student_id = session.get('real_id')
        
        # 获取学生ID
        cursor.execute("SELECT id FROM student WHERE student_id = %s", (student_id,))
        student = cursor.fetchone()
        if not student:
            return jsonify({'code': 1, 'msg': '学生信息不存在'})
        
        # 检查选课记录是否存在
        cursor.execute("""
            SELECT * FROM course_selection 
            WHERE id = %s AND student_id = %s
        """, (selection_id, student['id']))
        if not cursor.fetchone():
            return jsonify({'code': 1, 'msg': '选课记录不存在'})
        
        # 更新选课状态为退选
        cursor.execute("""
            UPDATE course_selection 
            SET status = '退选' 
            WHERE id = %s AND student_id = %s
        """, (selection_id, student['id']))
        db.commit()
        
        return jsonify({'code': 0, 'msg': '退课成功'})
        
    except mysql.connector.Error as err:
        return jsonify({'code': 1, 'msg': f'数据库错误: {err}'})
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/student/grades')
@login_required
def student_grades():
    if session.get('role') != 'student':
        flash('您没有权限访问此页面')
        return redirect(url_for('dashboard_page'))
    
    try:
        db = get_db_connection()
        if not db:
            flash('数据库连接错误，请稍后重试')
            return redirect(url_for('dashboard_page'))
            
        cursor = db.cursor(dictionary=True)
        student_id = session.get('real_id')
        
        # 获取学生成绩
        cursor.execute("""
            SELECT g.*, c.name as course_name, c.credit, t.name as teacher_name, tt.semester
            FROM grade g
            JOIN teaching_task tt ON g.task_id = tt.id
            JOIN course c ON tt.course_id = c.id
            JOIN teacher t ON tt.teacher_id = t.id
            WHERE g.student_id = (SELECT id FROM student WHERE student_id = %s)
        """, (student_id,))
        grades = cursor.fetchall()
        
        # 计算GPA
        total_credit = 0
        total_gpa_points = 0
        
        for grade in grades:
            if grade['gpa'] is not None and grade['credit'] is not None:
                total_credit += grade['credit']
                total_gpa_points += grade['gpa'] * grade['credit']
        
        overall_gpa = round(total_gpa_points / total_credit, 2) if total_credit > 0 else 0
        
        return render_template('student/grades.html', 
                              grades=grades,
                              overall_gpa=overall_gpa)
        
    except mysql.connector.Error as err:
        flash(f'数据库错误: {err}')
        return redirect(url_for('dashboard_page'))
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'db' in locals():
            db.close()

@app.route('/import_data', methods=['GET', 'POST'])
@login_required
@role_required(['admin'])
def import_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'code': 1, 'msg': '没有选择文件'})
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'code': 1, 'msg': '没有选择文件'})
            
        if not file.filename.endswith(('.xlsx', '.xls', '.csv')):
            return jsonify({'code': 1, 'msg': '不支持的文件格式，请上传Excel或CSV文件'})
            
        try:
            # 读取文件内容
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
                
            # 获取要导入的表名
            table_name = request.form.get('table_name')
            if not table_name:
                return jsonify({'code': 1, 'msg': '请选择要导入的表'})
                
            # 连接数据库
            db = get_db_connection()
            if not db:
                return jsonify({'code': 1, 'msg': '数据库连接错误'})
                
            cursor = db.cursor()
            
            # 获取表的列名
            cursor.execute(f"SHOW COLUMNS FROM {table_name}")
            columns = [column[0] for column in cursor.fetchall()]
            
            # 验证数据列是否匹配
            missing_columns = set(columns) - set(df.columns)
            if missing_columns:
                return jsonify({'code': 1, 'msg': f'数据缺少必要的列: {", ".join(missing_columns)}'})
                
            # 准备插入语句
            placeholders = ', '.join(['%s'] * len(columns))
            columns_str = ', '.join(columns)
            insert_query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # 插入数据
            success_count = 0
            error_count = 0
            for _, row in df.iterrows():
                try:
                    values = [row[col] for col in columns]
                    cursor.execute(insert_query, values)
                    success_count += 1
                except mysql.connector.Error as err:
                    error_count += 1
                    print(f"插入错误: {err}")
                    continue
                    
            db.commit()
            
            return jsonify({
                'code': 0,
                'msg': f'导入完成。成功: {success_count}条，失败: {error_count}条'
            })
            
        except Exception as e:
            return jsonify({'code': 1, 'msg': f'导入失败: {str(e)}'})
        finally:
            if 'cursor' in locals():
                cursor.close()
            if 'db' in locals():
                db.close()
                
    # GET请求显示导入页面
    return render_template('admin/import_data.html')

@app.route('/init_db')
def init_db_route():
    try:
        init_db()
        flash('数据库初始化成功')
    except Exception as e:
        flash(f'数据库初始化失败: {e}')
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)
    # app.run(host='0.0.0.0', port=5000)
