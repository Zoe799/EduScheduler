from datetime import date, timedelta
from typing import Optional
import os

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

import mysql.connector


app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount(
    "/static",
    StaticFiles(directory="static"),
    name="static"
)


DAY_NAMES = {
    1: "Monday",
    2: "Tuesday",
    3: "Wednesday",
    4: "Thursday",
    5: "Friday",
}

SCHOOL_COLORS = {
    "ISB": {
        "background": "#EAF2FF",
        "border": "#5B8DEF",
    },

    "WAB": {
        "background": "#EAF7EE",
        "border": "#55A96B",
    },

    "BSB Sanlitun": {
        "background": "#FFF2E5",
        "border": "#E58A3A",
    },

    "LFIP": {
        "background": "#F3ECFF",
        "border": "#9566D8",
    },

    "Dulwich": {
        "background": "#E8F7F7",
        "border": "#3FA6A6",
    },

    "Harrow": {
        "background": "#FFF0F2",
        "border": "#D96B7B",
    },

    "Daystar SLT": {
        "background": "#FFF8DF",
        "border": "#D4A72C",
    },

    "DSP": {
        "background": "#EEF0FF",
        "border": "#6978D8",
    },

    "THIS": {
        "background": "#F1F1F1",
        "border": "#777777",
    },

    # 下面是预留颜色
    "MSB": {
        "background": "#EAF5FF",
        "border": "#4C9BCF",
    },

    "NAS": {
        "background": "#FDEDF7",
        "border": "#C85A9B",
    },

    "BSB Shunyi": {
        "background": "#EEF8E8",
        "border": "#76A84F",
    },

    "Daystar BG": {
        "background": "#FFF0E8",
        "border": "#D8784D",
    },
}

SCHOOL_COLOR_PALETTE = [
    {"background": "#EAF2FF", "border": "#5B8DEF"},
    {"background": "#EAF7EE", "border": "#55A96B"},
    {"background": "#FFF2E5", "border": "#E58A3A"},
    {"background": "#F3ECFF", "border": "#9566D8"},
    {"background": "#E8F7F7", "border": "#3FA6A6"},
    {"background": "#FFF0F2", "border": "#D96B7B"},
    {"background": "#FFF8DF", "border": "#D4A72C"},
    {"background": "#EEF0FF", "border": "#6978D8"},
    {"background": "#F1F1F1", "border": "#777777"},
    {"background": "#EAF5FF", "border": "#4C9BCF"},
    {"background": "#FDEDF7", "border": "#C85A9B"},
    {"background": "#EEF8E8", "border": "#76A84F"},
    {"background": "#FFF0E8", "border": "#D8784D"},

    # New colors
    {"background": "#EAF8F5", "border": "#48A999"},
    {"background": "#FFF4E8", "border": "#D98A45"},
    {"background": "#F0EAFF", "border": "#8667C8"},
    {"background": "#EAF0F8", "border": "#607FA8"},
    {"background": "#F9EAF0", "border": "#B85C7A"},
    {"background": "#EDF7E9", "border": "#6C9E50"},
    {"background": "#FFF9E8", "border": "#C9A43A"},
]

def get_school_color(
    school_name,
    school_id
):
    if school_name in SCHOOL_COLORS:
        return SCHOOL_COLORS[school_name]

    index = (
        int(school_id) - 1
    ) % len(SCHOOL_COLOR_PALETTE)

    return SCHOOL_COLOR_PALETTE[index]

# =========================================================
# Database
# =========================================================

def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST","localhost"),
        user=os.getenv("DB_USER","root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=("DB_PASSWORD", "course_scheduler")
    )

@app.get("/")
async def home():
    return RedirectResponse("/view")

