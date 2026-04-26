import csv

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QMessageBox, QComboBox, QHeaderView
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt


STYLE = """
QWidget {
    background: #0f172a;
    color: white;
    font-family: 'Segoe UI', sans-serif;
}

QLabel {
    color: white;
}

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

QPushButton {
    background: #6366f1;
    padding: 11px;
    border-radius: 8px;
    color: white;
    font-weight: bold;
    font-size: 14px;
}

QPushButton:hover {
    background: #4f46e5;
}

QComboBox {
    background: #1e293b;
    color: white;
    border: 1px solid #334155;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 13px;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background: #1e293b;
    color: white;
    selection-background-color: #6366f1;
}
"""


class AttendanceEditor(QWidget):

    def __init__(self, file_path):
        super().__init__()

        self.file_path = file_path
        self.setWindowTitle(f"Edit Attendance — {file_path.parent.name} / {file_path.stem}")
        self.resize(520, 480)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header info
        info = QLabel(
            f"Subject: <b>{file_path.parent.name.upper()}</b>   "
            f"Date: <b>{file_path.stem}</b>"
        )
        info.setStyleSheet("color:#94a3b8;font-size:13px;")
        layout.addWidget(info)

        note = QLabel("Use the dropdown to change each student's status. Changes are saved only when you click Save.")
        note.setStyleSheet("color:#64748b;font-size:12px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Student", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.table.setColumnWidth(1, 150)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)  # name column non-editable

        layout.addWidget(self.table)

        # Bottom buttons
        btn_row = QHBoxLayout()

        self.present_all_btn = QPushButton("Mark All Present")
        self.present_all_btn.setStyleSheet("background:#166534;")
        self.present_all_btn.clicked.connect(lambda: self._mark_all("Present"))

        self.absent_all_btn = QPushButton("Mark All Absent")
        self.absent_all_btn.setStyleSheet("background:#7f1d1d;")
        self.absent_all_btn.clicked.connect(lambda: self._mark_all("Absent"))

        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)

        btn_row.addWidget(self.present_all_btn)
        btn_row.addWidget(self.absent_all_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)
        self.setLayout(layout)

        self.load_data()

    # --------------------------------------------------------
    # Load CSV into table with QComboBox for status
    # --------------------------------------------------------

    def load_data(self):
        with open(self.file_path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        self.table.setRowCount(len(rows))
        self.table.setRowHeight(0, 36)

        for i, r in enumerate(rows):
            self.table.setRowHeight(i, 36)

            # Student name (read-only)
            name_item = QTableWidgetItem(r["Student"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, name_item)

            # Status dropdown
            combo = QComboBox()
            combo.addItems(["Present", "Absent"])
            combo.setCurrentText(r["Status"].strip())
            combo.currentTextChanged.connect(lambda _, row=i: self._colour_row(row))
            self.table.setCellWidget(i, 1, combo)

            self._colour_row(i)

    # --------------------------------------------------------
    # Colour row green / red based on status
    # --------------------------------------------------------

    def _colour_row(self, row: int):
        combo = self.table.cellWidget(row, 1)
        if combo is None:
            return
        status = combo.currentText()
        if status == "Present":
            bg = QColor("#052e16")  # dark green
            fg = QColor("#4ade80")
        else:
            bg = QColor("#2d0b0b")  # dark red
            fg = QColor("#f87171")

        name_item = self.table.item(row, 0)
        if name_item:
            name_item.setBackground(bg)
            name_item.setForeground(fg)

    # --------------------------------------------------------
    # Mark all rows to one status
    # --------------------------------------------------------

    def _mark_all(self, status: str):
        for row in range(self.table.rowCount()):
            combo = self.table.cellWidget(row, 1)
            if combo:
                combo.setCurrentText(status)
                self._colour_row(row)

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    def save_changes(self):
        rows = []
        for i in range(self.table.rowCount()):
            name   = self.table.item(i, 0).text()
            combo  = self.table.cellWidget(i, 1)
            status = combo.currentText() if combo else "Absent"
            rows.append([name, status])

        with open(self.file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Student", "Status"])
            writer.writerows(rows)

        QMessageBox.information(self, "Saved", "Attendance updated successfully.")
