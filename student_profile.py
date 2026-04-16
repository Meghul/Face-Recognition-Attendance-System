import csv
from pathlib import Path
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHeaderView

from config import ATTENDANCE_DIR, IMAGES_DIR


class StudentProfile(QWidget):

    def __init__(self, student):
        super().__init__()

        self.student = student

        self.setWindowTitle(f"{student} - Profile")
        self.resize(700,500)

        self.setStyleSheet("""
        QWidget{
            background:#0f172a;
            color:white;
        }

        QLabel{
            color:white;
        }

        QTableWidget{
            background:#020617;
            color:white;
            border:none;
        }

        QHeaderView::section{
            background:#1e293b;
            color:white;
            border:none;
            padding:6px;
        }
        """)

        main_layout = QVBoxLayout()

        # ---------------- Top Profile Section ----------------

        top_layout = QHBoxLayout()

        # Photo

        self.photo = QLabel()

        photo_path = IMAGES_DIR / f"{student}.jpg"

        if photo_path.exists():

            pix = QPixmap(str(photo_path))
            pix = pix.scaled(150,150, Qt.KeepAspectRatio)

            self.photo.setPixmap(pix)

        else:

            self.photo.setText("No Photo")

        top_layout.addWidget(self.photo)

        # Info Section

        info_layout = QVBoxLayout()

        name_label = QLabel(f"Name: {student}")
        name_label.setStyleSheet("font-size:20px;font-weight:bold")

        self.attendance_label = QLabel("Attendance: calculating...")

        self.last_seen_label = QLabel("Last Seen: calculating...")

        info_layout.addWidget(name_label)
        info_layout.addWidget(self.attendance_label)
        info_layout.addWidget(self.last_seen_label)

        top_layout.addLayout(info_layout)

        main_layout.addLayout(top_layout)

        # ---------------- Subject Table ----------------

        self.table = QTableWidget()

        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Subject",
            "Classes Attended",
            "Total Classes",
            "Attendance %"
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        main_layout.addWidget(self.table)

        self.setLayout(main_layout)

        # Load analytics

        self.load_student_data()

    # ---------------- Load Student Analytics ----------------

    def load_student_data(self):

        subjects = [p.name for p in ATTENDANCE_DIR.iterdir()]

        subject_stats = []

        total_attended = 0
        total_classes = 0

        last_seen = None

        for subject in subjects:

            subject_path = ATTENDANCE_DIR / subject

            files = list(subject_path.glob("*.csv"))

            attended = 0

            for file in files:

                with open(file) as f:

                    reader = csv.DictReader(f)

                    for r in reader:

                        if r["Student"].strip() == self.student:

                            if r["Status"] == "Present":

                                attended += 1

                                file_date = file.stem

                                if last_seen is None:
                                    last_seen = file_date

                                else:
                                    if file_date > last_seen:
                                        last_seen = file_date

            total = len(files)

            if total > 0:

                percent = int((attended / total) * 100)

                subject_stats.append((subject, attended, total, f"{percent}%"))

                total_attended += attended
                total_classes += total

        # Overall attendance

        if total_classes > 0:

            overall_percent = int((total_attended / total_classes) * 100)

            self.attendance_label.setText(
                f"Overall Attendance: {overall_percent}%"
            )

        else:

            self.attendance_label.setText("Overall Attendance: N/A")

        # Last seen

        if last_seen:

            self.last_seen_label.setText(f"Last Seen: {last_seen}")

        else:

            self.last_seen_label.setText("Last Seen: Never")

        # Fill table

        self.table.setRowCount(len(subject_stats))

        for i,row in enumerate(subject_stats):

            for j,val in enumerate(row):

                self.table.setItem(i,j,QTableWidgetItem(str(val)))