@app.get("/edit")
async def schedule(
    request: Request,
    date_str: Optional[str] = None
):
    # --------------------------------------------------
    # 1. Determine selected week
    # --------------------------------------------------

    if date_str:
        try:
            selected_date = date.fromisoformat(date_str)
        except ValueError:
            selected_date = date.today()
    else:
        selected_date = date.today()

    # Monday = 0
    week_start = (
        selected_date
        - timedelta(days=selected_date.weekday())
    )

    week_dates = [
        week_start + timedelta(days=i)
        for i in range(5)
    ]


    # --------------------------------------------------
    # 2. Database
    # --------------------------------------------------

    db = get_db()
    cursor = db.cursor(dictionary=True)


    # --------------------------------------------------
    # 3. Schools
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status
        FROM schools
        ORDER BY name
    """)

    schools = cursor.fetchall()


    # --------------------------------------------------
    # 4. Courses
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            c.id,
            c.school_id,
            s.name AS school_name,
            c.course_name,
            c.day_of_week,
            c.start_time,
            c.end_time,
            c.classroom,
            c.group_name,
            c.student_number
        FROM courses c
        JOIN schools s
            ON c.school_id = s.id
        ORDER BY
            s.name,
            c.day_of_week,
            c.start_time,
            c.course_name
    """)

    courses = cursor.fetchall()


    # --------------------------------------------------
    # 5. Teachers
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status,
            work_days
        FROM teachers
        WHERE status <> 'hidden'
        ORDER BY name
    """)

    teachers = cursor.fetchall()

    teacher_name_map = {
        teacher["id"]: teacher["name"]
        for teacher in teachers
    }


    # --------------------------------------------------
    # 6. Default course teachers
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            teacher_id
        FROM course_teachers
        ORDER BY course_id, teacher_id
    """)

    course_teacher_rows = cursor.fetchall()

    default_teacher_map = {}

    for item in course_teacher_rows:

        course_id = item["course_id"]

        if course_id not in default_teacher_map:
            default_teacher_map[course_id] = []

        if len(default_teacher_map[course_id]) < 4:
            default_teacher_map[course_id].append(
                item["teacher_id"]
            )


    # --------------------------------------------------
    # 7. Weekly assignments
    #
    # Get all assignments up to the end of this week.
    # This allows previous schedules to be inherited.
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            class_date,
            teacher_id
        FROM weekly_assignments
        WHERE class_date <= %s
            AND (teacher_id IS NULL OR teacher_id <> %s)
        ORDER BY
            course_id,
            class_date DESC,
            teacher_id
    """, (
        week_dates[-1],
        18
    ))

    all_weekly_assignments = cursor.fetchall()


    # --------------------------------------------------
    # 8. Exact weekly assignments
    #
    # If a row exists for course + date,
    # it is an explicit override.
    #
    # teacher_id = NULL means explicitly unassigned.
    # --------------------------------------------------

    weekly_assignment_map = {}

    for item in all_weekly_assignments:

        key = (
            item["course_id"],
            item["class_date"]
        )

        if key not in weekly_assignment_map:
            weekly_assignment_map[key] = []

        if item["teacher_id"] is not None:

            if len(weekly_assignment_map[key]) < 4:
                weekly_assignment_map[key].append(
                    item["teacher_id"]
                )


    # --------------------------------------------------
    # 9. Inherited assignments
    #
    # Only use the MOST RECENT previous assignment
    # for the same course + weekday.
    # --------------------------------------------------

    inherited_assignment_map = {}
    inherited_assignment_date = {}

    for item in all_weekly_assignments:

        if item["class_date"] >= week_start:
            continue

        course_id = item["course_id"]
        weekday = item["class_date"].weekday()

        key = (
            course_id,
            weekday
        )

        # First date encountered is the newest previous date
        if key not in inherited_assignment_date:

            inherited_assignment_date[key] = (
                item["class_date"]
            )

            inherited_assignment_map[key] = []

        # Only collect teachers from that newest date
        if (
            item["class_date"]
            == inherited_assignment_date[key]
        ):

            if item["teacher_id"] is not None:

                if len(inherited_assignment_map[key]) < 4:
                    inherited_assignment_map[key].append(
                        item["teacher_id"]
                    )


    # --------------------------------------------------
    # 10. School calendar
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            school_id,
            start_date,
            end_date,
            type,
            note
        FROM school_calendar
        WHERE start_date <= %s
          AND end_date >= %s
    """, (
        week_dates[-1],
        week_dates[0]
    ))

    calendar_events = cursor.fetchall()


    # --------------------------------------------------
    # 11. Teacher leave
    # --------------------------------------------------

    cursor.execute("""
        SELECT
            teacher_id,
            start_date,
            end_date,
            note
        FROM teacher_leave
        WHERE start_date <= %s
          AND end_date >= %s
    """, (
        week_dates[-1],
        week_dates[0]
    ))

    teacher_leaves = cursor.fetchall()

    teacher_leave_map = {}

    for leave in teacher_leaves:

        teacher_id = leave["teacher_id"]

        if teacher_id not in teacher_leave_map:
            teacher_leave_map[teacher_id] = []

        teacher_leave_map[teacher_id].append(
            leave
        )


    # --------------------------------------------------
    # 12. Build calendar map
    #
    # school_id + date -> events
    # --------------------------------------------------

    calendar_map = {}

    for event in calendar_events:

        current = event["start_date"]

        while current <= event["end_date"]:

            key = (
                event["school_id"],
                current
            )

            if key not in calendar_map:
                calendar_map[key] = []

            calendar_map[key].append(event)

            current += timedelta(days=1)


    # --------------------------------------------------
    # 13. Prepare courses
    # --------------------------------------------------

    for course in courses:

        # MySQL TIME comes back as timedelta
        course["start_time_display"] = str(
            course["start_time"]
        )[:5]

        course["end_time_display"] = str(
            course["end_time"]
        )[:5]


    # --------------------------------------------------
    # 14. Build Day × All Schools structure
    # --------------------------------------------------

    days = []

    # Keep schools in the same order as the schools table
    school_order = {
        school["id"]: index
        for index, school in enumerate(schools)
    }

    school_name_map = {
        school["id"]: school["name"]
        for school in schools
    }


    for current_date in week_dates:

        day_courses = []

        for course in courses:

            if course["day_of_week"] != (
                current_date.weekday() + 1
            ):
                continue

            # ------------------------------------------
            # Determine teachers
            # ------------------------------------------

            assignment_key = (
                course["id"],
                current_date
            )

            if assignment_key in weekly_assignment_map:

                teacher_ids = weekly_assignment_map[
                    assignment_key
                ]

                assignment_exists = True
                assignment_inherited = False

            else:

                inherited_key = (
                    course["id"],
                    current_date.weekday()
                )

                if inherited_key in inherited_assignment_map:

                    teacher_ids = inherited_assignment_map[
                        inherited_key
                    ]

                    assignment_exists = False
                    assignment_inherited = True

                else:

                    teacher_ids = default_teacher_map.get(
                        course["id"],
                        []
                    )

                    assignment_exists = False
                    assignment_inherited = False


            teacher_ids = teacher_ids[:4]

            teacher_ids = (
                teacher_ids
                + [None] * (4 - len(teacher_ids))
            )


            course_data = course.copy()

            school_color = get_school_color(
                course["school_name"],
                course["school_id"]
            )

            course_data["school_background"] = (
                school_color["background"]
            )

            course_data["school_border"] = (
                school_color["border"]
            )

            course_data["teacher_ids"] = teacher_ids

            course_data["assignment_exists"] = (
                assignment_exists
            )

            course_data["assignment_inherited"] = (
                assignment_inherited
            )


            # ------------------------------------------
            # Calendar
            # ------------------------------------------

            events = calendar_map.get(
                (
                    course["school_id"],
                    current_date
                ),
                []
            )

            course_data["calendar_events"] = events

            course_data["is_holiday"] = len(events) > 0


            # ------------------------------------------
            # Teacher leave
            # ------------------------------------------

            course_data["teacher_leave_warnings"] = []

            for teacher_id in teacher_ids:

                if teacher_id is None:
                    continue

                leaves = teacher_leave_map.get(
                    teacher_id,
                    []
                )

                for leave in leaves:

                    if (
                        leave["start_date"]
                        <= current_date
                        <= leave["end_date"]
                    ):

                        course_data[
                            "teacher_leave_warnings"
                        ].append({
                            "teacher_name":
                                teacher_name_map.get(
                                    teacher_id,
                                    "Unknown teacher"
                                ),
                            "note":
                                leave["note"]
                        })


            course_data["teacher_conflicts"] = []

            day_courses.append(course_data)


        # ------------------------------------------
        # Sort:
        #
        # 1. School
        # 2. Time
        #
        # This keeps courses from the same school
        # together vertically.
        # ------------------------------------------

        day_courses.sort(
            key=lambda c: (
                school_order.get(
                    c["school_id"],
                    999
                ),
                c["start_time_display"],
                c["course_name"]
            )
        )


        days.append({
            "date": current_date,
            "courses": day_courses
        })


    # --------------------------------------------------
    # 14.5. Compute free teachers per day
    # --------------------------------------------------

    # 所有可分配老师（已过滤 hidden）
    all_teacher_ids = {t["id"] for t in teachers}

    teacher_by_id = {t["id"]: t for t in teachers}

    # 每个 weekday（1-5）-> set(teacher_id)
    busy_by_weekday = {1: set(), 2: set(), 3: set(), 4: set(), 5: set()}

    for day in days:
        weekday = day["date"].isoweekday()   # 1=Monday ... 5=Friday
        for course in day["courses"]:
            # 假期课程不算占用
            if course.get("is_holiday"):
                continue
            for tid in course["teacher_ids"]:
                if tid is not None:
                    busy_by_weekday[weekday].add(tid)

    # 给每一天附加 free_teachers 列表
    for day in days:
        weekday = day["date"].isoweekday()

        busy = busy_by_weekday.get(weekday, set())

        free = []

        for t in teachers:
            if t["id"] in busy:
                continue

            # 老师当天是否上班？
            work_days = (t["work_days"] or "").split(",")
            work_days = [d.strip() for d in work_days if d.strip()]

            if work_days and str(weekday) not in work_days:
                # 如果老师有配置 work_days 且今天不在其中，
                # 视为"本来就不上班"，不显示在空闲列表。
                # 如果 work_days 为空，则默认视为上班。
                continue

            free.append(t)

        day["free_teachers"] = free

    # --------------------------------------------------
    # 15. Teacher conflict detection
    # --------------------------------------------------

    all_day_courses = []

    for day_index, day in enumerate(days):

        for course in day["courses"]:
            if course.get("is_holiday"):
                continue
            all_day_courses.append({
                "day_index": day_index,
                "course": course
            })


    for i in range(len(all_day_courses)):

        item_a = all_day_courses[i]

        course_a = item_a["course"]
        day_a = item_a["day_index"]

        if course_a.get("is_holiday"):
            continue

        for j in range(i + 1, len(all_day_courses)):

            item_b = all_day_courses[j]

            course_b = item_b["course"]
            day_b = item_b["day_index"]

            if day_a != day_b:
                continue

            start_a = course_a["start_time_display"]
            end_a = course_a["end_time_display"]

            start_b = course_b["start_time_display"]
            end_b = course_b["end_time_display"]

            if not (
                start_a < end_b
                and start_b < end_a
            ):
                continue

            teachers_a = [
                teacher_id
                for teacher_id in course_a["teacher_ids"]
                if teacher_id is not None
            ]

            teachers_b = [
                teacher_id
                for teacher_id in course_b["teacher_ids"]
                if teacher_id is not None
            ]

            conflicts = (
                set(teachers_a)
                & set(teachers_b)
            )

            if not conflicts:
                continue

            for teacher_id in conflicts:

                teacher_name = teacher_name_map.get(
                    teacher_id,
                    "Unknown teacher"
                )

                warning_a = {
                    "teacher_name": teacher_name,
                    "course_name": course_b["course_name"],
                    "start_time": start_b,
                    "end_time": end_b
                }

                warning_b = {
                    "teacher_name": teacher_name,
                    "course_name": course_a["course_name"],
                    "start_time": start_a,
                    "end_time": end_a
                }

                course_a["teacher_conflicts"].append(
                    warning_a
                )

                course_b["teacher_conflicts"].append(
                    warning_b
                )


    cursor.close()
    db.close()


    # --------------------------------------------------
    # 16. Render
    # --------------------------------------------------

    return templates.TemplateResponse(
        "schedule.html",
        {
            "request": request,
            "week_dates": week_dates,
            "selected_date": selected_date.isoformat(),
            "week_start": week_start.isoformat(),
            "days": days,
            "schools": schools,
            "teachers": teachers,
            "calendar_events": calendar_events
        }
    )

