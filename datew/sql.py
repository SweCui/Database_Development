from app import db

class 学生(db.Model):
    学号 = db.Column(db.String(20), primary_key=True)
    姓名 = db.Column(db.String(50))
    专业 = db.Column(db.String(50))
    # 其他字段...

class 排课(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    周次 = db.Column(db.Integer)
    星期 = db.Column(db.Integer)
    节次 = db.Column(db.Integer)
    # 其他字段与关系...