import sys
from PySide6.QtWidgets import QApplication
from login import LoginWindow

app = QApplication(sys.argv)
app.setApplicationName("AI Attendance System")

window = LoginWindow()
window.show()

sys.exit(app.exec())