# =========================================================
# Create School Holiday
# =========================================================
@app.post("/create-school-holiday")
async def create_school_holiday(request: Request):

    form = await request.form()

    school_id = form.get("school_id")
    start_date_value = form.get("start_date")
    end_date_value = form.get("end_date")
    note = form.get("note", "").strip()

    if not school_id or not start_date_value or not end_date_value:
        return RedirectResponse(
            url="/edit",
            status_code=303
        )

    try:
        school_id = int(school_id)
        start_date = date.fromisoformat(
            str(start_date_value)
        )
        end_date = date.fromisoformat(
            str(end_date_value)
        )
    except (ValueError, TypeError):
        return RedirectResponse(
            url="/edit",
            status_code=303
        )

    # Start date cannot be after end date
    if start_date > end_date:
        return RedirectResponse(
            url="/edit?date_str=" + start_date.isoformat(),
            status_code=303
        )

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        INSERT INTO school_calendar
            (
                school_id,
                start_date,
                end_date,
                type,
                note
            )
        VALUES
            (%s, %s, %s, %s, %s)
    """, (
        school_id,
        start_date,
        end_date,
        "holiday",
        note
    ))

    db.commit()

    cursor.close()
    db.close()

    return RedirectResponse(
        url="/edit?date_str=" + start_date.isoformat(),
        status_code=303
    )

# =========================================================
# Delete School Holiday
# =========================================================
@app.post("/delete-school-holiday")
async def delete_school_holiday(request: Request):

    form = await request.form()

    event_id = form.get("event_id")
    week_start = form.get("week_start")

    if not event_id:
        return RedirectResponse(
            url="/edit",
            status_code=303
        )

    try:
        event_id = int(event_id)
    except ValueError:
        return RedirectResponse(
            url="/edit",
            status_code=303
        )

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        DELETE FROM school_calendar
        WHERE id = %s
    """, (
        event_id,
    ))
    deleted_rows = cursor.rowcount

    db.commit()
    print(f"[DELETE SCHOOL HOLIDAY] event_id={event_id}, deleted_rows={deleted_rows}")

    cursor.close()
    db.close()

    if week_start:
        return RedirectResponse(
            url="/edit?date_str=" + str(week_start),
            status_code=303
        )

    return RedirectResponse(
        url="/edit",
        status_code=303
    )

