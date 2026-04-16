"""
Central configuration and path utilities for the AI Attendance System
"""

from pathlib import Path

# ------------------------------------------------
# Base directory
# ------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


# ------------------------------------------------
# Core folders
# ------------------------------------------------

IMAGES_DIR = BASE_DIR / "ImagesAttendance"
ATTENDANCE_DIR = BASE_DIR / "Attendance"
STUDENT_LIST_DIR = BASE_DIR / "StudentList"

STUDENT_LIST_FILE = STUDENT_LIST_DIR / "students.csv"


# ------------------------------------------------
# Ensure directories exist
# ------------------------------------------------

for directory in (IMAGES_DIR, ATTENDANCE_DIR, STUDENT_LIST_DIR):
    directory.mkdir(exist_ok=True)


# ------------------------------------------------
# Subject utilities
# ------------------------------------------------

def normalize_subject(subject: str) -> str:
    """
    Normalize subject names to avoid duplicate folders
    Example:
        AI -> ai
        Ai -> ai
        AI  -> ai
    """
    return subject.strip().lower()


def subject_dir(subject: str) -> Path:
    """
    Return subject folder path and create it if needed
    """
    subject = normalize_subject(subject)

    path = ATTENDANCE_DIR / subject
    path.mkdir(exist_ok=True)

    return path


def attendance_file(subject: str, date_str: str) -> Path:
    """
    Return attendance CSV file for subject and date
    """
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
    "Contact"
]


# ------------------------------------------------
# Ensure CSV headers
# ------------------------------------------------

def ensure_student_list():
    """
    Create student CSV if not exists
    """
    if not STUDENT_LIST_FILE.exists():

        import csv

        with open(STUDENT_LIST_FILE, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)
            writer.writerow(STUDENT_HEADER)


def ensure_attendance_file(file_path: Path):
    """
    Create attendance file with header if not exists
    """

    if not file_path.exists():

        import csv

        with open(file_path, "w", newline="", encoding="utf-8") as f:

            writer = csv.writer(f)
            writer.writerow(ATTENDANCE_HEADER)


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
    "ensure_attendance_file"
]