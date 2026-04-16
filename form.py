import sys
import csv
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QFileDialog, QVBoxLayout,
    QMessageBox
)

from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "ImagesAttendance"
STUDENT_FILE = BASE_DIR / "StudentList" / "students.csv"


class StudentForm(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Student Enrollment")
        self.resize(420,520)

        self.setStyleSheet("""

        QWidget{
            background-color:#0f172a;
            color:white;
        }

        QLineEdit{
            padding:10px;
            border-radius:6px;
            border:1px solid #334155;
            background-color:#1e293b;
            color:white;
        }

        QPushButton{
            background-color:#2563eb;
            padding:10px;
            border-radius:6px;
            color:white;
        }

        QPushButton:hover{
            background-color:#1d4ed8;
        }

        QLabel{
            font-size:14px;
        }
        """)

        layout = QVBoxLayout()

        title = QLabel("Register Student")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:22px;font-weight:bold")

        layout.addWidget(title)

        self.enrollment = QLineEdit()
        self.enrollment.setPlaceholderText("Enrollment Number")

        self.name = QLineEdit()
        self.name.setPlaceholderText("Student Name")

        self.father = QLineEdit()
        self.father.setPlaceholderText("Father Name")

        self.email = QLineEdit()
        self.email.setPlaceholderText("Email")

        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Phone")

        layout.addWidget(self.enrollment)
        layout.addWidget(self.name)
        layout.addWidget(self.father)
        layout.addWidget(self.email)
        layout.addWidget(self.phone)

        self.photo_preview = QLabel("No Photo Selected")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setFixedHeight(120)

        layout.addWidget(self.photo_preview)

        upload_btn = QPushButton("Upload Photo")
        upload_btn.clicked.connect(self.upload_photo)

        save_btn = QPushButton("Save Student")
        save_btn.clicked.connect(self.save_student)

        layout.addWidget(upload_btn)
        layout.addWidget(save_btn)

        self.setLayout(layout)

        self.photo_path = None

    def upload_photo(self):

        file,_ = QFileDialog.getOpenFileName(
            self,
            "Select Photo",
            "",
            "Images (*.png *.jpg *.jpeg)"
        )

        if file:

            self.photo_path = file

            pix = QPixmap(file)
            pix = pix.scaled(120,120, Qt.KeepAspectRatio)

            self.photo_preview.setPixmap(pix)

    def save_student(self):

        name = self.name.text()

        if not name:
            QMessageBox.warning(self,"Error","Enter student name")
            return

        if not self.photo_path:
            QMessageBox.warning(self,"Error","Upload student photo")
            return

        IMAGES_DIR.mkdir(exist_ok=True)

        shutil.copy(self.photo_path, IMAGES_DIR / f"{name}.jpg")

        QMessageBox.information(self,"Success","Student Registered")

        self.close()


if __name__ == "__main__":

    app = QApplication(sys.argv)

    window = StudentForm()
    window.show()

    sys.exit(app.exec())