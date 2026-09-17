# EduScheduler

**教育课程与教师排课管理系统**
**A Scheduling System for Multi-School Education Programs**

> A web-based scheduling system designed for education programs where teachers, courses, and resources are shared across multiple schools.

---

## 💡 Why EduScheduler?

### 为什么自己开发，而不是使用现有排课系统？

**中文**

EduScheduler 并不是为了重新实现一个通用的排课软件，而是为了适应一个比较特殊的实际工作场景。

我们的课程安排涉及 **多个学校、多个校区，以及一批需要在不同学校之间流动的教师**。

例如，一名教师可能在：

```text
14:00–14:30   School A
14:30–15:30   School B
```

也可能出现课程时间存在部分重叠的情况：

```text
14:00–15:00   School A
14:30–15:30   School B
```

这种情况下，系统需要发现潜在的时间冲突，但不能简单地认为：

> “一个老师同时出现在两个课程中 = 排课错误。”

实际的排课工作仍然需要由工作人员根据课程地点、移动时间和具体情况进行判断。

因此，EduScheduler 的设计理念是：

> **发现问题，而不是替人做决定。**

系统会对教师时间冲突和请假等情况提供 **warnings**，而不是强制阻止排课。

此外，我们的课程安排还存在一些通用排课软件不一定能够很好适应的需求：

* 同一批教师需要跨多个学校授课
* 不同学校拥有独立的假期和不上课日期
* 常规课程安排与某一周实际的教师安排可能不同
* 教师拥有自己的工作日和请假记录
* 一门课程可能由多名教师共同负责
* 排课人员需要在发现异常后保留人工判断和调整的空间

EduScheduler 因此被设计成一个面向实际工作流程的 **multi-school scheduling system**，而不仅仅是一张电子课表。

---

### Why build another scheduling system?

**English**

EduScheduler was not created to reinvent a generic scheduling application. It was built to fit a specific real-world workflow.

Our teaching schedule involves **multiple schools, multiple locations, and a shared pool of teachers who move between schools**.

For example, a teacher may have:

```text
14:00–14:30   School A
14:30–15:30   School B
```

There may also be situations where course times partially overlap:

```text
14:00–15:00   School A
14:30–15:30   School B
```

In such cases, the system should identify the potential conflict, but it should not automatically assume that the schedule is invalid.

The scheduler may need to consider factors such as travel time, classroom arrangements, and the actual circumstances of the classes.

Therefore, one of the core design principles of EduScheduler is:

> **Identify potential problems without making scheduling decisions for people.**

The system provides **warnings** for teacher scheduling conflicts and leave, rather than simply blocking the assignment.

Other requirements that shaped the system include:

* Teachers may work across multiple schools
* Each school has its own holidays and non-class days
* Regular course schedules may differ from actual weekly teacher assignments
* Teachers have individual working days and leave
* A course may have multiple teachers
* Scheduling staff need to retain the ability to review and adjust unusual cases manually

EduScheduler is therefore designed as a **multi-school scheduling system built around a real operational workflow**, rather than simply a digital timetable.

---

## ✨ Key Features | 主要功能

### 📅 Course Scheduling | 课程安排

* Weekly schedule view
* Organize courses by school and day
* Manage course time, classroom, group, and student number
* Support multiple teachers per course
* Make weekly changes without modifying the regular course configuration

---

### 👨‍🏫 Teacher Management | 教师管理

* Add and manage teachers
* Configure teacher working days
* Record teacher leave
* Assign teachers to courses
* Support up to four teachers per course

---

### 🔄 Weekly Teacher Assignments | 每周教师分配

EduScheduler separates the **regular course schedule** from the **actual teacher assignment for a specific week**.

```text
Regular Course
      │
      ▼
Previous Week Assignment
      │
      ▼
Current Week Assignment
      │
      └── Override when necessary
```

This allows a regular course to remain unchanged while teachers can be temporarily reassigned for a particular week.

**中文**

系统将长期课程设置和某一周实际的教师安排分开管理。

例如：

```text
Regular Course
Monday 16:00–17:00
SchoolI Robotics

Week 1 → Teacher A + Teacher B
Week 2 → Teacher A + Teacher C
Week 3 → Teacher B + Teacher C
```

这样临时调课不会破坏课程本身的长期配置。

---

### ⚠️ Conflict Detection | 冲突检测

The system checks for potential issues such as:

* Teacher time conflicts
* Teachers assigned during their leave
* Teachers scheduled at different schools at overlapping times

