import cv2
import face_recognition
import numpy as np
import time
import csv

from datetime import datetime
from pathlib import Path

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QListWidget
from PySide6.QtCore import QTimer
from PySide6.QtGui import QImage, QPixmap

from config import IMAGES_DIR, attendance_file, normalize_subject


# -----------------------------
# Load student images
# -----------------------------

images = []
classNames = []

for file in IMAGES_DIR.iterdir():

    img = cv2.imread(str(file))

    if img is None:
        continue

    images.append(img)
    classNames.append(file.stem.strip())

print("Students loaded:", classNames)


# -----------------------------
# Encode faces
# -----------------------------

def findEncodings(images):

    encodeList = []

    for img in images:

        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        enc = face_recognition.face_encodings(rgb)

        if enc:
            encodeList.append(enc[0])

    return encodeList


encodeListKnown = findEncodings(images)

print("Encodings:", len(encodeListKnown))


# -----------------------------
# Save attendance session
# -----------------------------

def save_session(subject, present_students):

    subject = normalize_subject(subject)

    today = datetime.now().strftime("%Y-%m-%d")

    file_path = attendance_file(subject, today)

    students = [f.stem.strip() for f in IMAGES_DIR.iterdir()]

    with open(file_path, "w", newline="", encoding="utf-8") as f:

        writer = csv.writer(f)

        writer.writerow(["Student", "Status"])

        for s in students:

            status = "Present" if s in present_students else "Absent"

            writer.writerow([s, status])

    print("Session saved:", file_path)


# -----------------------------
# Attendance Window
# -----------------------------

class AttendanceWindow(QWidget):

    def __init__(self, subject, duration):

        super().__init__()

        self.subject = normalize_subject(subject)

        # minutes → seconds
        self.duration = duration * 60

        self.session_start = time.time()

        self.setWindowTitle("Live Attendance Monitoring")
        self.resize(1100,600)

        main_layout = QHBoxLayout()

        # ---------------- VIDEO PANEL ----------------

        self.video_label = QLabel()
        main_layout.addWidget(self.video_label,3)

        # ---------------- SIDE PANEL ----------------

        side_layout = QVBoxLayout()

        title = QLabel("Live Attendance")
        title.setStyleSheet("font-size:18px;font-weight:bold")

        self.student_list = QListWidget()

        side_layout.addWidget(title)
        side_layout.addWidget(self.student_list)

        main_layout.addLayout(side_layout,1)

        self.setLayout(main_layout)

        # ---------------- CAMERA ----------------

        self.cap = cv2.VideoCapture(0)

        # presence tracking
        self.presence_time = {}

        # time delta tracking
        self.last_update = time.time()

        # update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)


    # ---------------- Frame Update ----------------

    def update_frame(self):

        elapsed = time.time() - self.session_start

        # Stop session if duration reached
        if elapsed >= self.duration:

            print("Class ended")

            self.timer.stop()

            if self.cap.isOpened():
                self.cap.release()

            # Determine present students
            half_time = self.duration / 2

            present_students = []

            for name, seconds in self.presence_time.items():

                if seconds >= half_time:
                    present_students.append(name)

            save_session(self.subject, present_students)

            self.close()
            return


        ret, frame = self.cap.read()

        if not ret:
            return

        frame = self.process_frame(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        h, w, ch = rgb.shape
        bytes_per_line = ch * w

        img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)

        self.video_label.setPixmap(QPixmap.fromImage(img))


    # ---------------- Face Detection ----------------

    def process_frame(self, frame):

        small = cv2.resize(frame,(0,0),None,0.25,0.25)

        rgb_small = cv2.cvtColor(small,cv2.COLOR_BGR2RGB)

        faces = face_recognition.face_locations(rgb_small)
        encodings = face_recognition.face_encodings(rgb_small,faces)

        now = time.time()
        delta = now - self.last_update
        self.last_update = now

        for encodeFace, faceLoc in zip(encodings,faces):

            matches = face_recognition.compare_faces(
                encodeListKnown, encodeFace
            )

            distances = face_recognition.face_distance(
                encodeListKnown, encodeFace
            )

            matchIndex = np.argmin(distances)

            if matches[matchIndex]:

                name = classNames[matchIndex]

                # initialize student timer
                if name not in self.presence_time:
                    self.presence_time[name] = 0

                # add time seen
                self.presence_time[name] += delta

                y1,x2,y2,x1 = faceLoc

                y1 *= 4
                x2 *= 4
                y2 *= 4
                x1 *= 4

                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),2)

                cv2.putText(
                    frame,
                    name,
                    (x1,y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.9,
                    (255,255,255),
                    2
                )

        self.update_panel()

        return frame


    # ---------------- Side Panel ----------------

    def update_panel(self):

        self.student_list.clear()

        for name, seconds in self.presence_time.items():

            minutes = round(seconds / 60, 2)

            self.student_list.addItem(f"{name}  -  {minutes} min")


    # ---------------- Close Event ----------------

    def closeEvent(self,event):

        if self.cap.isOpened():
            self.cap.release()

        event.accept()