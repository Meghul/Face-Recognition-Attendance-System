import sys
import csv
import subprocess
from datetime import date

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFrame,
    QTableWidget, QTableWidgetItem,
    QCalendarWidget, QListWidget, QListWidgetItem,
    QStackedWidget, QInputDialog, QMessageBox, QHeaderView, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from attendance import AttendanceWindow
from student_profile import StudentProfile
from attendance_editor import AttendanceEditor
from analytics import AnalyticsPage
from config import ATTENDANCE_DIR, IMAGES_DIR


# ──────────────────────────────────────────────────────────
# Master stylesheet
# ──────────────────────────────────────────────────────────

STYLE = """
QMainWindow, QWidget {
    background: #0f172a;
    font-family: 'Segoe UI', sans-serif;
}

QLabel { color: white; }

/* ── Sidebar list ─────────────────────── */
QListWidget {
    background: #020617;
    border: none;
    color: #94a3b8;
    font-size: 14px;
}
QListWidget::item {
    padding: 13px 16px;
    border-radius: 8px;
    margin: 2px 0;
}
QListWidget::item:selected {
    background: #1e293b;
    color: white;
}
QListWidget::item:hover {
    background: #0f172a;
    color: white;
}

/* ── Cards ────────────────────────────── */
QFrame#stat_card {
    background: #1e293b;
    border-radius: 12px;
}

/* ── Tables ───────────────────────────── */
QTableWidget {
    background: #020617;
    border: none;
    color: white;
    gridline-color: #1e293b;
    font-size: 13px;
}
QHeaderView::section {
    background: #0f172a;
    color: #94a3b8;
    border: none;
    padding: 8px;
    font-weight: bold;
}

/* ── Buttons ──────────────────────────── */
QPushButton {
    background: #6366f1;
    padding: 11px 18px;
    border-radius: 8px;
    color: white;
    font-weight: bold;
    font-size: 13px;
}
QPushButton:hover  { background: #4f46e5; }
QPushButton:pressed { background: #3730a3; }

/* ── Calendar ─────────────────────────── */
QCalendarWidget QWidget {
    background: #020617;
    color: white;
}
QCalendarWidget QToolButton {
    color: white;
    background: #1e293b;
    font-weight: bold;
    border-radius: 4px;
    padding: 4px 8px;
}
QCalendarWidget QAbstractItemView:enabled {
    background: #020617;
    color: white;
    selection-background-color: #6366f1;
    selection-color: white;
}

/* ── Combo / Input dialogs ────────────── */
QComboBox {
    background: white;
    color: black;
    padding: 4px;
    border-radius: 4px;
}
QComboBox QAbstractItemView {
    background: white;
    color: black;
    selection-background-color: #6366f1;
    selection-color: white;
}
"""