# =========================================================
# Save Weekly Assignments
# =========================================================
@app.post("/save-assignments")
async def save_assignments(request: Request):

    form = await request.form()

    # -----------------------------------------------------
    # Get week start
    # -----------------------------------------------------

    week_start_value = form.get("week_start")

    if not week_start_value:
        return RedirectResponse(
            url="/",
            status_code=303
        )

    week_start = date.fromisoformat(
        str(week_start_value)
    )

    # -----------------------------------------------------
    # Database
    # -----------------------------------------------------

    db = get_db()
    cursor = db.cursor()

    # -----------------------------------------------------
    # Collect submitted assignments
    #
    # Example field:
    #
    # teacher_1_2026-09-21_1 = 8
    #
    # course_id = 1
    # date      = 2026-09-21
    # slot      = 1
    # teacher   = 8
    # -----------------------------------------------------

    assignments = {}
    print(assignments)
    for key, value in form.multi_items():

        if not key.startswith("teacher_"):
            continue

        parts = key.split("_")

        if len(parts) != 4:
            continue

        try:
            course_id = int(parts[1])
            class_date = date.fromisoformat(parts[2])
            slot = int(parts[3])
        except ValueError:
            continue

        # Only save dates belonging to this week
        if not (
            week_start
            <= class_date
            <= week_start + timedelta(days=4)
        ):
            continue

        assignment_key = (
            course_id,
            class_date
        )

        if assignment_key not in assignments:
            assignments[assignment_key] = []

        if value:
            teacher_id = int(value)

            # Avoid duplicate teachers
            if teacher_id not in assignments[assignment_key]:
                assignments[assignment_key].append(
                    teacher_id
                )

    # -----------------------------------------------------
    # Replace assignments
    # -----------------------------------------------------

    for (course_id, class_date), teacher_ids in assignments.items():
        
        cursor.execute("""
            SELECT 1
            FROM school_calendar sc 
            JOIN courses c 
                ON c.school_id = sc.school_id
            WHERE c.id = %s
                AND %s BETWEEN sc.start_date AND sc.end_date
            LIMIT 1
        """, (
            course_id,
            class_date
        ))

        is_holiday = cursor.fetchone() is not None

        cursor.execute("""
            DELETE FROM weekly_assignments
            WHERE course_id = %s
                AND class_date = %s
        """, (
            course_id,
            class_date
        ))

        if is_holiday:
            cursor.execute("""
                INSERT INTO weekly_assignments (
                    course_id, class_date, teacher_id
                )
                VALUES (%s, %s, %s)
            """, (
                course_id,
                class_date,
                18
            ))
            continue

        if not teacher_ids:
            cursor.execute("""
                INSERT INTO weekly_assignments (
                    course_id,
                    class_date,
                    teacher_id
                )
                VALUES (%s, %s, NULL)
            """, (
                course_id,
                class_date,
            ))

        for teacher_id in teacher_ids:
            cursor.execute("""
                INSERT INTO weekly_assignments (
                    course_id,
                    class_date,
                    teacher_id
                )
                VALUES (%s, %s, %s)
            """, (
                course_id,
                class_date,
                teacher_id
            ))

    # -----------------------------------------------------
    # Commit
    # -----------------------------------------------------

    db.commit()

    cursor.close()
    db.close()

    # -----------------------------------------------------
    # Return to the same week
    # -----------------------------------------------------

    return RedirectResponse(
        url="/edit?date_str=" + week_start.isoformat(),
        status_code=303
    )

# =========================================================
# Teacher Schedule - Teacher List
# =========================================================

