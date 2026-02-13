# Gear-Up

## Private Clinic Reception App (Morocco)

A creative desktop app for a private doctor clinic reception desk.

### Features
- Add/search patients quickly.
- Create and manage appointments.
- Update patient flow status: **Waiting**, **In Consultation**, **Done**.
- Dashboard cards for:
  - Total patients
  - Today's appointments
  - Waiting patients
- Local SQLite database (`clinic.db`) to save data.

### Run
```bash
python3 clinic_app.py
```

No extra packages required (uses Python standard library: `tkinter` + `sqlite3`).

### Reception workflow
1. Secretary registers patient details in **Patients** tab.
2. Secretary creates appointment in **Appointments** tab using Patient ID.
3. During clinic flow, status is updated by click buttons.
4. Dashboard gives instant overview of activity.
