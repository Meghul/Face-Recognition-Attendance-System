import cv2
import face_recognition
import numpy as np
import time
import csv

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QMessageBox, QFrame
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap, QColor, QFont

from config import IMAGES_DIR, attendance_file, normalize_subject


# -----------------------------
# Encode faces (called on demand, not at import)
# -----------------------------

def load_known_faces():
    """Load and encode all student face images from ImagesAttendance/."""
    images     = []
    classNames = []

    if not IMAGES_DIR.exists():
        return [], []

    for file in IMAGES_DIR.iterdir():
        if file.suffix.lower() not in (".jpg", ".jpeg", ".png"):
            continue
        img = cv2.imread(str(file))
        if img is None:
            continue
        images.append(img)
        classNames.append(file.stem.strip())

    encode_list = []
    for img in images:
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        enc = face_recognition.face_encodings(rgb)
        if enc:
            encode_list.append(enc[0])
        else:
            # Still keep a None placeholder so classNames index stays aligned
            encode_list.append(None)

    # Filter out any None encodings
    paired = [(e, n) for e, n in zip(encode_list, classNames) if e is not None]
    if paired:
        encode_list, classNames = zip(*paired)
        return list(encode_list), list(classNames)
    return [], []


# -----------------------------
# Save attendance session
# -----------------------------

def save_session(subject, presence_time, duration):
    """
    Write a CSV of Present/Absent for all enrolled students.
    A student is Present if they were detected for >= 50% of class duration.
    """
    subject    = normalize_subject(subject)
    today      = datetime.now().strftime("%Y-%m-%d")
    file_path  = attendance_file(subject, today)

    half_time = duration / 2
    present_students = {
        name for name, secs in presence_time.items() if secs >= half_time
    }

    students = [
        f.stem.strip()
        for f in IMAGES_DIR.iterdir()
        if f.suffix.lower() in (".jpg", ".jpeg", ".png")
    ]

    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Student", "Status"])
        for s in students:
            status = "Present" if s in present_students else "Absent"
            writer.writerow([s, status])

    print(f"Session saved → {file_path}")
    return file_path


# ============================================================
# Attendance Window
# ============================================================

DARK_STYLE = """
QWidget {
    background: #0f172a;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}
QLabel {
    color: white;
}
QListWidget {
    background: #020617;
    border: none;
    color: #94a3b8;
    font-size: 13px;
}
QListWidget::item {
    padding: 8px 10px;
    border-radius: 6px;
}
QFrame {
    background: #1e293b;
    border-radius: 10px;
}
"""


