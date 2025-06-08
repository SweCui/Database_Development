# 教务信息管理系统开发文档(region_dsj3_4)                   Database_Development               

## 目录
- [项目概述](#项目概述)
- [技术架构](#技术架构)
- [项目结构](#项目结构)
- [数据库设计](#数据库设计)
- [功能模块](#功能模块)
- [开发指南](#开发指南)
- [项目仓库](#项目仓库)

---

## 项目概述

本项目为实现"region_dsj3_4"教务信息管理系统的流程管理，涵盖**学生管理、课程排课、选课管理、成绩统计**等功能。系统采用前后端分离架构，提供完整的教务管理解决方案。

## 技术架构

### 前端技术栈
- **框架**：LayUI
- **模板引擎**：Jinja2
- **CSS**：原生CSS + LayUI样式
- **JavaScript**：原生JS + LayUI组件

### 后端技术栈
- **语言**：Python 3.x
- **Web框架**：Flask
- **数据库**：MySQL 5.7+
- **数据库连接**：mysql-connector-python
- **模板引擎**：Jinja2

## 项目结构
```
Database_Development/
├── static/             # 静态资源
│   ├── css/           # 样式文件
│   ├── js/            # JavaScript文件
│   └── images/        # 图片资源
│
├── templates/          # 前端模板
│   ├── index.html     # 首页
│   ├── login.html     # 登录页
│   ├── register.html  # 注册页
│   ├── dashboard.html # 仪表盘
│   └── student/       # 学生相关页面
│
├── run.py             # 应用入口
├── er_diagram.puml    # 数据库ER图
├── requirements.txt   # 项目依赖
└── README.md          # 项目文档
```

## 数据库设计

系统采用MySQL数据库，主要包含以下表结构：

### 用户管理
- **user**: 用户表，存储所有系统用户信息
- **admin_log**: 管理员操作日志表

### 学生管理
- **student**: 学生基本信息表
- **class**: 班级信息表
- **major**: 专业信息表
- **college**: 学院信息表
- **student_status_change**: 学籍变更记录表

### 课程管理
- **course**: 课程基本信息表
- **teaching_task**: 教学任务表（课程开设）
- **course_selection**: 选课记录表
- **grade**: 学生成绩表

### 表关系
- 学生属于班级，班级属于专业，专业属于学院
- 课程由学院负责，并通过教学任务开设
- 学生通过选课记录选择教学任务
- 成绩与选课记录关联

## 功能模块

### 1. 用户认证
- 用户登录
- 用户注册
- 密码重置
- 会话管理

### 2. 学生管理
- 学生信息维护
- 学生选课
- 成绩查询
- 课程表查看
- 学籍变更管理

### 3. 课程管理
- 课程信息维护
- 教学任务安排
- 选课管理
- 成绩录入与统计

### 4. 系统管理
- 用户权限管理
- 系统配置
- 数据备份
- 操作日志

## 开发指南

### 环境要求
- Python 3.x
- MySQL 5.7+
- pip包管理器

### 安装步骤
1. 克隆项目
```bash
git clone https://github.com/SweCui/Database_Development.git
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置数据库
- 创建MySQL数据库
- 修改数据库连接配置（默认配置：host="127.0.0.1", user="root", password="123456"）

4. 运行项目
```bash
python run.py
```

### 开发规范
1. 代码风格
   - 遵循PEP 8规范
   - 使用有意义的变量名
   - 添加必要的注释

2. 提交规范
   - 清晰的提交信息
   - 合理的分支管理
   - 代码审查

## 项目仓库
[github仓库](https://github.com/SweCui/Database_Development.git)

### 贡献指南
1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

### 许可证
MIT License