@app.get("/teacher")
async def teacher_list(request: Request):

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            id,
            name,
            status,
            work_days
        FROM teachers
        WHERE status <> 'hidden'
        ORDER BY name
    """)

    teachers = cursor.fetchall()

    cursor.execute("""
        SELECT
            id,
            teacher_id,
            start_date,
            end_date,
            note
        FROM teacher_leave
        ORDER BY start_date
    """)

    teacher_leaves = cursor.fetchall()

    cursor.close()
    db.close()

    leave_map = {}

    for leave in teacher_leaves:
        teacher_id = leave["teacher_id"]

        if teacher_id not in leave_map:
            leave_map[teacher_id] = []

        leave_map[teacher_id].append(leave)

    return templates.TemplateResponse(
        "teacher_list.html",
        {
            "request": request,
            "teachers": teachers,
            "leave_map": leave_map,
        }
    )

@app.get("/teacher/{teacher_id}")
async def teacher_schedule(
    request: Request,
    teacher_id: int,
    date_str: Optional[str] = None
):

    # ---------------------------------------------------------
    # 1. Calculate selected week
    # ---------------------------------------------------------

    if date_str:

        try:
            selected_date = date.fromisoformat(date_str)

        except ValueError:
            selected_date = date.today()

    else:
        selected_date = date.today()

    week_start = (
        selected_date
        - timedelta(days=selected_date.weekday())
    )

    week_end = week_start + timedelta(days=4)

    week_dates = [
        week_start + timedelta(days=i)
        for i in range(5)
    ]


    # ---------------------------------------------------------
    # 2. Database
    # ---------------------------------------------------------

    db = get_db()
    cursor = db.cursor(dictionary=True)


    # ---------------------------------------------------------
    # 3. Get teacher
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status
        FROM teachers
        WHERE id = %s AND status <> 'hidden'
    """, (teacher_id,))

    teacher = cursor.fetchone()

    if not teacher:

        cursor.close()
        db.close()

        return RedirectResponse(
            url="/",
            status_code=303
        )


    # ---------------------------------------------------------
    # 4. Get all teachers
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status
        FROM teachers
        WHERE status <> 'hidden'
        ORDER BY name
    """)

    teachers = cursor.fetchall()


    # ---------------------------------------------------------
    # 5. Get all courses
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            c.id,
            c.school_id,
            c.course_name,
            c.day_of_week,
            c.start_time,
            c.end_time,
            c.classroom,
            c.group_name,
            c.student_number,
            s.name AS school_name
        FROM courses c
        JOIN schools s
            ON c.school_id = s.id
        ORDER BY
            c.day_of_week,
            c.start_time,
            s.name,
            c.course_name
    """)

    courses = cursor.fetchall()


    # ---------------------------------------------------------
    # 6. Get default course teachers
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            teacher_id
        FROM course_teachers
    """)

    course_teacher_rows = cursor.fetchall()

    course_teacher_map = {}

    for row in course_teacher_rows:

        course_id = row["course_id"]

        if course_id not in course_teacher_map:

            course_teacher_map[course_id] = []

        if len(course_teacher_map[course_id]) < 4:

            course_teacher_map[course_id].append(
                row["teacher_id"]
            )


    # ---------------------------------------------------------
    # 7. Get weekly assignments
    #
    # We need:
    # - current week
    # - previous weeks
    #
    # because a course can inherit the most recent
    # assignment from a previous occurrence of the same weekday.
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            class_date,
            teacher_id
        FROM weekly_assignments
        WHERE class_date <= %s
            AND (teacher_id IS NULL OR teacher_id <> %s)
        ORDER BY
            class_date DESC,
            id DESC
    """, (week_end, 18))

    all_weekly_assignments = cursor.fetchall()


    # ---------------------------------------------------------
    # 8. Exact weekly assignment map
    #
    # Key:
    #     (course_id, class_date)
    #
    # If the key exists, it is an explicit assignment.
    # Even if teacher_id is NULL, it means explicitly unassigned.
    # ---------------------------------------------------------

    weekly_assignment_map = {}

    for item in all_weekly_assignments:

        key = (
            item["course_id"],
            item["class_date"]
        )

        if key not in weekly_assignment_map:

            weekly_assignment_map[key] = []

        if item["teacher_id"] == 18:
            # 但要注意：如果这一天的记录里同时有隐藏老师和真实老师，
            # 真实老师仍然要保留。
            # 简单做法：只要遇到隐藏老师就跳过这条 item。
            pass

        if item["teacher_id"] is not None:

            if len(weekly_assignment_map[key]) < 4:

                weekly_assignment_map[key].append(
                    item["teacher_id"]
                )


    # ---------------------------------------------------------
    # 9. Inherited assignment map
    #
    # For every course + weekday, find the most recent
    # previous occurrence.
    #
    # Explicit NULL means:
    #     no teacher
    #
    # and therefore it must NOT inherit further backwards.
    # ---------------------------------------------------------

    inherited_assignment_map = {}
    inherited_assignment_date = {}

    for item in all_weekly_assignments:

        if item["class_date"] >= week_start:
            continue

        course_id = item["course_id"]

        weekday = item["class_date"].weekday()

        key = (
            course_id,
            weekday
        )

        if key not in inherited_assignment_date:

            inherited_assignment_date[key] = (
                item["class_date"]
            )

            inherited_assignment_map[key] = []

        if (
            item["class_date"]
            == inherited_assignment_date[key]
        ):

            if item["teacher_id"] is not None:

                if len(
                    inherited_assignment_map[key]
                ) < 4:

                    inherited_assignment_map[key].append(
                        item["teacher_id"]
                    )


    # ---------------------------------------------------------
    # 10. Get school calendar
    #
    # Any record means the school does not have class
    # on that date.
    #
    # We intentionally DO NOT check "type".
    # ---------------------------------------------------------

    cursor.execute("""
        SELECT 
            id,
            school_id,
            start_date,
            end_date,
            type,
            note
        FROM school_calendar
        WHERE start_date <= %s
          AND end_date >= %s
    """, (
        week_end,
        week_start
    ))

    calendar_rows = cursor.fetchall()

    calendar_map = {}

    for event in calendar_rows:

        current = event["start_date"]

        while current <= event["end_date"]:

            key = (
                event["school_id"],
                current
            )

            if key not in calendar_map:

                calendar_map[key] = []

            calendar_map[key].append(event)

            current += timedelta(days=1)


    # ---------------------------------------------------------
    # 11. Build teacher schedule
    # ---------------------------------------------------------

    days = []

    for current_date in week_dates:

        day_courses = []

        weekday = current_date.weekday()

        for course in courses:

            if course["day_of_week"] != weekday + 1:
                continue


            # -------------------------------------------------
            # Determine effective teachers
            # -------------------------------------------------

            exact_key = (
                course["id"],
                current_date
            )

            inherited_key = (
                course["id"],
                weekday
            )


            if exact_key in weekly_assignment_map:

                teacher_ids = weekly_assignment_map[
                    exact_key
                ]

                assignment_source = "weekly"

            elif inherited_key in inherited_assignment_map:

                teacher_ids = inherited_assignment_map[
                    inherited_key
                ]

                assignment_source = "inherited"

            else:

                teacher_ids = course_teacher_map.get(
                    course["id"],
                    []
                )

                assignment_source = "default"


            # -------------------------------------------------
            # Is this teacher assigned?
            # -------------------------------------------------

            if teacher_id not in teacher_ids:
                continue


            # -------------------------------------------------
            # School holiday
            # -------------------------------------------------

            events = calendar_map.get(
                (
                    course["school_id"],
                    current_date
                ),
                []
            )

            is_holiday = bool(events)


            # Teacher schedule should hide holidays.
            if is_holiday:
                continue


            # -------------------------------------------------
            # Format time
            # -------------------------------------------------

            start_time_display = str(
                course["start_time"]
            )[:5]

            end_time_display = str(
                course["end_time"]
            )[:5]


            # -------------------------------------------------
            # School colors
            # -------------------------------------------------

            school_color = get_school_color(
                course["school_name"],
                course["school_id"]
            )


            # -------------------------------------------------
            # Course data
            # -------------------------------------------------

            course_data = {
                "id": course["id"],
                "school_id": course["school_id"],
                "school_name": course["school_name"],
                "course_name": course["course_name"],
                "day_of_week": course["day_of_week"],
                "start_time_display": start_time_display,
                "end_time_display": end_time_display,
                "classroom": course["classroom"],
                "group_name": course["group_name"],
                "student_number": course["student_number"],
                "assignment_source": assignment_source,
                "school_background": school_color["background"],
                "school_border": school_color["border"],
            }

            day_courses.append(course_data)


        # -----------------------------------------------------
        # Sort courses by start time
        # -----------------------------------------------------

        day_courses.sort(
            key=lambda x: (
                x["start_time_display"],
                x["school_name"],
                x["course_name"]
            )
        )


        days.append({
            "date": current_date,
            "courses": day_courses
        })


    cursor.close()
    db.close()


    # ---------------------------------------------------------
    # 12. Render
    # ---------------------------------------------------------

    return templates.TemplateResponse(
        "teacher_schedule.html",
        {
            "request": request,
            "teacher": teacher,
            "teachers": teachers,
            "teacher_id": teacher_id,
            "days": days,
            "week_dates": week_dates,
            "week_start": week_start,
            "week_end": week_end,
            "selected_date": selected_date,
        }
    )

# =========================================================
# View Schedule
# =========================================================

