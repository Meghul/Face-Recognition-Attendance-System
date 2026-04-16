# Attendance Management System (Face Recognition + Tkinter)

Revived and refactored version of your legacy project. This version removes hard‑coded absolute paths and introduces a small `config.py` for portability.

## Features

- Login screen (simple admin credentials)
- Dashboard with:
  - Take attendance (webcam + face recognition)
  - Register new student (store photo + CSV row)
  - View attendance per date & subject
  - View student list
- Subject creation
- Progress summary widget

## Project Structure

```
config.py              # Centralized paths & helpers
attendance.py          # Face encoding + attendance capture
login.py               # Login UI (entry point)
dashboard.py           # Main UI after login
form.py                # Student registration form
test4.py               # CSV append helper (refactored)
ImagesAttendance/      # Stored student face images
Attendance/            # Per-subject attendance CSVs
StudentList/           # Student list CSV
asset/                 # UI images
```

## Setup (Windows, cmd.exe)

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

If `dlib` wheels fail for `face_recognition`, install a precompiled package:

```cmd
pip install face_recognition
```

(If build errors appear, you may need Visual Studio Build Tools or consider using `cmake` and `dlib` manually. Most modern Python versions have pre-built wheels.)

## Running

Start from the login screen:

```cmd
.venv\Scripts\activate
python login.py
```

Admin credentials (hard-coded for now):

```
Username: admin
Password: admin
```

## Usage Notes

1. Register at least one student with a clear frontal photo (Form -> capture/upload) before taking attendance.
2. After registering, restart the app (or we can later add dynamic re-encoding) so new faces are included.
3. Create a subject before taking attendance (Dashboard -> Add Subject).
4. Take attendance (Dashboard -> Take Attendance). Press `q` in webcam window to finish.

## Data Files

- Student list: `StudentList/StudentList.csv`
- Attendance CSV example: `Attendance/<Subject>/<YYYY-MM-DD>.csv`

## Improvements Added

- Central path handling (`config.py`)
- Safe face encoding (skips images with no detectable face)
- Duplicate student enrollment prevention
- Header auto-creation for CSV files
- Robust attendance marking (no duplicate rows per day)

## Potential Next Steps

- Dynamic re-encoding when new student photo saved
- Replace hard-coded admin credential with hashed user store
- Add error handling & logging
- Package as executable with `pyinstaller`
- Add unit tests

## Troubleshooting

- Face not detected: ensure good lighting & clear frontal image.
- Import errors: confirm virtual environment is activated.
- CSV permission issues: avoid opening files in Excel while taking attendance.

Enjoy the refreshed project!
