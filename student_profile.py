import csv
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QFrame,
    QProgressBar, QHeaderView
)
from PySide6.QtGui import QPixmap, QColor, QPainter, QBrush, QPen
from PySide6.QtCore import Qt, QSize

from config import ATTENDANCE_DIR, IMAGES_DIR


STYLE = """
QWidget {
    background: #0f172a;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

QLabel { color: white; }

QFrame#profile_card {
    background: #1e293b;
    border-radius: 12px;
}

QTableWidget {
    background: #020617;
    color: white;
    border: none;
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

QProgressBar {
    background: #0f172a;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    font-size: 11px;
    color: white;
}

QProgressBar::chunk {
    border-radius: 5px;
}
"""


def _round_pixmap(pixmap: QPixmap, size: int) -> QPixmap:
    """Crop and round a pixmap into a circle of `size` px."""
    scaled = pixmap.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
    output = QPixmap(size, size)
    output.fill(Qt.transparent)

    painter = QPainter(output)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(scaled))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(0, 0, size, size)

    # Border ring
    painter.setPen(QPen(QColor("#6366f1"), 3))
    painter.setBrush(Qt.NoBrush)
    painter.drawEllipse(1, 1, size - 2, size - 2)

    painter.end()
    return output


class StudentProfile(QWidget):

    def __init__(self, student: str):
        super().__init__()

        self.student = student
        self.setWindowTitle(f"{student} — Profile")
        self.resize(720, 540)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        # ── Profile card ─────────────────────────────────
        card = QFrame()
        card.setObjectName("profile_card")
        card_lay = QHBoxLayout(card)
        card_lay.setContentsMargins(20, 18, 20, 18)
        card_lay.setSpacing(24)

        # Photo
        photo_lbl = QLabel()
        photo_path = IMAGES_DIR / f"{student}.jpg"

        if photo_path.exists():
            pix     = QPixmap(str(photo_path))
            rounded = _round_pixmap(pix, 110)
            photo_lbl.setPixmap(rounded)
        else:
            photo_lbl.setText("No\nPhoto")
            photo_lbl.setAlignment(Qt.AlignCenter)
            photo_lbl.setFixedSize(110, 110)
            photo_lbl.setStyleSheet(
                "background:#334155;border-radius:55px;"
                "color:#64748b;font-size:12px;"
            )

        photo_lbl.setFixedSize(110, 110)
        card_lay.addWidget(photo_lbl)

        # Info block
        info_lay = QVBoxLayout()
        info_lay.setSpacing(8)

        name_lbl = QLabel(student)
        name_lbl.setStyleSheet("font-size:22px;font-weight:bold;color:white;")

        self.overall_lbl = QLabel("Calculating overall attendance…")
        self.overall_lbl.setStyleSheet("font-size:13px;color:#94a3b8;")

        self.last_seen_lbl = QLabel("Last seen: —")
        self.last_seen_lbl.setStyleSheet("font-size:13px;color:#94a3b8;")

        # Progress bar
        bar_row = QHBoxLayout()
        bar_row.setSpacing(10)

        bar_lbl = QLabel("Overall:")
        bar_lbl.setStyleSheet("font-size:12px;color:#64748b;")
        bar_lbl.setFixedWidth(56)

        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        self.pct_lbl = QLabel("0%")
        self.pct_lbl.setStyleSheet("font-size:12px;color:#94a3b8;min-width:36px;")

        bar_row.addWidget(bar_lbl)
        bar_row.addWidget(self.progress, 1)
        bar_row.addWidget(self.pct_lbl)

        info_lay.addWidget(name_lbl)
        info_lay.addWidget(self.overall_lbl)
        info_lay.addWidget(self.last_seen_lbl)
        info_lay.addLayout(bar_row)
        card_lay.addLayout(info_lay, 1)

        root.addWidget(card)

        # ── Subject breakdown table ───────────────────────
        table_title = QLabel("Subject Breakdown")
        table_title.setStyleSheet("font-size:15px;font-weight:bold;color:#94a3b8;")
        root.addWidget(table_title)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Subject", "Attended", "Total", "Attendance %"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        root.addWidget(self.table)

        self._load_data()

    # ──────────────────────────────────────────────────────
    # Data loading
    # ──────────────────────────────────────────────────────

    def _load_data(self):
        if not ATTENDANCE_DIR.exists():
            return

        subject_stats  = []
        total_attended = 0
        total_classes  = 0
        last_seen      = None

        for subject_dir in sorted(ATTENDANCE_DIR.iterdir()):
            if not subject_dir.is_dir():
                continue

            files    = list(subject_dir.glob("*.csv"))
            attended = 0

            for file in files:
                with open(file, newline="", encoding="utf-8") as f:
                    for row in csv.DictReader(f):
                        if row["Student"].strip() == self.student:
                            if row["Status"].strip() == "Present":
                                attended += 1
                                d = file.stem
                                if last_seen is None or d > last_seen:
                                    last_seen = d

            total = len(files)
            if total > 0:
                pct = int(attended / total * 100)
                subject_stats.append((subject_dir.name, attended, total, pct))
                total_attended += attended
                total_classes  += total

        # Overall %
        if total_classes > 0:
            overall_pct = int(total_attended / total_classes * 100)
        else:
            overall_pct = 0

        colour = "#22c55e" if overall_pct >= 75 else ("#f59e0b" if overall_pct >= 50 else "#ef4444")
        self.overall_lbl.setText(
            f"Overall Attendance: <span style='color:{colour};font-weight:bold;'>"
            f"{total_attended}/{total_classes}</span>"
        )
        self.last_seen_lbl.setText(f"Last seen: {last_seen or 'Never'}")

        self.progress.setValue(overall_pct)
        self.progress.setStyleSheet(
            f"QProgressBar::chunk {{ background:{colour};border-radius:5px; }}"
        )
        self.pct_lbl.setText(f"{overall_pct}%")
        self.pct_lbl.setStyleSheet(f"font-size:12px;color:{colour};min-width:36px;")

        # Table
        self.table.setRowCount(len(subject_stats))

        for i, (subj, attended, total, pct) in enumerate(subject_stats):
            self.table.setRowHeight(i, 36)

            colour_row = (
                QColor("#052e16") if pct >= 75
                else (QColor("#422006") if pct >= 50 else QColor("#2d0b0b"))
            )
            fg_colour = (
                QColor("#4ade80") if pct >= 75
                else (QColor("#fbbf24") if pct >= 50 else QColor("#f87171"))
            )

            values = [subj.upper(), str(attended), str(total), f"{pct}%"]
            for j, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(colour_row)
                item.setForeground(fg_colour)
                self.table.setItem(i, j, item)