@app.get("/view")
async def view_schedule(
    request: Request,
    date_str: Optional[str] = None
):

    # -----------------------------------------------------
    # 1. Determine selected week
    # -----------------------------------------------------

    if date_str:

        try:
            selected_date = date.fromisoformat(
                date_str
            )

        except ValueError:
            selected_date = date.today()

    else:
        selected_date = date.today()


    week_start = (
        selected_date
        - timedelta(days=selected_date.weekday())
    )

    week_end = week_start + timedelta(days=4)

    week_dates = [
        week_start + timedelta(days=i)
        for i in range(5)
    ]


    # -----------------------------------------------------
    # 2. Database
    # -----------------------------------------------------

    db = get_db()
    cursor = db.cursor(dictionary=True)


    # -----------------------------------------------------
    # 3. Schools
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status
        FROM schools
        ORDER BY name
    """)

    schools = cursor.fetchall()


    # -----------------------------------------------------
    # 4. Courses
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            c.id,
            c.school_id,
            s.name AS school_name,
            c.course_name,
            c.day_of_week,
            c.start_time,
            c.end_time,
            c.classroom,
            c.group_name,
            c.student_number
        FROM courses c
        JOIN schools s
            ON c.school_id = s.id
        ORDER BY
            c.day_of_week,
            c.start_time,
            s.name,
            c.course_name
    """)

    courses = cursor.fetchall()


    # -----------------------------------------------------
    # 5. Teachers
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            id,
            name,
            status
        FROM teachers
        WHERE status <> 'hidden'
        ORDER BY name
    """)

    teachers = cursor.fetchall()

    teacher_name_map = {
        teacher["id"]: teacher["name"]
        for teacher in teachers
    }


    # -----------------------------------------------------
    # 6. Default course teachers
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            teacher_id
        FROM course_teachers
        ORDER BY course_id, teacher_id
    """)

    course_teacher_rows = cursor.fetchall()

    default_teacher_map = {}

    for item in course_teacher_rows:

        course_id = item["course_id"]

        if course_id not in default_teacher_map:

            default_teacher_map[course_id] = []

        if len(default_teacher_map[course_id]) < 4:

            default_teacher_map[course_id].append(
                item["teacher_id"]
            )


    # -----------------------------------------------------
    # 7. Weekly assignments
    #
    # Get all assignments before / during this week
    # so previous assignments can be inherited.
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            course_id,
            class_date,
            teacher_id
        FROM weekly_assignments
        WHERE class_date <= %s
            AND (teacher_id IS NULL OR teacher_id <> %s)
        ORDER BY
            course_id,
            class_date DESC,
            teacher_id
    """, (
        week_end,
        18
    ))

    all_weekly_assignments = cursor.fetchall()


    # -----------------------------------------------------
    # 8. Exact weekly assignments
    # -----------------------------------------------------

    weekly_assignment_map = {}

    for item in all_weekly_assignments:

        key = (
            item["course_id"],
            item["class_date"]
        )

        if key not in weekly_assignment_map:

            weekly_assignment_map[key] = []

        if item["teacher_id"] is not None:

            if len(
                weekly_assignment_map[key]
            ) < 4:

                weekly_assignment_map[key].append(
                    item["teacher_id"]
                )


    # -----------------------------------------------------
    # 9. Inherited assignments
    # -----------------------------------------------------

    inherited_assignment_map = {}
    inherited_assignment_date = {}

    for item in all_weekly_assignments:

        if item["class_date"] >= week_start:
            continue

        course_id = item["course_id"]

        weekday = item["class_date"].weekday()

        key = (
            course_id,
            weekday
        )

        if key not in inherited_assignment_date:

            inherited_assignment_date[key] = (
                item["class_date"]
            )

            inherited_assignment_map[key] = []


        if (
            item["class_date"]
            == inherited_assignment_date[key]
        ):

            if item["teacher_id"] is not None:

                if len(
                    inherited_assignment_map[key]
                ) < 4:

                    inherited_assignment_map[key].append(
                        item["teacher_id"]
                    )


    # -----------------------------------------------------
    # 10. School calendar
    #
    # Any calendar record means no class.
    # -----------------------------------------------------

    cursor.execute("""
        SELECT
            school_id,
            start_date,
            end_date,
            type,
            note
        FROM school_calendar
        WHERE start_date <= %s
          AND end_date >= %s
    """, (
        week_end,
        week_start
    ))

    calendar_events = cursor.fetchall()

    calendar_map = {}

    for event in calendar_events:

        current = event["start_date"]

        while current <= event["end_date"]:

            key = (
                event["school_id"],
                current
            )

            if key not in calendar_map:

                calendar_map[key] = []

            calendar_map[key].append(event)

            current += timedelta(days=1)


    # -----------------------------------------------------
    # 11. Build days
    # -----------------------------------------------------

    days = []

    for current_date in week_dates:

        day_courses = []

        weekday = current_date.weekday()


        for course in courses:

            if course["day_of_week"] != weekday + 1:
                continue


            # -------------------------------------------------
            # Determine effective teachers
            # -------------------------------------------------

            exact_key = (
                course["id"],
                current_date
            )

            inherited_key = (
                course["id"],
                weekday
            )


            if exact_key in weekly_assignment_map:

                teacher_ids = weekly_assignment_map[
                    exact_key
                ]

                assignment_source = "weekly"

            elif inherited_key in inherited_assignment_map:

                teacher_ids = inherited_assignment_map[
                    inherited_key
                ]

                assignment_source = "inherited"

            else:

                teacher_ids = default_teacher_map.get(
                    course["id"],
                    []
                )

                assignment_source = "default"


            # -------------------------------------------------
            # Holiday
            # -------------------------------------------------

            events = calendar_map.get(
                (
                    course["school_id"],
                    current_date
                ),
                []
            )

            is_holiday = bool(events)

            if is_holiday:
                continue


            # -------------------------------------------------
            # School color
            # -------------------------------------------------

            school_color = SCHOOL_COLORS.get(
                course["school_name"],
                {
                    "background": "#F8FAFC",
                    "border": "#9AA4B2",
                }
            )


            # -------------------------------------------------
            # Format time
            # -------------------------------------------------

            start_time_display = str(
                course["start_time"]
            )[:5]

            end_time_display = str(
                course["end_time"]
            )[:5]


            # -------------------------------------------------
            # Teacher names
            # -------------------------------------------------

            teacher_names = []

            for teacher_id in teacher_ids[:4]:

                if teacher_id is None:
                    continue

                teacher_name = teacher_name_map.get(
                    teacher_id,
                    "Unknown teacher"
                )

                teacher_names.append(
                    teacher_name
                )


            # -------------------------------------------------
            # Course data
            # -------------------------------------------------

            course_data = {
                "id": course["id"],
                "school_id": course["school_id"],
                "school_name": course["school_name"],
                "course_name": course["course_name"],
                "day_of_week": course["day_of_week"],
                "start_time_display":
                    start_time_display,
                "end_time_display":
                    end_time_display,
                "classroom":
                    course["classroom"],
                "group_name":
                    course["group_name"],
                "student_number":
                    course["student_number"],
                "teacher_names":
                    teacher_names,
                "assignment_source":
                    assignment_source,
                "school_background":
                    school_color["background"],
                "school_border":
                    school_color["border"],
                "is_holiday":
                    is_holiday,
                "calendar_events":
                    events,
            }


            day_courses.append(
                course_data
            )


        # -----------------------------------------------------
        # Sort by time first
        # -----------------------------------------------------

        day_courses.sort(
            key=lambda c: (
                c["start_time_display"],
                c["school_name"],
                c["course_name"]
            )
        )


        days.append({
            "date": current_date,
            "courses": day_courses
        })


    cursor.close()
    db.close()


    # -----------------------------------------------------
    # 12. Render
    # -----------------------------------------------------

    return templates.TemplateResponse(
        "view_schedule.html",
        {
            "request": request,
            "days": days,
            "week_dates": week_dates,
            "selected_date":
                selected_date.isoformat(),
            "week_start":
                week_start.isoformat(),
            "week_end":
                week_end.isoformat(),
        }
    )

# =========================================================
# Create Course
# =========================================================

@app.post("/create-course")
async def create_course(request: Request):

    form = await request.form()

    school_id_value = form.get("school_id")
    course_name = str(
        form.get("course_name", "")
    ).strip()

    day_of_week_value = form.get("day_of_week")

    start_time = str(
        form.get("start_time", "")
    ).strip()

    end_time = str(
        form.get("end_time", "")
    ).strip()

    classroom = str(
        form.get("classroom", "")
    ).strip()

    group_name = str(
        form.get("group_name", "")
    ).strip()

    student_number_value = str(
        form.get("student_number", "")
    ).strip()

    # -----------------------------------------------------
    # Validate school
    # -----------------------------------------------------

    try:
        school_id = int(school_id_value)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Please select a school."
        }

    # -----------------------------------------------------
    # Validate course name
    # -----------------------------------------------------

    if not course_name:
        return {
            "success": False,
            "message": "Course name cannot be empty."
        }

    # -----------------------------------------------------
    # Validate day
    # -----------------------------------------------------

    try:
        day_of_week = int(day_of_week_value)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Invalid day."
        }

    if day_of_week < 1 or day_of_week > 5:
        return {
            "success": False,
            "message": "Day must be Monday to Friday."
        }

    # -----------------------------------------------------
    # Validate time
    # -----------------------------------------------------

    if not start_time or not end_time:
        return {
            "success": False,
            "message": "Start time and end time are required."
        }

    if end_time <= start_time:
        return {
            "success": False,
            "message": "End time must be after start time."
        }

    # -----------------------------------------------------
    # Validate students
    # -----------------------------------------------------

    if student_number_value == "":
        student_number = None

    else:

        try:
            student_number = int(
                student_number_value
            )
        except ValueError:
            return {
                "success": False,
                "message": "Student number must be a number."
            }

        if student_number < 0:
            return {
                "success": False,
                "message": "Student number cannot be negative."
            }

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # -----------------------------------------------------
    # Check school exists
    # -----------------------------------------------------

    cursor.execute(
        """
        SELECT id
        FROM schools
        WHERE id = %s
        """,
        (school_id,)
    )

    school = cursor.fetchone()

    if school is None:

        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "School not found."
        }

    # -----------------------------------------------------
    # Create course
    # -----------------------------------------------------

    cursor.execute(
        """
        INSERT INTO courses
        (
            school_id,
            course_name,
            day_of_week,
            start_time,
            end_time,
            classroom,
            group_name,
            student_number
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        (
            school_id,
            course_name,
            day_of_week,
            start_time,
            end_time,
            classroom,
            group_name,
            student_number
        )
    )

    course_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Course created successfully.",
        "course_id": course_id
    }

