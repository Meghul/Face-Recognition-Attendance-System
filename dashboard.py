import sys
import csv
import subprocess
from datetime import date
from attendance_editor import AttendanceEditor

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem,
    QCalendarWidget, QListWidget, QStackedWidget,
    QInputDialog, QMessageBox
)

from PySide6.QtWidgets import QHeaderView
from PySide6.QtCore import Qt

from attendance import AttendanceWindow
from student_profile import StudentProfile
from config import ATTENDANCE_DIR, IMAGES_DIR


class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Classroom Attendance Monitor")
        self.resize(1300,800)

        self.setStyleSheet("""

        QMainWindow{
            background:#0f172a;
        }

        QLabel{
            color:white;
        }

        QListWidget{
            background:#020617;
            border:none;
            color:#94a3b8;
            font-size:14px;
        }

        QListWidget::item{
            padding:12px;
            border-radius:6px;
        }

        QListWidget::item:selected{
            background:#1e293b;
            color:white;
        }

        QListWidget::item:hover{
            background:#334155;
            color:white;
        }

        QFrame{
            background:#020617;
            border-radius:10px;
        }

        QTableWidget{
            background:#020617;
            border:none;
            color:white;
            gridline-color:#1e293b;
        }

        QHeaderView::section{
            background:#0f172a;
            color:#94a3b8;
            border:none;
            padding:6px;
        }

        QPushButton{
            background:#6366f1;
            padding:12px;
            border-radius:8px;
            color:white;
            font-weight:bold;
        }

        QPushButton:hover{
            background:#4f46e5;
        }

        /* -------- FIX CALENDAR VISIBILITY -------- */

        QCalendarWidget QWidget{
            background:#020617;
            color:white;
        }

        QCalendarWidget QToolButton{
            color:white;
            background:#1e293b;
            font-weight:bold;
        }

        QCalendarWidget QAbstractItemView:enabled{
            background:#020617;
            color:white;
            selection-background-color:#6366f1;
            selection-color:white;
        }

        /* -------- FIX DROPDOWN VISIBILITY -------- */

        QComboBox{
            background:white;
            color:black;
            padding:4px;
        }

        QComboBox QAbstractItemView{
            background:white;
            color:black;
            selection-background-color:#6366f1;
            selection-color:white;
        }

        /* -------- FIX INPUT DIALOG -------- */

        QInputDialog{
            background:white;
            color:black;
        }

        """)

        container = QWidget()
        self.setCentralWidget(container)

        main_layout = QHBoxLayout()

        # ---------------- Sidebar ----------------

        sidebar = QVBoxLayout()

        logo = QLabel("AI Attendance System")
        logo.setStyleSheet("font-size:20px;font-weight:bold")

        sidebar.addWidget(logo)

        self.menu = QListWidget()

        self.menu.addItems([
            "Dashboard",
            "Take Attendance",
            "Enroll Student",
            "Student Profiles",
            "Attendance Logs"
        ])

        self.menu.currentRowChanged.connect(self.switch_page)

        sidebar.addWidget(self.menu)
        sidebar.addStretch()

        main_layout.addLayout(sidebar,1)

        # ---------------- Pages ----------------

        self.pages = QStackedWidget()

        self.dashboard_page = self.create_dashboard()
        self.profiles_page = self.create_profiles_page()
        self.logs_page = self.create_logs()

        self.pages.addWidget(self.dashboard_page)
        self.pages.addWidget(QWidget())
        self.pages.addWidget(QWidget())
        self.pages.addWidget(self.profiles_page)
        self.pages.addWidget(self.logs_page)

        main_layout.addWidget(self.pages,4)

        container.setLayout(main_layout)

        self.load_recent()

    # ---------------- Student Profiles Page ----------------

    def create_profiles_page(self):

        page = QWidget()
        layout = QVBoxLayout()

        title = QLabel("Student Profiles")
        title.setStyleSheet("font-size:28px;font-weight:bold")

        layout.addWidget(title)

        self.student_list = QListWidget()

        if IMAGES_DIR.exists():
            students = [f.stem for f in IMAGES_DIR.iterdir()]
            self.student_list.addItems(students)

        self.student_list.itemClicked.connect(self.open_profile_from_list)

        layout.addWidget(self.student_list)

        page.setLayout(layout)

        return page

    def open_profile_from_list(self,item):

        student = item.text()

        self.profile = StudentProfile(student)
        self.profile.show()

    # ---------------- Dashboard Page ----------------

    def create_dashboard(self):

        page = QWidget()
        layout = QVBoxLayout()

        title = QLabel("System Dashboard")
        title.setStyleSheet("font-size:28px;font-weight:bold")

        layout.addWidget(title)

        stats_layout = QHBoxLayout()

        stats_layout.addWidget(self.card("Total Students", self.count_students()))
        stats_layout.addWidget(self.card("Today's Attendance", self.today_attendance()))
        stats_layout.addWidget(self.card("Classes Conducted", self.count_classes()))
        stats_layout.addWidget(self.card("Last Subject", self.last_subject()))

        layout.addLayout(stats_layout)

        recent_title = QLabel("Recent Activity")
        recent_title.setStyleSheet("font-size:18px")

        layout.addWidget(recent_title)

        self.table = QTableWidget()

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Student","Subject","Date","Status"]
        )

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)

        layout.addWidget(self.table)

        take_btn = QPushButton("Take Attendance")
        take_btn.clicked.connect(self.take_attendance)

        layout.addWidget(take_btn)

        page.setLayout(layout)

        return page

    # ---------------- Card Widget ----------------

    def card(self,title,value):

        card = QFrame()

        layout = QVBoxLayout()

        t = QLabel(title)
        t.setStyleSheet("color:#94a3b8")

        v = QLabel(str(value))
        v.setStyleSheet("font-size:26px;font-weight:bold")

        layout.addWidget(t)
        layout.addWidget(v)

        card.setLayout(layout)

        return card

    # ---------------- Dashboard Calculations ----------------

    def count_students(self):

        if IMAGES_DIR.exists():
            return len(list(IMAGES_DIR.iterdir()))

        return 0

    def today_attendance(self):

        today = date.today().strftime("%Y-%m-%d")

        present = 0
        total = self.count_students()

        if ATTENDANCE_DIR.exists():

            for subject in ATTENDANCE_DIR.iterdir():

                file = subject / f"{today}.csv"

                if file.exists():

                    with open(file) as f:

                        reader = csv.DictReader(f)

                        for r in reader:

                            if r["Status"] == "Present":
                                present += 1

        return f"{present} / {total}"

    def count_classes(self):

        total = 0

        if ATTENDANCE_DIR.exists():

            for subject in ATTENDANCE_DIR.iterdir():

                total += len(list(subject.glob("*.csv")))

        return total

    def last_subject(self):

        latest_date = None
        latest_subject = "-"

        if ATTENDANCE_DIR.exists():

            for subject in ATTENDANCE_DIR.iterdir():

                for file in subject.glob("*.csv"):

                    d = file.stem

                    if latest_date is None or d > latest_date:
                        latest_date = d
                        latest_subject = subject.name

        return latest_subject

    # ---------------- Recent Activity ----------------

    def load_recent(self):

        today = date.today().strftime("%Y-%m-%d")

        rows = []

        if ATTENDANCE_DIR.exists():

            for subject in ATTENDANCE_DIR.iterdir():

                file = subject / f"{today}.csv"

                if file.exists():

                    with open(file) as f:

                        reader = csv.DictReader(f)

                        for r in reader:

                            rows.append({
                                "student": r["Student"],
                                "subject": subject.name,
                                "date": today,
                                "status": r["Status"]
                            })

        self.table.setRowCount(len(rows))

        for i,r in enumerate(rows):

            self.table.setItem(i,0,QTableWidgetItem(r["student"]))
            self.table.setItem(i,1,QTableWidgetItem(r["subject"]))
            self.table.setItem(i,2,QTableWidgetItem(r["date"]))
            self.table.setItem(i,3,QTableWidgetItem(r["status"]))

    # ---------------- Logs Page ----------------

    def create_logs(self):

        page = QWidget()

        layout = QHBoxLayout()

        calendar_box = QVBoxLayout()

        self.calendar = QCalendarWidget()
        self.calendar.setFixedSize(320,260)

        self.calendar.clicked.connect(self.load_logs)

        calendar_box.addWidget(self.calendar)
        calendar_box.addStretch()

        layout.addLayout(calendar_box,1)

        self.logs_table = QTableWidget()

        self.logs_table.setColumnCount(6)

        self.logs_table.setHorizontalHeaderLabels([
            "Student",
            "Subject",
            "Classes Attended",
            "Total Classes",
            "Attendance %",
            "Status"
        ])

        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.verticalHeader().setVisible(False)

        layout.addWidget(self.logs_table,3)
        edit_btn = QPushButton("Edit Attendance")
        edit_btn.clicked.connect(self.edit_attendance)
        layout.addWidget(edit_btn)

        page.setLayout(layout)

        return page

    def load_logs(self,date):

        subjects = [p.name for p in ATTENDANCE_DIR.iterdir()]

        if not subjects:

            QMessageBox.information(self,"Info","No subjects found")
            return

        subject, ok = QInputDialog.getItem(
            self,"Select Subject","Subject:",subjects,0,False
        )

        if not ok:
            return

        subject_path = ATTENDANCE_DIR / subject

        students = {}

        files = list(subject_path.glob("*.csv"))
        total_classes = len(files)

        for file in files:

            with open(file) as f:

                reader = csv.DictReader(f)

                for r in reader:

                    name = r["Student"].strip()

                    if name not in students:
                        students[name] = 0

                    if r["Status"] == "Present":
                        students[name] += 1

        rows = []

        for student, attended in students.items():

            percent = int((attended/total_classes)*100) if total_classes else 0

            if percent >= 75:
                status = "Good"
            elif percent >= 50:
                status = "Warning"
            else:
                status = "Low"

            rows.append((student,subject,attended,total_classes,f"{percent}%",status))

        self.logs_table.setRowCount(len(rows))

        for i,row in enumerate(rows):

            for j,val in enumerate(row):

                self.logs_table.setItem(i,j,QTableWidgetItem(str(val)))


    def edit_attendance(self):

        subjects = [p.name for p in ATTENDANCE_DIR.iterdir()]

        if not subjects:
            QMessageBox.information(self,"Info","No subjects found")
            return

        subject, ok = QInputDialog.getItem(
            self,"Select Subject","Subject:",subjects,0,False
    )

        if not ok:
            return

        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")

        file_path = ATTENDANCE_DIR / subject / f"{selected_date}.csv"

        if not file_path.exists():
            QMessageBox.warning(self,"Error","No attendance file found")
            return

        self.editor = AttendanceEditor(file_path)
        self.editor.show()    

    # ---------------- Navigation ----------------

    def switch_page(self,index):

        if index == 1:
            self.take_attendance()

        elif index == 2:
            subprocess.Popen([sys.executable,"form.py"])
            self.menu.setCurrentRow(0)

        else:
            self.pages.setCurrentIndex(index)

    # ---------------- Start Attendance ----------------

    def take_attendance(self):

        subject, ok = QInputDialog.getText(
            self,"Subject","Enter subject name:"
        )

        if not ok or not subject:
            return

        duration, ok = QInputDialog.getInt(
            self,"Duration","Class duration (minutes):",60
        )

        if not ok:
            return

        self.att = AttendanceWindow(subject,duration)
        self.att.show()