class Dashboard(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Classroom Attendance Monitor")
        self.resize(1350, 820)
        self.setStyleSheet(STYLE)

        container = QWidget()
        self.setCentralWidget(container)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Sidebar ──────────────────────────────────────
        sidebar_widget = QWidget()
        sidebar_widget.setFixedWidth(220)
        sidebar_widget.setStyleSheet("background:#020617;")

        sidebar = QVBoxLayout(sidebar_widget)
        sidebar.setContentsMargins(12, 20, 12, 20)
        sidebar.setSpacing(6)

        logo = QLabel("AI Attendance")
        logo.setStyleSheet("font-size:18px;font-weight:bold;color:#6366f1;padding:0 4px 16px 4px;")
        sidebar.addWidget(logo)

        self.menu = QListWidget()
        self.menu.addItems([
            "  Dashboard",
            "  Take Attendance",
            "  Enroll Student",
            "  Student Profiles",
            "  Attendance Logs",
            "  Analytics",
        ])
        self.menu.setCurrentRow(0)
        self.menu.currentRowChanged.connect(self.switch_page)
        sidebar.addWidget(self.menu)
        sidebar.addStretch()

        main_layout.addWidget(sidebar_widget)

        # ── Pages ─────────────────────────────────────────
        self.pages = QStackedWidget()

        self.dashboard_page = self._build_dashboard()
        self.profiles_page  = self._build_profiles()
        self.logs_page      = self._build_logs()
        self.analytics_page = AnalyticsPage()

        self.pages.addWidget(self.dashboard_page)   # 0
        self.pages.addWidget(QWidget())              # 1 – Take Attendance (handled via dialog)
        self.pages.addWidget(QWidget())              # 2 – Enroll Student  (handled via subprocess)
        self.pages.addWidget(self.profiles_page)    # 3
        self.pages.addWidget(self.logs_page)        # 4
        self.pages.addWidget(self.analytics_page)   # 5

        main_layout.addWidget(self.pages, 1)

        self._load_recent()

        # Auto-refresh stats every 30 seconds
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_dashboard)
        self._refresh_timer.start(30_000)

    # ══════════════════════════════════════════════════════
    # Dashboard page
    # ══════════════════════════════════════════════════════

    def _build_dashboard(self) -> QWidget:
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(18)

        title = QLabel("System Dashboard")
        title.setStyleSheet("font-size:26px;font-weight:bold;")
        layout.addWidget(title)

        # Stat cards
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(14)
        layout.addLayout(self._cards_row)

        self._stat_widgets = {}
        for key, label in [
            ("students", "Total Students"),
            ("today",    "Today's Attendance"),
            ("classes",  "Classes Conducted"),
            ("subject",  "Last Subject"),
        ]:
            card, val_lbl = self._make_stat_card(label, "—")
            self._stat_widgets[key] = val_lbl
            self._cards_row.addWidget(card)

        # Recent activity table
        recent_title = QLabel("Recent Activity — Today")
        recent_title.setStyleSheet("font-size:16px;color:#94a3b8;font-weight:bold;")
        layout.addWidget(recent_title)

        self.recent_table = QTableWidget()
        self.recent_table.setColumnCount(4)
        self.recent_table.setHorizontalHeaderLabels(["Student", "Subject", "Date", "Status"])
        self.recent_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.recent_table.verticalHeader().setVisible(False)
        self.recent_table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.recent_table)

        take_btn = QPushButton("Start Attendance Session")
        take_btn.clicked.connect(self.take_attendance)
        layout.addWidget(take_btn)

        # Load initial values
        self._refresh_dashboard()

        return page

    def _make_stat_card(self, title: str, value: str):
        card = QFrame()
        card.setObjectName("stat_card")
        lay  = QVBoxLayout(card)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)

        t = QLabel(title)
        t.setStyleSheet("color:#94a3b8;font-size:12px;")

        v = QLabel(value)
        v.setStyleSheet("font-size:24px;font-weight:bold;color:white;")

        lay.addWidget(t)
        lay.addWidget(v)
        return card, v

    def _refresh_dashboard(self):
        self._stat_widgets["students"].setText(str(self._count_students()))
        self._stat_widgets["today"].setText(self._today_attendance())
        self._stat_widgets["classes"].setText(str(self._count_classes()))
        self._stat_widgets["subject"].setText(self._last_subject())
        self._load_recent()

    # ── Stat calculations ────────────────────────────────

    def _count_students(self) -> int:
        if IMAGES_DIR.exists():
            return sum(
                1 for f in IMAGES_DIR.iterdir()
                if f.suffix.lower() in (".jpg", ".jpeg", ".png")
            )
        return 0

    def _today_attendance(self) -> str:
        today   = date.today().strftime("%Y-%m-%d")
        present = 0
        total   = self._count_students()
        if ATTENDANCE_DIR.exists():
            for subject in ATTENDANCE_DIR.iterdir():
                fp = subject / f"{today}.csv"
                if fp.exists():
                    with open(fp, newline="", encoding="utf-8") as f:
                        for r in csv.DictReader(f):
                            if r["Status"] == "Present":
                                present += 1
        return f"{present} / {total}"

    def _count_classes(self) -> int:
        total = 0
        if ATTENDANCE_DIR.exists():
            for subject in ATTENDANCE_DIR.iterdir():
                total += len(list(subject.glob("*.csv")))
        return total

    def _last_subject(self) -> str:
        latest_date = None
        latest_subj = "—"
        if ATTENDANCE_DIR.exists():
            for subject in ATTENDANCE_DIR.iterdir():
                for file in subject.glob("*.csv"):
                    d = file.stem
                    if latest_date is None or d > latest_date:
                        latest_date = d
                        latest_subj = subject.name.upper()
        return latest_subj

    def _load_recent(self):
        today = date.today().strftime("%Y-%m-%d")
        rows  = []
        if ATTENDANCE_DIR.exists():
            for subject in ATTENDANCE_DIR.iterdir():
                fp = subject / f"{today}.csv"
                if fp.exists():
                    with open(fp, newline="", encoding="utf-8") as f:
                        for r in csv.DictReader(f):
                            rows.append({
                                "student": r["Student"],
                                "subject": subject.name.upper(),
                                "date":    today,
                                "status":  r["Status"],
                            })

        self.recent_table.setRowCount(len(rows))
        for i, r in enumerate(rows):
            self.recent_table.setRowHeight(i, 34)
            for j, val in enumerate([r["student"], r["subject"], r["date"], r["status"]]):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                if j == 3:
                    if val == "Present":
                        item.setForeground(QColor("#22c55e"))
                        item.setBackground(QColor("#052e16"))
                    else:
                        item.setForeground(QColor("#f87171"))
                        item.setBackground(QColor("#2d0b0b"))
                self.recent_table.setItem(i, j, item)

    # ══════════════════════════════════════════════════════
    # Student Profiles page
    # ══════════════════════════════════════════════════════

    def _build_profiles(self) -> QWidget:
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        title = QLabel("Student Profiles")
        title.setStyleSheet("font-size:26px;font-weight:bold;")
        layout.addWidget(title)

        hint = QLabel("Click a student to open their detailed profile and attendance breakdown.")
        hint.setStyleSheet("color:#64748b;font-size:13px;")
        layout.addWidget(hint)

        self.student_list = QListWidget()
        self.student_list.setStyleSheet("""
            QListWidget { background:#1e293b; border-radius:10px; font-size:14px; }
            QListWidget::item { padding:12px 16px; border-radius:6px; }
            QListWidget::item:hover { background:#334155; color:white; }
            QListWidget::item:selected { background:#6366f1; color:white; }
        """)
        self.student_list.itemClicked.connect(self._open_profile)
        layout.addWidget(self.student_list)

        return page

    def _refresh_profiles(self):
        self.student_list.clear()
        if IMAGES_DIR.exists():
            for f in sorted(IMAGES_DIR.iterdir()):
                if f.suffix.lower() in (".jpg", ".jpeg", ".png"):
                    self.student_list.addItem(f"  {f.stem}")

    def _open_profile(self, item):
        name = item.text().strip()
        self.profile = StudentProfile(name)
        self.profile.show()

    # ══════════════════════════════════════════════════════
    # Attendance Logs page
    # ══════════════════════════════════════════════════════

    def _build_logs(self) -> QWidget:
        page   = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(14)

        # Header row
        hdr_row = QHBoxLayout()
        title = QLabel("Attendance Logs")
        title.setStyleSheet("font-size:26px;font-weight:bold;")
        hdr_row.addWidget(title)
        hdr_row.addStretch()
        layout.addLayout(hdr_row)

        # ── Controls: subject selector + view mode ───────────
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet("""
            QFrame {
                background:#1e293b;
                border-radius:10px;
                border:1px solid #334155;
            }
        """)
        ctrl_lay = QHBoxLayout(ctrl_frame)
        ctrl_lay.setContentsMargins(14, 10, 14, 10)
        ctrl_lay.setSpacing(14)

        subj_lbl = QLabel("SUBJECT")
        subj_lbl.setStyleSheet("color:#64748b;font-size:11px;font-weight:700;letter-spacing:0.8px;")

        self.logs_subject_combo = QComboBox()
        self.logs_subject_combo.setStyleSheet("""
            QComboBox {
                background:#0f172a; color:#e2e8f0;
                border:1px solid #334155; border-radius:8px;
                padding:7px 14px; font-size:13px; min-width:160px;
            }
            QComboBox:hover { border-color:#6366f1; }
            QComboBox::drop-down { border:none; width:22px; }
            QComboBox QAbstractItemView {
                background:#1e293b; color:#e2e8f0;
                selection-background-color:#6366f1;
                border:1px solid #334155;
            }
        """)

        mode_lbl = QLabel("VIEW")
        mode_lbl.setStyleSheet("color:#64748b;font-size:11px;font-weight:700;letter-spacing:0.8px;")

        self.logs_mode_combo = QComboBox()
        self.logs_mode_combo.addItems(["By Date (Selected Day)", "Overall Summary"])
        self.logs_mode_combo.setStyleSheet(self.logs_subject_combo.styleSheet())

        ctrl_lay.addWidget(subj_lbl)
        ctrl_lay.addWidget(self.logs_subject_combo)
        ctrl_lay.addSpacing(8)
        ctrl_lay.addWidget(mode_lbl)
        ctrl_lay.addWidget(self.logs_mode_combo)
        ctrl_lay.addStretch()

        edit_btn = QPushButton("Edit Selected Day")
        edit_btn.setStyleSheet("""
            QPushButton {
                background:#0f172a; border:1px solid #334155;
                padding:8px 16px; border-radius:8px;
                font-size:13px; color:#e2e8f0; font-weight:600;
            }
            QPushButton:hover { background:#1e293b; border-color:#6366f1; }
        """)
        edit_btn.clicked.connect(self._edit_attendance)
        ctrl_lay.addWidget(edit_btn)

        layout.addWidget(ctrl_frame)

        # ── Body: calendar + table ────────────────────────────
        body = QHBoxLayout()
        body.setSpacing(16)

        # Calendar column
        cal_col = QVBoxLayout()
        cal_col.setSpacing(8)

        cal_hint = QLabel("Select a date:")
        cal_hint.setStyleSheet("color:#64748b;font-size:12px;font-weight:600;")

        self.calendar = QCalendarWidget()
        self.calendar.setFixedSize(310, 265)
        self.calendar.setStyleSheet("""
            QCalendarWidget QWidget { background:#020617; color:white; }
            QCalendarWidget QToolButton {
                color:white; background:#1e293b;
                font-weight:bold; border-radius:4px; padding:4px 8px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                background:#020617; color:white;
                selection-background-color:#6366f1;
                selection-color:white;
            }
        """)

        # Date indicator label
        self.date_info_lbl = QLabel()
        self.date_info_lbl.setStyleSheet("color:#818cf8;font-size:12px;font-weight:600;")
        self._update_date_label()

        cal_col.addWidget(cal_hint)
        cal_col.addWidget(self.calendar)
        cal_col.addWidget(self.date_info_lbl)
        cal_col.addStretch()
        body.addLayout(cal_col)

        # Logs table
        table_col = QVBoxLayout()
        table_col.setSpacing(6)

        self.logs_info_lbl = QLabel("Select a subject and date to view attendance.")
        self.logs_info_lbl.setStyleSheet("color:#64748b;font-size:12px;")
        table_col.addWidget(self.logs_info_lbl)

        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(3)
        self.logs_table.setHorizontalHeaderLabels(["Student", "Subject", "Status"])
        self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setStyleSheet("""
            QTableWidget { alternate-background-color:#0a1628; }
        """)
        table_col.addWidget(self.logs_table)
        body.addLayout(table_col, 1)

        layout.addLayout(body)

        # ── Wire signals ─────────────────────────────────────
        self.calendar.clicked.connect(self._on_log_date_changed)
        self.logs_subject_combo.currentIndexChanged.connect(self._load_logs)
        self.logs_mode_combo.currentIndexChanged.connect(self._load_logs)

        return page

    def _update_date_label(self):
        d = self.calendar.selectedDate().toString("yyyy-MM-dd")
        self.date_info_lbl.setText(f"Selected: {d}")

    def _on_log_date_changed(self, qdate):
        self._update_date_label()
        self._load_logs()

    def _refresh_logs_subjects(self):
        """Reload subject combo in Logs page without firing signals."""
        self.logs_subject_combo.blockSignals(True)
        prev = self.logs_subject_combo.currentText()
        self.logs_subject_combo.clear()
        if ATTENDANCE_DIR.exists():
            subjects = sorted(p.name for p in ATTENDANCE_DIR.iterdir() if p.is_dir())
            self.logs_subject_combo.addItems(subjects)
            idx = self.logs_subject_combo.findText(prev)
            if idx >= 0:
                self.logs_subject_combo.setCurrentIndex(idx)
        self.logs_subject_combo.blockSignals(False)

    def _load_logs(self, _=None):
        """
        Load attendance for the SELECTED DATE + SELECTED SUBJECT.
        In 'By Date' mode  → shows Student | Subject | Present/Absent for that single day.
        In 'Overall' mode  → shows Student | Subject | Overall % across all days.
        """
        self._refresh_logs_subjects()
        subject = self.logs_subject_combo.currentText()
        if not subject or not ATTENDANCE_DIR.exists():
            self.logs_info_lbl.setText("No subjects found. Take attendance first.")
            self.logs_table.setRowCount(0)
            return

        mode = self.logs_mode_combo.currentText()
        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        subject_path  = ATTENDANCE_DIR / subject

        if "By Date" in mode:
            # ── DATE-SPECIFIC view ───────────────────────────
            self.logs_table.setColumnCount(3)
            self.logs_table.setHorizontalHeaderLabels(["Student", "Subject", "Status"])
            self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            file_path = subject_path / f"{selected_date}.csv"
            if not file_path.exists():
                self.logs_info_lbl.setText(
                    f"No attendance record for {subject.upper()} on {selected_date}."
                )
                self.logs_table.setRowCount(0)
                return

            rows = []
            with open(file_path, newline="", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    rows.append((r["Student"].strip(), subject.upper(), r["Status"].strip()))

            self.logs_info_lbl.setText(
                f"Showing {len(rows)} student(s) for {subject.upper()} on {selected_date}."
            )
            self.logs_table.setRowCount(len(rows))
            for i, (student, subj, status) in enumerate(rows):
                self.logs_table.setRowHeight(i, 34)
                is_present = (status == "Present")
                bg = QColor("#052e16") if is_present else QColor("#2d0b0b")
                fg = QColor("#4ade80") if is_present else QColor("#f87171")

                for j, val in enumerate([student, subj, status]):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    if j == 2:
                        item.setBackground(bg)
                        item.setForeground(fg)
                    self.logs_table.setItem(i, j, item)

        else:
            # ── OVERALL SUMMARY view ─────────────────────────
            self.logs_table.setColumnCount(5)
            self.logs_table.setHorizontalHeaderLabels([
                "Student", "Subject", "Attended", "Total", "Attendance %"
            ])
            self.logs_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

            files         = list(subject_path.glob("*.csv"))
            total_classes = len(files)
            students      = {}

            for file in files:
                with open(file, newline="", encoding="utf-8") as f:
                    for r in csv.DictReader(f):
                        name = r["Student"].strip()
                        if name not in students:
                            students[name] = 0
                        if r["Status"] == "Present":
                            students[name] += 1

            rows = []
            for student, attended in students.items():
                pct = int(attended / total_classes * 100) if total_classes else 0
                rows.append((student, subject.upper(), attended, total_classes, pct))

            self.logs_info_lbl.setText(
                f"Overall summary for {subject.upper()} — {total_classes} class(es) recorded."
            )
            self.logs_table.setRowCount(len(rows))
            for i, (student, subj, attended, total, pct) in enumerate(rows):
                self.logs_table.setRowHeight(i, 34)
                if pct >= 75:
                    bg, fg = QColor("#052e16"), QColor("#4ade80")
                elif pct >= 50:
                    bg, fg = QColor("#422006"), QColor("#fbbf24")
                else:
                    bg, fg = QColor("#2d0b0b"), QColor("#f87171")

                vals = [student, subj, str(attended), str(total), f"{pct}%"]
                for j, val in enumerate(vals):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(Qt.AlignCenter)
                    if j >= 4:
                        item.setBackground(bg)
                        item.setForeground(fg)
                    self.logs_table.setItem(i, j, item)

    def _edit_attendance(self):
        if not ATTENDANCE_DIR.exists():
            return
        subject = self.logs_subject_combo.currentText()
        if not subject:
            QMessageBox.information(self, "Info", "Please select a subject first.")
            return

        selected_date = self.calendar.selectedDate().toString("yyyy-MM-dd")
        file_path     = ATTENDANCE_DIR / subject / f"{selected_date}.csv"

        if not file_path.exists():
            QMessageBox.warning(
                self, "Not Found",
                f"No attendance record for {subject.upper()} on {selected_date}.\n"
                "Attendance can only be edited for dates where a session was recorded."
            )
            return

        self.editor = AttendanceEditor(file_path)
        self.editor.show()

    # ══════════════════════════════════════════════════════
    # Navigation
    # ══════════════════════════════════════════════════════

    def switch_page(self, index: int):
        if index == 1:
            self.menu.setCurrentRow(0)
            self.take_attendance()
        elif index == 2:
            self.menu.setCurrentRow(0)
            subprocess.Popen([sys.executable, "form.py"])
        elif index == 3:
            self._refresh_profiles()
            self.pages.setCurrentIndex(3)
        elif index == 4:
            self._refresh_logs_subjects()
            self._load_logs()
            self.pages.setCurrentIndex(4)
        elif index == 5:
            self.analytics_page.refresh()
            self.pages.setCurrentIndex(5)
        else:
            self.pages.setCurrentIndex(index)

    # ══════════════════════════════════════════════════════
    # Take attendance
    # ══════════════════════════════════════════════════════

    def take_attendance(self):
        subject, ok = QInputDialog.getText(
            self, "Subject Name", "Enter subject name:"
        )
        if not ok or not subject.strip():
            return

        duration, ok = QInputDialog.getInt(
            self, "Class Duration", "Duration in minutes:", 60, 1, 300
        )
        if not ok:
            return

        self.att = AttendanceWindow(subject.strip(), duration)
        self.att.show()
        self.menu.setCurrentRow(0)
