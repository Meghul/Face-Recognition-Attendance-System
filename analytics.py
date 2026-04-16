import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ATTENDANCE_DIR = Path("Attendance")

def plot_subject_attendance(subject):

    files = list((ATTENDANCE_DIR/subject).glob("*.csv"))

    counts = []

    dates = []

    for f in files:

        df = pd.read_csv(f)

        counts.append(len(df))

        dates.append(f.stem)

    plt.figure(figsize=(8,4))

    plt.plot(dates, counts, marker="o")

    plt.title(f"{subject} Attendance Trend")

    plt.xlabel("Date")
    plt.ylabel("Students Present")

    plt.xticks(rotation=45)

    plt.tight_layout()

    plt.show()