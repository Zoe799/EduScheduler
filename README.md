# EduScheduler

**教育课程与教师排课管理系统**
**An Education Course and Teacher Scheduling Management System**

---

## 📖 项目简介 | Overview

**中文**

EduScheduler 是一个基于 Web 的课程与教师排课管理系统，主要用于管理课外教育机构中多个学校、课程、教师、教室和学生班级的日常排课工作。

系统将课程安排、教师分配、学校假期和教师可用时间集中管理，帮助减少人工维护课表的工作，并及时发现教师时间冲突。

**English**

EduScheduler is a web-based course and teacher scheduling management system designed for after-school education programs.

It centralizes course schedules, teacher assignments, school holidays, and teacher availability in one place, helping reduce manual schedule management and identify teacher scheduling conflicts.

---

## ✨ 主要功能 | Features

### 📅 课程安排 | Course Scheduling

**中文**

* 查看每周课程安排
* 按学校和日期组织课程
* 按学校分组显示课程
* 管理课程时间、教室和学生人数
* 支持每周单独调整教师分配

**English**

* View weekly course schedules
* Organize courses by school and day
* Group courses by school
* Manage course times, classrooms, and student numbers
* Make weekly adjustments to teacher assignments

---

### 🏫 学校管理 | School Management

**中文**

* 添加和编辑学校
* 为不同学校分配颜色
* 管理学校假期
* 根据学校假期自动隐藏当天课程

**English**

* Add and edit schools
* Assign colors to different schools
* Manage school holidays
* Automatically hide courses during school holidays

---

### 👨‍🏫 教师管理 | Teacher Management

**中文**

* 添加和管理教师
* 设置教师工作日
* 记录教师请假
* 将教师分配到课程
* 支持每门课程最多 4 名教师

**English**

* Add and manage teachers
* Set teacher working days
* Record teacher leave
* Assign teachers to courses
* Support up to four teachers per course

---

### 🔄 每周教师分配 | Weekly Teacher Assignments

**中文**

系统将常规课程信息与每周教师安排分开管理。

教师安排可以继承之前一周的设置，同时也可以针对某一周进行临时调整，而不会修改课程本身的长期设置。

**English**

The system separates regular course information from weekly teacher assignments.

Teacher assignments can be inherited from the previous week while still allowing temporary changes for a specific week without modifying the regular course configuration.

---

### ⚠️ 冲突检测 | Conflict Detection

**中文**

系统会检查：

* 教师课程时间冲突
* 教师请假期间的课程安排
* 同一教师在不同学校同时授课的情况

冲突以警告形式显示，不会强制阻止排课操作。

**English**

The system checks for:

* Teacher schedule conflicts
* Course assignments during teacher leave
* Teachers assigned to different schools at the same time

Conflicts are displayed as warnings rather than blocking schedule changes.

---

### 🗓️ 学校日历 | School Calendar

**中文**

学校日历用于记录不上课的日期，例如学校假期和其他非授课日。

当课程日期落在学校的非授课日期范围内时，该课程不会显示在课表中。

**English**

The school calendar records non-class days, including school holidays and other days without classes.

Courses are automatically hidden when their scheduled dates fall within a school's non-class period.

---

### 📱 响应式界面 | Responsive Interface

**中文**

系统支持桌面和移动端浏览器访问，并针对教师查看课表的使用场景进行了简化设计。

**English**

The system supports both desktop and mobile browsers, with a simplified interface for teachers to quickly view their schedules.

---

## 🛠️ 技术栈 | Tech Stack

### Backend

* Python
* FastAPI
* MySQL

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 Templates

### Database

* MySQL

---

## 📁 项目结构 | Project Structure

```text
EduScheduler/
│
├── main.py
├── utils/
│   └── ...
│
├── templates/
│   └── ...
│
├── static/
│   ├── css/
│   └── js/
│
├── .env
├── .gitignore
├── .gitattributes
├── requirements.txt
└── README.md
```

---

## 🚀 安装与运行 | Getting Started

### 1. 克隆项目 | Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/EduScheduler.git
cd EduScheduler
```

### 2. 创建虚拟环境 | Create a Virtual Environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

macOS / Linux:

```bash
source venv/bin/activate
```

### 3. 安装依赖 | Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. 配置数据库 | Configure the Database

在项目根目录创建 `.env` 文件：

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=course_scheduler
```

然后创建 MySQL 数据库并导入项目所需的数据表。

Create the MySQL database and import the required database tables.

### 5. 启动项目 | Start the Application

```bash
uvicorn main:app --reload
```

默认访问地址：

Default URL:

```text
http://127.0.0.1:8000
```

---

## 🗄️ 数据库 | Database

EduScheduler 使用 MySQL 保存以下数据：

EduScheduler uses MySQL to store:

* 学校 | Schools
* 课程 | Courses
* 教师 | Teachers
* 教师工作日 | Teacher Work Days
* 教师请假 | Teacher Leave
* 每周教师分配 | Weekly Teacher Assignments
* 学校假期 | School Holidays

**注意 | Note**

数据库账号、密码等敏感信息应保存在 `.env` 中，不应提交到 GitHub。

Database credentials and other sensitive information should be stored in `.env` and should **not** be committed to GitHub.

---

## 📌 当前状态 | Current Status

**中文**

EduScheduler 目前主要用于课外教育机构的内部课程和教师管理。

项目仍在持续开发中，后续将继续改进移动端界面、排课流程、部署方式以及系统的自动化功能。

**English**

EduScheduler is currently designed for internal course and teacher management in an after-school education environment.

The project is actively being developed, with future improvements planned for the mobile interface, scheduling workflow, deployment, and automation.

---

## 🔮 后续计划 | Future Improvements

* 📱 优化移动端界面
  Improve the mobile interface

* ⚠️ 改进课程冲突的可视化
  Improve schedule conflict visualization

* 👨‍🏫 更完善的教师可用时间管理
  Improve teacher availability management

* 🤖 自动排课功能
  Automated schedule generation

* 💾 自动数据库备份
  Automated database backups

* 🔐 用户登录与权限管理
  User authentication and permission management

* 📊 课表导出与数据报告
  Schedule export and reporting

* 🌐 更完善的服务器部署方案
  Improved server deployment

---

## 🔒 License

This project is currently intended for internal use.

本项目目前主要用于内部使用。
