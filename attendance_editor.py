import csv
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtWidgets import QHeaderView


class AttendanceEditor(QWidget):

    def __init__(self, file_path):
        super().__init__()

        self.file_path = file_path

        self.setWindowTitle("Edit Attendance")
        self.resize(500, 400)

        layout = QVBoxLayout()

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Student", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(self.table)

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)

        layout.addWidget(save_btn)

        self.setLayout(layout)

        self.load_data()

    def load_data(self):

        with open(self.file_path) as f:

            reader = csv.DictReader(f)
            rows = list(reader)

        self.table.setRowCount(len(rows))

        for i, r in enumerate(rows):

            self.table.setItem(i, 0, QTableWidgetItem(r["Student"]))
            self.table.setItem(i, 1, QTableWidgetItem(r["Status"]))

    def save_changes(self):

        rows = []

        for i in range(self.table.rowCount()):

            student = self.table.item(i, 0).text()
            status = self.table.item(i, 1).text()

            rows.append([student, status])

        with open(self.file_path, "w", newline="") as f:

            writer = csv.writer(f)
            writer.writerow(["Student", "Status"])
            writer.writerows(rows)

        QMessageBox.information(self, "Saved", "Attendance updated successfully")