# =========================================================
# Create School
# =========================================================

@app.post("/create-school")
async def create_school(request: Request):

    form = await request.form()

    school_name = str(
        form.get("school_name", "")
    ).strip()

    if not school_name:
        return {
            "success": False,
            "message": "School name cannot be empty."
        }

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id
        FROM schools
        WHERE name = %s
        """,
        (school_name,)
    )

    existing_school = cursor.fetchone()

    if existing_school is not None:

        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "This school already exists."
        }

    cursor.execute(
        """
        INSERT INTO schools
            (name)
        VALUES
            (%s)
        """,
        (school_name,)
    )

    school_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "School added successfully.",
        "school_id": school_id,
        "school_name": school_name
    }

@app.post("/update-course")
async def update_course(request: Request):

    form = await request.form()

    course_id_value = form.get("course_id")

    if not course_id_value:
        return {
            "success": False,
            "message": "Missing course ID"
        }

    try:
        course_id = int(course_id_value)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid course ID"
        }

    course_name = str(
        form.get("course_name", "")
    ).strip()

    start_time = str(
        form.get("start_time", "")
    ).strip()

    end_time = str(
        form.get("end_time", "")
    ).strip()

    classroom = str(
        form.get("classroom", "")
    ).strip()

    group_name = str(
        form.get("group_name", "")
    ).strip()

    student_number_value = str(
        form.get("student_number", "")
    ).strip()


    if not course_name:

        return {
            "success": False,
            "message": "Course name cannot be empty"
        }


    if not start_time or not end_time:

        return {
            "success": False,
            "message": "Start time and end time are required"
        }


    try:

        student_number = int(
            student_number_value
        )

    except ValueError:

        return {
            "success": False,
            "message": "Student number must be a number"
        }


    if student_number < 0:

        return {
            "success": False,
            "message": "Student number cannot be negative"
        }


    if end_time <= start_time:

        return {
            "success": False,
            "message": "End time must be after start time"
        }


    db = get_db()
    cursor = db.cursor()


    # First check that the course actually exists

    cursor.execute(
        """
        SELECT id
        FROM courses
        WHERE id = %s
        """,
        (course_id,)
    )

    course = cursor.fetchone()


    if course is None:

        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Course not found"
        }


    # Update the recurring course

    cursor.execute(
        """
        UPDATE courses
        SET
            course_name = %s,
            start_time = %s,
            end_time = %s,
            classroom = %s,
            group_name = %s,
            student_number = %s
        WHERE id = %s
        """,
        (
            course_name,
            start_time,
            end_time,
            classroom,
            group_name,
            student_number,
            course_id
        )
    )


    db.commit()


    cursor.close()
    db.close()


    return {
        "success": True,
        "message": "Course updated successfully"
    }

@app.post("/delete-course")
async def delete_course(request: Request):
    form = await request.form()

    course_id_value = form.get("course_id")

    if not course_id_value:
        return {
            "success": False,
            "message": "Missing course ID."
        }

    try:
        course_id = int(course_id_value)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid course ID."
        }

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check that the course exists
    cursor.execute(
        """
        SELECT
            c.id,
            c.course_name,
            s.name AS school_name
        FROM courses c
        JOIN schools s
            ON c.school_id = s.id
        WHERE c.id = %s
        """,
        (course_id,)
    )

    course = cursor.fetchone()

    if course is None:
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Course not found."
        }

    # Delete the course
    #
    # course_teachers has ON DELETE CASCADE,
    # so teacher assignments are removed automatically.
    #
    # weekly_assignments also has ON DELETE CASCADE,
    # so weekly teacher overrides are removed automatically.

    cursor.execute(
        """
        DELETE FROM courses
        WHERE id = %s
        """,
        (course_id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Course deleted successfully.",
        "course_id": course_id,
        "course_name": course["course_name"],
        "school_name": course["school_name"]
    }


@app.post("/create-teacher")
async def create_teacher(request: Request):
    form = await request.form()

    teacher_name = str(
        form.get("teacher_name", "")
    ).strip()

    status = str(
        form.get("status", "")
    ).strip()

    if not teacher_name:
        return {
            "success": False,
            "message": "Teacher name cannot be empty."
        }

    db = get_db()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id
        FROM teachers
        WHERE name = %s AND status <> 'hidden'
        """,
        (teacher_name,)
    )

    existing_teacher = cursor.fetchone()

    if existing_teacher is not None:
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "This teacher already exists."
        }

    cursor.execute(
        """
        INSERT INTO teachers
            (name, status)
        VALUES
            (%s, %s)
        """,
        (
            teacher_name,
            status
        )
    )

    teacher_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Teacher added successfully.",
        "teacher_id": teacher_id,
        "teacher_name": teacher_name
    }

