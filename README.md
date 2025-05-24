# Database_Development
教务信息数据库设计与开发

[github仓库](https://github.com/SweCui/Database_Development.git)




项目结构
```
Database_Development/
├── app/
│   ├── __init__.py
│   ├── routes.py       # 路由定义
│   ├── models.py       # 数据库模型
│   ├── auth.py         # 认证模块
│   ├── utils/
│   │   ├── scheduler.py  # 排课算法
│   │   └── ai_sql.py    # AI功能
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── course.html
│   │   └── grade.html
│   └── static/
│       ├── css/
│       └── js/
├── config.py           # 配置
└── run.py              # 启动脚本
```