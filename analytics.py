import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.ticker as ticker
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QComboBox, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt

from config import ATTENDANCE_DIR

BG      = "#0f172a"
SURFACE = "#1e293b"
ACCENT  = "#6366f1"
ACCENT2 = "#818cf8"
TEXT    = "#e2e8f0"
MUTED   = "#64748b"
GREEN   = "#22c55e"
RED     = "#ef4444"
AMBER   = "#f59e0b"
BORDER  = "#334155"


class AnalyticsPage(QWidget):
    """
    Analytics dashboard.
    Auto-refreshes on subject OR chart-type change — no manual Refresh needed.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{BG};color:{TEXT};font-family:'Segoe UI',sans-serif;")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(16)

        # ── Header ─────────────────────────────────────────────
        title = QLabel("Analytics")
        title.setStyleSheet(f"font-size:28px;font-weight:800;color:{TEXT};letter-spacing:-0.5px;")
        subtitle = QLabel("Attendance trends and subject-wise breakdown")
        subtitle.setStyleSheet(f"font-size:13px;color:{MUTED};margin-top:2px;")
        root.addWidget(title)
        root.addWidget(subtitle)

        # ── Controls row ────────────────────────────────────────
        ctrl_frame = QFrame()
        ctrl_frame.setStyleSheet(f"""
            QFrame {{
                background:{SURFACE};
                border-radius:12px;
                border:1px solid {BORDER};
            }}
        """)
        ctrl_layout = QHBoxLayout(ctrl_frame)
        ctrl_layout.setContentsMargins(16, 12, 16, 12)
        ctrl_layout.setSpacing(16)

        combo_style = f"""
            QComboBox {{
                background:#0f172a; color:{TEXT};
                border:1px solid {BORDER}; border-radius:8px;
                padding:7px 14px; font-size:13px; min-width:190px;
            }}
            QComboBox:hover {{ border-color:{ACCENT}; }}
            QComboBox::drop-down {{ border:none; width:22px; }}
            QComboBox QAbstractItemView {{
                background:{SURFACE}; color:{TEXT};
                selection-background-color:{ACCENT};
                border:1px solid {BORDER};
                padding:4px;
            }}
        """

        subject_lbl = QLabel("SUBJECT")
        subject_lbl.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:0.8px;")
        self.subject_combo = QComboBox()
        self.subject_combo.setStyleSheet(combo_style)

        chart_lbl = QLabel("CHART TYPE")
        chart_lbl.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:700;letter-spacing:0.8px;")
        self.chart_combo = QComboBox()
        self.chart_combo.addItems([
            "Present vs Absent (Bar)",
            "Attendance Trend (Line)",
            "Student Breakdown (Bar)",
        ])
        self.chart_combo.setStyleSheet(combo_style)

        ctrl_layout.addWidget(subject_lbl)
        ctrl_layout.addWidget(self.subject_combo)
        ctrl_layout.addSpacing(8)
        ctrl_layout.addWidget(chart_lbl)
        ctrl_layout.addWidget(self.chart_combo)
        ctrl_layout.addStretch()

        root.addWidget(ctrl_frame)

        # ── Stat cards row ──────────────────────────────────────
        self.cards_row = QHBoxLayout()
        self.cards_row.setSpacing(12)
        root.addLayout(self.cards_row)

        # ── Chart canvas ────────────────────────────────────────
        chart_frame = QFrame()
        chart_frame.setStyleSheet(f"""
            QFrame {{
                background:{SURFACE};
                border-radius:14px;
                border:1px solid {BORDER};
            }}
        """)
        chart_vlay = QVBoxLayout(chart_frame)
        chart_vlay.setContentsMargins(8, 8, 8, 8)

        self.figure = Figure(figsize=(10, 4.5), facecolor=SURFACE)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setStyleSheet(f"background:{SURFACE};border-radius:10px;")
        chart_vlay.addWidget(self.canvas)
        root.addWidget(chart_frame, 1)

        # ── Load subjects, then wire signals (order matters) ────
        self._load_subjects()
        self.subject_combo.currentIndexChanged.connect(self.refresh)
        self.chart_combo.currentIndexChanged.connect(self.refresh)
        self.refresh()

    # ─────────────────────────────────────────────────────────
    # Data helpers
    # ─────────────────────────────────────────────────────────

    def _load_subjects(self):
        """Reload subject dropdown without firing signals."""
        self.subject_combo.blockSignals(True)
        prev = self.subject_combo.currentText()
        self.subject_combo.clear()
        if ATTENDANCE_DIR.exists():
            subjects = sorted(p.name for p in ATTENDANCE_DIR.iterdir() if p.is_dir())
            self.subject_combo.addItems(subjects)
            idx = self.subject_combo.findText(prev)
            if idx >= 0:
                self.subject_combo.setCurrentIndex(idx)
        self.subject_combo.blockSignals(False)

    def _read_subject_data(self, subject: str):
        path = ATTENDANCE_DIR / subject
        if not path.exists():
            return [], [], [], {}

        files = sorted(path.glob("*.csv"), key=lambda f: f.stem)
        dates, present, absent = [], [], []
        student_stats = {}

        for f in files:
            p_count = a_count = 0
            with open(f, newline="", encoding="utf-8") as fp:
                for row in csv.DictReader(fp):
                    name   = row["Student"].strip()
                    status = row["Status"].strip()
                    if name not in student_stats:
                        student_stats[name] = [0, 0]
                    student_stats[name][1] += 1
                    if status == "Present":
                        p_count += 1
                        student_stats[name][0] += 1
                    else:
                        a_count += 1
            dates.append(f.stem)
            present.append(p_count)
            absent.append(a_count)

        return dates, present, absent, student_stats

    # ─────────────────────────────────────────────────────────
    # Stat cards
    # ─────────────────────────────────────────────────────────

    def _rebuild_cards(self, subject, dates, present, absent, student_stats):
        while self.cards_row.count():
            item = self.cards_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        total_classes = len(dates)
        total_present = sum(present)
        total_records = sum(p + a for p, a in zip(present, absent))
        overall_pct   = round(total_present / total_records * 100) if total_records else 0
        below_75      = sum(
            1 for attended, total in student_stats.values()
            if total and (attended / total * 100) < 75
        )

        card_data = [
            ("Classes Recorded", str(total_classes),     ACCENT),
            ("Avg Attendance",   f"{overall_pct}%",       GREEN if overall_pct >= 75 else AMBER),
            ("Total Students",   str(len(student_stats)), ACCENT2),
            ("Below 75%",        str(below_75),           RED if below_75 else GREEN),
        ]
        for label, value, colour in card_data:
            self.cards_row.addWidget(self._make_card(label, value, colour))

    def _make_card(self, label: str, value: str, colour: str) -> QFrame:
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background:{SURFACE};
                border-radius:12px;
                border:1px solid {BORDER};
                border-left:4px solid {colour};
            }}
        """)
        card.setFixedHeight(80)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 10, 16, 10)
        lay.setSpacing(4)
        lbl = QLabel(label)
        lbl.setStyleSheet(f"color:{MUTED};font-size:11px;font-weight:600;letter-spacing:0.5px;")
        val = QLabel(value)
        val.setStyleSheet(f"color:{colour};font-size:24px;font-weight:800;")
        lay.addWidget(lbl)
        lay.addWidget(val)
        return card

    # ─────────────────────────────────────────────────────────
    # Chart — called automatically on every combo change
    # ─────────────────────────────────────────────────────────

    def refresh(self):
        """Read data for the CURRENTLY selected subject + chart type and redraw."""
        self._load_subjects()
        subject = self.subject_combo.currentText()
        if not subject:
            self._show_empty("No subjects found. Take attendance to get started.")
            return

        dates, present, absent, student_stats = self._read_subject_data(subject)
        self._rebuild_cards(subject, dates, present, absent, student_stats)

        chart_type = self.chart_combo.currentText()
        self.figure.clear()
        ax = self.figure.add_subplot(111)

        # Consistent dark styling
        bg_plot = "#0d1929"
        ax.set_facecolor(bg_plot)
        self.figure.patch.set_facecolor(SURFACE)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.tick_params(colors=MUTED, labelsize=10)
        ax.xaxis.label.set_color(MUTED)
        ax.yaxis.label.set_color(MUTED)
        ax.title.set_color(TEXT)
        ax.yaxis.set_major_locator(ticker.MaxNLocator(integer=True))
        ax.grid(axis="y", color=BORDER, linewidth=0.5, alpha=0.4, linestyle="--")

        if not dates:
            ax.text(0.5, 0.5,
                    f"No attendance data found for {subject.upper()}",
                    ha="center", va="center", color=MUTED, fontsize=13,
                    transform=ax.transAxes)
            self.canvas.draw()
            return

        short_dates = [d[5:] for d in dates]   # "2026-03-16" → "03-16"

        if "Line" in chart_type:
            ax.plot(short_dates, present, marker="o", color=ACCENT,
                    linewidth=2.5, markersize=8, label="Present", zorder=3)
            ax.fill_between(short_dates, present, alpha=0.15, color=ACCENT)
            if len(short_dates) > 1:
                ax.plot(short_dates, absent, marker="s", color=RED,
                        linewidth=2, markersize=7, label="Absent",
                        linestyle="--", alpha=0.75, zorder=3)
            ax.set_title(f"{subject.upper()} — Attendance Trend",
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_ylabel("Students", labelpad=8)
            ax.legend(facecolor=bg_plot, edgecolor=BORDER, labelcolor=TEXT,
                      framealpha=0.9, fontsize=11)

        elif "Bar" in chart_type and "Student" not in chart_type:
            x     = range(len(short_dates))
            width = 0.38
            bars_p = ax.bar([i - width/2 for i in x], present, width,
                            color=GREEN, alpha=0.85, label="Present",
                            zorder=3, linewidth=0)
            bars_a = ax.bar([i + width/2 for i in x], absent,  width,
                            color=RED, alpha=0.75, label="Absent",
                            zorder=3, linewidth=0)
            for bar in bars_p:
                h = bar.get_height()
                if h > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                            str(int(h)), ha="center", va="bottom",
                            color=GREEN, fontsize=9, fontweight="bold")
            for bar in bars_a:
                h = bar.get_height()
                if h > 0:
                    ax.text(bar.get_x() + bar.get_width()/2, h + 0.05,
                            str(int(h)), ha="center", va="bottom",
                            color=RED, fontsize=9, fontweight="bold")
            ax.set_xticks(list(x))
            ax.set_xticklabels(short_dates, rotation=30, ha="right")
            ax.set_title(f"{subject.upper()} — Present vs Absent per Class",
                         fontsize=14, pad=14, fontweight="bold")
            ax.set_ylabel("Students", labelpad=8)
            ax.legend(facecolor=bg_plot, edgecolor=BORDER, labelcolor=TEXT,
                      framealpha=0.9, fontsize=11)

        else:
            names    = list(student_stats.keys())
            percents = [
                round(v[0] / v[1] * 100) if v[1] else 0
                for v in student_stats.values()
            ]
            colours  = [
                GREEN if p >= 75 else (AMBER if p >= 50 else RED)
                for p in percents
            ]
            bars = ax.barh(names, percents, color=colours, alpha=0.85,
                           zorder=3, linewidth=0, height=0.55)
            ax.axvline(75, color=AMBER, linestyle="--", linewidth=1.5,
                       label="75% threshold", zorder=4)
            ax.set_xlim(0, 115)
            ax.set_xlabel("Attendance %", labelpad=8)
            ax.set_title(f"{subject.upper()} — Student Attendance Breakdown",
                         fontsize=14, pad=14, fontweight="bold")
            for bar, pct in zip(bars, percents):
                ax.text(bar.get_width() + 1.5,
                        bar.get_y() + bar.get_height() / 2,
                        f"{pct}%", va="center", color=TEXT, fontsize=9,
                        fontweight="bold")
            ax.legend(facecolor=bg_plot, edgecolor=BORDER, labelcolor=TEXT,
                      framealpha=0.9, fontsize=11)
            ax.tick_params(axis="y", labelsize=10)
            ax.grid(axis="x", color=BORDER, linewidth=0.5, alpha=0.4, linestyle="--")

        if "%" not in ax.get_xlabel():
            ax.set_xlabel("Date", labelpad=8)
        self.figure.tight_layout(pad=2.0)
        self.canvas.draw()

    def _show_empty(self, msg: str):
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_facecolor("#0d1929")
        self.figure.patch.set_facecolor(SURFACE)
        for spine in ax.spines.values():
            spine.set_edgecolor(BORDER)
        ax.text(0.5, 0.5, msg, ha="center", va="center",
                color=MUTED, fontsize=13, transform=ax.transAxes)
        self.canvas.draw()
