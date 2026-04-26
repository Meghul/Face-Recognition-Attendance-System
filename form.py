import sys
import csv
import shutil
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit,
    QPushButton, QFileDialog, QVBoxLayout, QHBoxLayout,
    QMessageBox, QFrame
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

BASE_DIR     = Path(__file__).parent
IMAGES_DIR   = BASE_DIR / "ImagesAttendance"
STUDENT_DIR  = BASE_DIR / "StudentList"
STUDENT_FILE = STUDENT_DIR / "students.csv"

STUDENT_HEADER = ["Enrollment_No", "Name", "Father_Name", "Email", "Contact"]


def _ensure_student_csv():
    """Create StudentList folder and CSV header if not present."""
    STUDENT_DIR.mkdir(exist_ok=True)
    if not STUDENT_FILE.exists():
        with open(STUDENT_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(STUDENT_HEADER)


def _enrollment_exists(enrollment_no: str) -> bool:
    """Return True if this enrollment number is already registered."""
    if not STUDENT_FILE.exists():
        return False
    with open(STUDENT_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("Enrollment_No", "").strip() == enrollment_no.strip():
                return True
    return False


STYLE = """
QWidget {
    background-color: #0f172a;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

QLineEdit {
    padding: 11px 14px;
    border-radius: 8px;
    border: 1px solid #334155;
    background-color: #1e293b;
    color: white;
    font-size: 14px;
}

QLineEdit:focus {
    border: 1px solid #6366f1;
}

QPushButton {
    padding: 11px;
    border-radius: 8px;
    color: white;
    font-size: 14px;
    font-weight: bold;
}

QPushButton#upload_btn {
    background-color: #1e293b;
    border: 1px solid #334155;
}

QPushButton#upload_btn:hover {
    background-color: #334155;
}

QPushButton#save_btn {
    background-color: #6366f1;
}

QPushButton#save_btn:hover {
    background-color: #4f46e5;
}

QLabel {
    font-size: 13px;
    color: #94a3b8;
}

QLabel#title {
    font-size: 22px;
    font-weight: bold;
    color: white;
}

QLabel#photo_box {
    background: #1e293b;
    border: 1px dashed #334155;
    border-radius: 10px;
    color: #64748b;
    font-size: 13px;
}
"""


class StudentForm(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Enroll New Student")
        self.setFixedSize(440, 580)
        self.setStyleSheet(STYLE)

        self.photo_path = None

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 28, 30, 28)
        layout.setSpacing(12)

        title = QLabel("Register Student")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Form fields
        self.enrollment = self._field("Enrollment Number *")
        self.name       = self._field("Full Name *")
        self.father     = self._field("Father's Name")
        self.email      = self._field("Email Address")
        self.phone      = self._field("Phone Number")

        for w in (self.enrollment, self.name, self.father, self.email, self.phone):
            layout.addWidget(w)

        # Photo preview
        self.photo_preview = QLabel("Click 'Upload Photo' to select\nstudent image")
        self.photo_preview.setObjectName("photo_box")
        self.photo_preview.setAlignment(Qt.AlignCenter)
        self.photo_preview.setFixedHeight(130)
        layout.addWidget(self.photo_preview)

        # Buttons row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        upload_btn = QPushButton("📷  Upload Photo")
        upload_btn.setObjectName("upload_btn")
        upload_btn.setCursor(Qt.PointingHandCursor)
        upload_btn.clicked.connect(self.upload_photo)

        save_btn = QPushButton("Save Student")
        save_btn.setObjectName("save_btn")
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.clicked.connect(self.save_student)

        btn_row.addWidget(upload_btn)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    # --------------------------------------------------------
    # Helpers
    # --------------------------------------------------------

    def _field(self, placeholder: str) -> QLineEdit:
        f = QLineEdit()
        f.setPlaceholderText(placeholder)
        return f

    # --------------------------------------------------------
    # Upload photo
    # --------------------------------------------------------

    def upload_photo(self):
        file, _ = QFileDialog.getOpenFileName(
            self, "Select Student Photo", "",
            "Images (*.png *.jpg *.jpeg)"
        )
        if file:
            self.photo_path = file
            pix = QPixmap(file).scaled(
                120, 120,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.photo_preview.setPixmap(pix)
            self.photo_preview.setAlignment(Qt.AlignCenter)

    # --------------------------------------------------------
    # Save student — writes BOTH photo AND CSV row
    # --------------------------------------------------------

    def save_student(self):
        enrollment = self.enrollment.text().strip()
        name       = self.name.text().strip()
        father     = self.father.text().strip()
        email      = self.email.text().strip()
        phone      = self.phone.text().strip()

        # Validation
        if not enrollment:
            QMessageBox.warning(self, "Missing Field", "Enrollment number is required.")
            return
        if not name:
            QMessageBox.warning(self, "Missing Field", "Student name is required.")
            return
        if not self.photo_path:
            QMessageBox.warning(self, "No Photo", "Please upload a student photo.")
            return

        _ensure_student_csv()

        if _enrollment_exists(enrollment):
            QMessageBox.warning(
                self, "Duplicate",
                f"Enrollment number '{enrollment}' is already registered."
            )
            return

        # 1. Copy photo
        IMAGES_DIR.mkdir(exist_ok=True)
        dest = IMAGES_DIR / f"{name}.jpg"
        shutil.copy(self.photo_path, dest)

        # 2. Write CSV row  ← this was completely missing before
        with open(STUDENT_FILE, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow([enrollment, name, father, email, phone])

        QMessageBox.information(
            self, "Success",
            f"Student '{name}' registered successfully.\n"
            f"Photo saved and details recorded."
        )
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w   = StudentForm()
    w.show()
    sys.exit(app.exec())