Conflicts are displayed as **warnings**, rather than hard restrictions.

**中文**

系统会检查：

* 教师课程时间冲突
* 教师请假期间的课程安排
* 教师在不同学校之间的时间重叠

系统不会直接禁止操作，而是提醒排课人员进行人工确认。

---

### 🗓️ School-Specific Calendar | 学校独立日历

Each school has its own calendar.

```text
School A → Holiday
School B → Classes
School C → Holiday
```

A holiday at one school does not automatically affect other schools.

**中文**

每个学校拥有独立的不上课日期。

因此：

> School A 放假 ≠ 所有学校都放假

课程只有在对应学校的非授课日期内才会被隐藏。

---

### 🏫 School Management | 学校管理

* Add and edit schools
* Assign visual colors to schools
* Manage school-specific holidays
* Group courses by school

---

### 📱 Schedule View | 课表查看

The system provides a simplified read-only schedule view for teachers and staff.

The goal is to make the information needed during daily operations easy to find without exposing unnecessary editing controls.

---

## 🧩 Design Philosophy | 设计理念

### Human-in-the-loop Scheduling

**中文**

EduScheduler 并不试图完全自动化排课。

复杂的教育排课工作往往包含一些软件无法直接判断的现实因素，例如：

* 教师在不同学校之间移动
* 临时人员调整
* 特殊课程安排
* 教室和学生数量
* 某些看似冲突、但实际上经过人工确认是可行的安排

因此，系统负责：

**Detect → Warn → Visualize**

而最终的：

**Review → Decide → Adjust**

仍然交给排课人员。

**English**

EduScheduler does not attempt to completely automate the scheduling process.

Real-world education scheduling can involve factors that are difficult for software to determine automatically, such as:

* Teacher movement between schools
* Temporary staff changes
* Special course arrangements
* Classroom and student capacity
* Apparent conflicts that have been manually verified as workable

The system focuses on:

**Detect → Warn → Visualize**

while leaving:

**Review → Decide → Adjust**

to the scheduling staff.

---

## 🛠️ Tech Stack | 技术栈

### Backend

* Python
* FastAPI
* MySQL

### Frontend

* HTML
* CSS
* JavaScript
* Jinja2 Templates

### Development

* Git / GitHub
* REST-style API endpoints
* Environment-based database configuration

---

## 📁 Project Structure | 项目结构

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

## 🚀 Getting Started | 安装与运行

### 1. Clone the repository | 克隆项目

```bash
git clone https://github.com/Zoe799/EduScheduler.git
cd EduScheduler
```

### 2. Create a virtual environment | 创建虚拟环境

```bash
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS / Linux:

```bash
source .venv/bin/activate
```

### 3. Install dependencies | 安装依赖

```bash
pip install -r requirements.txt
```

### 4. Configure the database | 配置数据库

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=8000
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=course_scheduler
```

数据库账号和密码等敏感信息应保存在 `.env` 中，不应提交到 GitHub。

### 5. Start the application | 启动项目

```bash
uvicorn main:app --reload
```

The application will normally be available at:

```text
http://127.0.0.1:8000
```

---

## 🗄️ Database | 数据库

EduScheduler uses MySQL to manage:

* Schools
* Courses
* Teachers
* Teacher work days
* Teacher leave
* Weekly teacher assignments
* School calendars

The database structure is designed around the relationship between **schools, courses, teachers, and weekly assignments**.

---

## 📌 Current Status | 当前状态

**中文**

EduScheduler 目前主要用于课外教育机构内部的课程和教师排课管理。

项目正在持续开发中。目前重点已经从基础排课功能逐渐转向代码结构、用户体验、移动端界面以及部署和备份。

**English**

EduScheduler is currently designed for internal scheduling and teacher management in an after-school education environment.

The project is actively being developed, with ongoing work focused on code organization, user experience, mobile interface improvements, deployment, and database backup.

---

## 🔮 Future Improvements | 后续计划

* 📱 Improve the mobile interface
  优化移动端界面

* 🤖 Explore automated schedule generation
  探索自动排课

* ⚠️ Improve conflict visualization
  改进冲突可视化

* 👨‍🏫 Improve teacher availability management
  完善教师可用时间管理

* 💾 Automated database backup
  自动数据库备份

* 🔐 User authentication and permissions
  用户登录与权限管理

* 📊 Schedule export and reporting
  课表导出与数据报告

* 🌐 Improve deployment and hosting
  改进部署与服务器方案

---

## 🔒 License

This project is currently intended for internal use.

本项目目前主要用于内部使用。
