# from app import create_app
from flask import Flask ,render_template, request

app = Flask(__name__)

@app.route('/')
def admin_login():
    
    return render_template('index.html')

def hello_world():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # 登录成功之后，链接数据库，校验账号密码
        print('从服务器接收到的数据：', username, password)
        # 登录成功之后，应该调转到管理页面
        return render_template('/admin')
    return render_template('index.html')


if __name__ == "__main__":
    app.run()
    # app.run(host='0.0.0.0', port=5000)
