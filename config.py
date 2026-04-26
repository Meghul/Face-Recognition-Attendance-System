"""
Central configuration and path utilities for the AI Attendance System
"""

from pathlib import Path

# ------------------------------------------------
# Base directory (same folder as this file)
# ------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


# ------------------------------------------------
# Core folders
# ------------------------------------------------

IMAGES_DIR        = BASE_DIR / "ImagesAttendance"
ATTENDANCE_DIR    = BASE_DIR / "Attendance"
STUDENT_LIST_DIR  = BASE_DIR / "StudentList"

STUDENT_LIST_FILE = STUDENT_LIST_DIR / "StudentList.csv"


# ------------------------------------------------
# Ensure directories exist at startup
# ------------------------------------------------

for _dir in (IMAGES_DIR, ATTENDANCE_DIR, STUDENT_LIST_DIR):
    _dir.mkdir(exist_ok=True)


# ------------------------------------------------
# Subject utilities
# ------------------------------------------------

def normalize_subject(subject: str) -> str:
    """
    Normalise subject names so folders stay consistent.
    e.g.  'AI', 'Ai', '  AI  ' → 'ai'
    """
    return subject.strip().lower()


def subject_dir(subject: str) -> Path:
    """Return subject folder path (creates it if needed)."""
    path = ATTENDANCE_DIR / normalize_subject(subject)
    path.mkdir(exist_ok=True)
    return path


def attendance_file(subject: str, date_str: str) -> Path:
    """Return path to the CSV for a given subject + date."""
    return subject_dir(subject) / f"{date_str}.csv"


# ------------------------------------------------
# CSV schemas
# ------------------------------------------------

ATTENDANCE_HEADER = ["Student", "Status"]

STUDENT_HEADER = [
    "Enrollment_No",
    "Name",
    "Father_Name",
    "Email",
    "Contact",
]


# ------------------------------------------------
# CSV initialisation helpers
# ------------------------------------------------

def ensure_student_list():
    """Create student CSV with header if it doesn't exist."""
    if not STUDENT_LIST_FILE.exists():
        import csv
        with open(STUDENT_LIST_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(STUDENT_HEADER)


def ensure_attendance_file(file_path: Path):
    """Create attendance CSV with header if it doesn't exist."""
    if not file_path.exists():
        import csv
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(ATTENDANCE_HEADER)


__all__ = [
    "BASE_DIR",
    "IMAGES_DIR",
    "ATTENDANCE_DIR",
    "STUDENT_LIST_DIR",
    "STUDENT_LIST_FILE",
    "normalize_subject",
    "subject_dir",
    "attendance_file",
    "ensure_student_list",
    "ensure_attendance_file",
]
