from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QLineEdit,
    QMessageBox
)

from dashboard import Dashboard


class LoginWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("AI Attendance Login")
        self.resize(300,200)

        layout = QVBoxLayout()

        title = QLabel("AI Attendance System")

        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")

        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.Password)

        login_btn = QPushButton("Login")

        login_btn.clicked.connect(self.login)

        layout.addWidget(title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(login_btn)

        self.setLayout(layout)

    def login(self):

        user = self.username.text()
        pw = self.password.text()

        if user == "admin" and pw == "admin":

            self.dashboard = Dashboard()
            self.dashboard.show()

            self.close()

        else:

            QMessageBox.warning(self,"Error","Wrong credentials")