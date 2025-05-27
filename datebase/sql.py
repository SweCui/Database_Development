import mysql.connector

# 创建数据库连接
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",
    database="date"
)

print("数据库连接成功!")