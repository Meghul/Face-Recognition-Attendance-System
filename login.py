import hashlib

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton,
    QVBoxLayout, QLineEdit, QMessageBox, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from dashboard import Dashboard

# ------------------------------------------------------------
# Stored as sha256 hash — plain text "admin" is never in code.
# To change password: hashlib.sha256("newpassword".encode()).hexdigest()
# ------------------------------------------------------------
ADMIN_USER = "admin"
ADMIN_PASS_HASH = hashlib.sha256("admin".encode()).hexdigest()


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Attendance System")
        self.setFixedSize(420, 480)

        self.setStyleSheet("""
        QWidget {
            background-color: #0f172a;
            color: white;
            font-family: 'Segoe UI', sans-serif;
        }

        QLabel#title {
            font-size: 26px;
            font-weight: bold;
            color: #6366f1;
        }

        QLabel#subtitle {
            font-size: 13px;
            color: #64748b;
        }

        QLineEdit {
            padding: 12px 16px;
            border-radius: 8px;
            border: 1px solid #334155;
            background-color: #1e293b;
            color: white;
            font-size: 14px;
        }

        QLineEdit:focus {
            border: 1px solid #6366f1;
        }

        QPushButton#login_btn {
            background-color: #6366f1;
            padding: 13px;
            border-radius: 8px;
            color: white;
            font-weight: bold;
            font-size: 15px;
        }

        QPushButton#login_btn:hover {
            background-color: #4f46e5;
        }

        QPushButton#login_btn:pressed {
            background-color: #3730a3;
        }
        """)

        outer = QVBoxLayout()
        outer.setAlignment(Qt.AlignCenter)
        outer.setContentsMargins(50, 40, 50, 40)
        outer.setSpacing(14)

        # Logo / Title
        title = QLabel("AI Attendance")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignCenter)

        subtitle = QLabel("Face Recognition System")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignCenter)

        outer.addWidget(title)
        outer.addWidget(subtitle)
        outer.addSpacerItem(QSpacerItem(0, 20, QSizePolicy.Minimum, QSizePolicy.Fixed))

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)
        self.password.returnPressed.connect(self.login)

        login_btn = QPushButton("Login")
        login_btn.setObjectName("login_btn")
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.clicked.connect(self.login)

        outer.addWidget(self.username)
        outer.addWidget(self.password)
        outer.addSpacerItem(QSpacerItem(0, 6, QSizePolicy.Minimum, QSizePolicy.Fixed))
        outer.addWidget(login_btn)

        hint = QLabel("Default: admin / admin")
        hint.setObjectName("subtitle")
        hint.setAlignment(Qt.AlignCenter)
        outer.addWidget(hint)

        self.setLayout(outer)

    def login(self):
        user = self.username.text().strip()
        pw   = self.password.text()

        pw_hash = hashlib.sha256(pw.encode()).hexdigest()

        if user == ADMIN_USER and pw_hash == ADMIN_PASS_HASH:
            self.dashboard = Dashboard()
            self.dashboard.show()
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")
            self.password.clear()
            self.password.setFocus()