@app.post("/delete-teacher")
async def delete_teacher(request: Request):
    form = await request.form()

    teacher_id_value = form.get("teacher_id")

    if not teacher_id_value:
        return {
            "success": False,
            "message": "Missing teacher ID."
        }

    try:
        teacher_id = int(teacher_id_value)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid teacher ID."
        }

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check teacher exists
    cursor.execute(
        """
        SELECT
            id,
            name
        FROM teachers
        WHERE id = %s
        """,
        (teacher_id,)
    )

    teacher = cursor.fetchone()

    if teacher is None:
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Teacher not found."
        }

    try:
        cursor.execute(
            """
            DELETE FROM teachers
            WHERE id = %s
            """,
            (teacher_id,)
        )

        db.commit()

    except Exception as error:

        db.rollback()

        cursor.close()
        db.close()

        print(error)

        return {
            "success": False,
            "message": (
                "This teacher is still assigned to "
                "one or more courses or schedules."
            )
        }

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Teacher deleted successfully.",
        "teacher_id": teacher_id,
        "teacher_name": teacher["name"]
    }


@app.post("/create-teacher-leave")
async def create_teacher_leave(request: Request):

    form = await request.form()

    teacher_id_value = form.get("teacher_id")
    start_date = str(
        form.get("start_date", "")
    ).strip()
    end_date = str(
        form.get("end_date", "")
    ).strip()
    note = str(
        form.get("note", "")
    ).strip()


    if not teacher_id_value:
        return {
            "success": False,
            "message": "Missing teacher ID."
        }


    try:
        teacher_id = int(teacher_id_value)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid teacher ID."
        }


    if not start_date or not end_date:
        return {
            "success": False,
            "message": "Start and end dates are required."
        }


    if end_date < start_date:
        return {
            "success": False,
            "message": "End date cannot be before start date."
        }


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute(
        """
        SELECT id
        FROM teachers
        WHERE id = %s
        """,
        (teacher_id,)
    )

    teacher = cursor.fetchone()


    if teacher is None:

        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Teacher not found."
        }


    cursor.execute(
        """
        INSERT INTO teacher_leave
            (teacher_id, start_date, end_date, note)
        VALUES
            (%s, %s, %s, %s)
        """,
        (
            teacher_id,
            start_date,
            end_date,
            note or None
        )
    )


    leave_id = cursor.lastrowid

    db.commit()

    cursor.close()
    db.close()


    return {
        "success": True,
        "message": "Teacher leave added successfully.",
        "leave_id": leave_id
    }

@app.post("/delete-teacher-leave")
async def delete_teacher_leave(request: Request):

    form = await request.form()

    leave_id_value = form.get("leave_id")


    if not leave_id_value:
        return {
            "success": False,
            "message": "Missing leave ID."
        }


    try:
        leave_id = int(leave_id_value)
    except ValueError:
        return {
            "success": False,
            "message": "Invalid leave ID."
        }


    db = get_db()
    cursor = db.cursor(dictionary=True)


    cursor.execute(
        """
        SELECT id
        FROM teacher_leave
        WHERE id = %s
        """,
        (leave_id,)
    )

    leave = cursor.fetchone()


    if leave is None:

        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Leave record not found."
        }


    cursor.execute(
        """
        DELETE FROM teacher_leave
        WHERE id = %s
        """,
        (leave_id,)
    )


    db.commit()

    cursor.close()
    db.close()


    return {
        "success": True,
        "message": "Teacher leave deleted successfully."
    }


# =========================================================
# Update Teacher Working Days
# =========================================================

@app.post("/update-teacher-workdays")
async def update_teacher_workdays(request: Request):

    form = await request.form()

    teacher_id_value = form.get("teacher_id")
    work_days_value = form.get("work_days")

    # Validate teacher ID
    try:
        teacher_id = int(teacher_id_value)
    except (TypeError, ValueError):
        return {
            "success": False,
            "message": "Invalid teacher ID."
        }

    # Convert work_days string to list
    # Example:
    # "1,2,4,5" -> [1, 2, 4, 5]
    if work_days_value:
        try:
            workdays = [
                int(day.strip())
                for day in work_days_value.split(",")
                if day.strip()
            ]
        except (TypeError, ValueError):
            return {
                "success": False,
                "message": "Invalid workday value."
            }
    else:
        workdays = []

    # Only Monday-Friday
    if any(day < 1 or day > 5 for day in workdays):
        return {
            "success": False,
            "message": "Workdays must be between 1 and 5."
        }

    # Remove duplicates and sort
    workdays = sorted(set(workdays))

    # Convert back to DB format
    # [1, 2, 4, 5] -> "1,2,4,5"
    work_days_value = ",".join(
        str(day)
        for day in workdays
    )

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Check teacher exists
    cursor.execute(
        """
        SELECT id
        FROM teachers
        WHERE id = %s
        """,
        (teacher_id,)
    )

    teacher = cursor.fetchone()

    if teacher is None:
        cursor.close()
        db.close()

        return {
            "success": False,
            "message": "Teacher not found."
        }

    # Update working days
    cursor.execute(
        """
        UPDATE teachers
        SET work_days = %s
        WHERE id = %s
        """,
        (
            work_days_value,
            teacher_id
        )
    )

    db.commit()

    cursor.close()
    db.close()

    return {
        "success": True,
        "message": "Working days updated successfully.",
        "teacher_id": teacher_id,
        "workdays": workdays
    }