class AttendanceWindow(QWidget):

    def __init__(self, subject, duration_minutes):
        super().__init__()

        self.subject       = normalize_subject(subject)
        self.duration      = duration_minutes * 60          # seconds
        self.session_start = time.time()
        self.last_update   = time.time()
        self.presence_time = {}
        self.session_saved = False

        self.setWindowTitle(f"Live Attendance — {subject.upper()}")
        self.resize(1150, 640)
        self.setStyleSheet(DARK_STYLE)

        # ---------------- Load encodings ----------------
        self.encode_list, self.class_names = load_known_faces()
        print(f"Loaded {len(self.class_names)} students: {self.class_names}")

        # ---------------- Layout ----------------
        root = QHBoxLayout()
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(12)

        # --- Video ---
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background:#000;border-radius:8px;")
        root.addWidget(self.video_label, 3)

        # --- Side panel ---
        side_frame = QFrame()
        side_layout = QVBoxLayout(side_frame)
        side_layout.setContentsMargins(12, 14, 12, 14)
        side_layout.setSpacing(10)

        subject_lbl = QLabel(f"Subject: {subject.upper()}")
        subject_lbl.setStyleSheet("font-size:15px;font-weight:bold;color:#6366f1;")

        # Countdown label
        self.countdown_lbl = QLabel()
        self.countdown_lbl.setStyleSheet("font-size:13px;color:#94a3b8;")
        self._refresh_countdown()

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background:#334155;max-height:1px;")

        panel_title = QLabel("Students Detected")
        panel_title.setStyleSheet("font-size:13px;color:#64748b;font-weight:bold;")

        self.student_list = QListWidget()
        self.student_list.setStyleSheet("""
            QListWidget { background:#020617; border-radius:8px; }
            QListWidget::item { padding:10px; border-radius:6px; }
        """)

        side_layout.addWidget(subject_lbl)
        side_layout.addWidget(self.countdown_lbl)
        side_layout.addWidget(div)
        side_layout.addWidget(panel_title)
        side_layout.addWidget(self.student_list)

        root.addWidget(side_frame, 1)
        self.setLayout(root)

        # ---------------- Camera ----------------
        self.cap = cv2.VideoCapture(0)

        # Frame timer (30 ms ≈ 33 fps)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

        # Countdown refresh every second
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self._refresh_countdown)
        self.clock_timer.start(1000)

    # --------------------------------------------------------
    # Countdown helper
    # --------------------------------------------------------

    def _refresh_countdown(self):
        elapsed   = time.time() - self.session_start
        remaining = max(0, self.duration - elapsed)
        mins      = int(remaining // 60)
        secs      = int(remaining % 60)
        self.countdown_lbl.setText(f"Time remaining: {mins:02d}:{secs:02d}")

    # --------------------------------------------------------
    # Frame update
    # --------------------------------------------------------

    def update_frame(self):
        elapsed = time.time() - self.session_start

        # Auto-end when duration reached
        if elapsed >= self.duration:
            self.timer.stop()
            self.clock_timer.stop()
            if self.cap.isOpened():
                self.cap.release()
            self._do_save()
            QMessageBox.information(self, "Class Ended", "Session complete. Attendance saved.")
            self.close()
            return

        ret, frame = self.cap.read()
        if not ret:
            return

        frame = self.process_frame(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.video_label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.video_label.width(),
                self.video_label.height(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    # --------------------------------------------------------
    # Face detection
    # --------------------------------------------------------

    def process_frame(self, frame):
        if not self.encode_list:
            return frame

        small     = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        faces     = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small, faces)

        now   = time.time()
        delta = now - self.last_update
        self.last_update = now

        for enc_face, face_loc in zip(encodings, faces):
            matches   = face_recognition.compare_faces(self.encode_list, enc_face)
            distances = face_recognition.face_distance(self.encode_list, enc_face)
            idx       = int(np.argmin(distances))

            if matches[idx]:
                name = self.class_names[idx]
                self.presence_time[name] = self.presence_time.get(name, 0) + delta

                y1, x2, y2, x1 = face_loc
                y1 *= 4; x2 *= 4; y2 *= 4; x1 *= 4

                # Colour box: green if already qualifies, yellow if pending
                half_time = self.duration / 2
                qualified = self.presence_time[name] >= half_time
                color     = (0, 220, 80) if qualified else (255, 200, 0)

                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(
                    frame, name,
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.85,
                    color, 2
                )

        self._update_panel()
        return frame

    # --------------------------------------------------------
    # Side panel
    # --------------------------------------------------------

    def _update_panel(self):
        self.student_list.clear()
        half_time = self.duration / 2

        for name, seconds in self.presence_time.items():
            mins      = int(seconds // 60)
            secs_rem  = int(seconds % 60)
            qualified = seconds >= half_time

            badge  = "✔ Present" if qualified else "⏳ Pending"
            text   = f"{name}   {mins}m {secs_rem:02d}s   {badge}"

            item = QListWidgetItem(text)
            item.setForeground(
                QColor("#22c55e") if qualified else QColor("#f59e0b")
            )
            self.student_list.addItem(item)

    # --------------------------------------------------------
    # Save helper
    # --------------------------------------------------------

    def _do_save(self):
        if not self.session_saved:
            save_session(self.subject, self.presence_time, self.duration)
            self.session_saved = True

    # --------------------------------------------------------
    # Close event — ask before discarding data
    # --------------------------------------------------------

    def closeEvent(self, event):
        self.timer.stop()
        self.clock_timer.stop()

        if self.cap.isOpened():
            self.cap.release()

        if not self.session_saved and self.presence_time:
            reply = QMessageBox.question(
                self,
                "Save Attendance?",
                "Class ended early. Save attendance for students detected so far?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self._do_save()

        event.accept()
