import sqlite3
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, ttk


class ClinicDB:
    def __init__(self, db_path="clinic.db"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                phone TEXT,
                birth_date TEXT,
                city TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                reason TEXT,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(patient_id) REFERENCES patients(id)
            )
            """
        )
        self.conn.commit()

    def add_patient(self, full_name, phone, birth_date, city, notes):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO patients(full_name, phone, birth_date, city, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (full_name, phone, birth_date, city, notes, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def search_patients(self, keyword=""):
        cur = self.conn.cursor()
        query = """
            SELECT id, full_name, phone, birth_date, city, notes, created_at
            FROM patients
            WHERE full_name LIKE ? OR phone LIKE ? OR city LIKE ?
            ORDER BY id DESC
        """
        kw = f"%{keyword.strip()}%"
        cur.execute(query, (kw, kw, kw))
        return cur.fetchall()

    def add_appointment(self, patient_id, appointment_date, reason):
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO appointments(patient_id, appointment_date, reason, status, created_at)
            VALUES (?, ?, ?, 'Waiting', ?)
            """,
            (patient_id, appointment_date, reason, datetime.now().isoformat(timespec="seconds")),
        )
        self.conn.commit()

    def list_appointments(self):
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT a.id, p.full_name, p.phone, a.appointment_date, a.reason, a.status
            FROM appointments a
            JOIN patients p ON p.id = a.patient_id
            ORDER BY a.appointment_date ASC, a.id DESC
            """
        )
        return cur.fetchall()

    def update_appointment_status(self, appointment_id, status):
        cur = self.conn.cursor()
        cur.execute("UPDATE appointments SET status = ? WHERE id = ?", (status, appointment_id))
        self.conn.commit()

    def dashboard_stats(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM patients")
        total_patients = cur.fetchone()["count"]

        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            "SELECT COUNT(*) AS count FROM appointments WHERE appointment_date LIKE ?",
            (f"{today}%",),
        )
        today_appointments = cur.fetchone()["count"]

        cur.execute("SELECT COUNT(*) AS count FROM appointments WHERE status = 'Waiting'")
        waiting = cur.fetchone()["count"]

        return {
            "total_patients": total_patients,
            "today_appointments": today_appointments,
            "waiting": waiting,
        }


class ClinicApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clinique Privée Maroc - Reception Desk")
        self.geometry("1100x700")
        self.configure(bg="#f4f6f9")

        self.db = ClinicDB()
        self._build_style()
        self._build_ui()
        self.refresh_dashboard()
        self.refresh_patients()
        self.refresh_appointments()

    def _build_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#f4f6f9", borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 11, "bold"), padding=(10, 8))
        style.configure("TFrame", background="#f4f6f9")
        style.configure("TLabelframe", background="#f4f6f9")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"))
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        title = tk.Label(
            self,
            text="🩺 Gestion Clinique Privée (Maroc)",
            font=("Segoe UI", 20, "bold"),
            bg="#f4f6f9",
            fg="#1f3b73",
        )
        title.pack(pady=14)

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=14, pady=8)

        self.tab_dashboard = ttk.Frame(notebook)
        self.tab_patients = ttk.Frame(notebook)
        self.tab_appointments = ttk.Frame(notebook)

        notebook.add(self.tab_dashboard, text="Dashboard")
        notebook.add(self.tab_patients, text="Patients")
        notebook.add(self.tab_appointments, text="Appointments")

        self._build_dashboard_tab()
        self._build_patients_tab()
        self._build_appointments_tab()

    def _build_dashboard_tab(self):
        card_wrap = ttk.Frame(self.tab_dashboard)
        card_wrap.pack(fill="x", pady=20)

        self.lbl_total_patients = self._make_card(card_wrap, "Total Patients", "0", 0)
        self.lbl_today_appointments = self._make_card(card_wrap, "Today's Appointments", "0", 1)
        self.lbl_waiting = self._make_card(card_wrap, "Patients Waiting", "0", 2)

        hint = tk.Label(
            self.tab_dashboard,
            text=(
                "Reception workflow: 1) Add patient ➜ 2) Create appointment ➜ "
                "3) Update status (Waiting / In Consultation / Done)."
            ),
            font=("Segoe UI", 11),
            bg="#f4f6f9",
            fg="#3a3a3a",
        )
        hint.pack(pady=20)

        refresh_btn = tk.Button(
            self.tab_dashboard,
            text="Refresh Dashboard",
            command=self.refresh_dashboard,
            bg="#1f3b73",
            fg="white",
            padx=16,
            pady=8,
            relief="flat",
            font=("Segoe UI", 10, "bold"),
        )
        refresh_btn.pack()

    def _make_card(self, parent, title, value, col):
        frame = tk.Frame(parent, bg="white", highlightbackground="#d0d7e2", highlightthickness=1)
        frame.grid(row=0, column=col, padx=12, ipadx=20, ipady=14, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(frame, text=title, font=("Segoe UI", 11, "bold"), bg="white", fg="#2f2f2f").pack(pady=(6, 6))
        val_lbl = tk.Label(frame, text=value, font=("Segoe UI", 26, "bold"), bg="white", fg="#1f3b73")
        val_lbl.pack(pady=(2, 8))
        return val_lbl

    def _build_patients_tab(self):
        form = ttk.LabelFrame(self.tab_patients, text="Add New Patient")
        form.pack(fill="x", padx=8, pady=8)

        labels = ["Full Name*", "Phone", "Birth Date (YYYY-MM-DD)", "City", "Notes"]
        self.patient_entries = []
        for idx, text in enumerate(labels):
            tk.Label(form, text=text, bg="#f4f6f9", font=("Segoe UI", 10)).grid(row=idx, column=0, sticky="w", padx=8, pady=5)
            ent = tk.Entry(form, width=45, font=("Segoe UI", 10))
            ent.grid(row=idx, column=1, padx=8, pady=5, sticky="w")
            self.patient_entries.append(ent)

        add_btn = tk.Button(
            form,
            text="Add Patient",
            command=self.add_patient,
            bg="#0f766e",
            fg="white",
            relief="flat",
            padx=14,
            pady=7,
            font=("Segoe UI", 10, "bold"),
        )
        add_btn.grid(row=0, column=2, padx=10)

        search_frame = ttk.Frame(self.tab_patients)
        search_frame.pack(fill="x", padx=8, pady=(4, 0))

        tk.Label(search_frame, text="Search:", bg="#f4f6f9", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.patient_search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.patient_search_var, font=("Segoe UI", 10), width=35)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<KeyRelease>", lambda _: self.refresh_patients())

        cols = ("ID", "Name", "Phone", "Birth Date", "City", "Notes")
        self.patient_tree = ttk.Treeview(self.tab_patients, columns=cols, show="headings", height=14)
        for col in cols:
            self.patient_tree.heading(col, text=col)
            width = 150 if col in ["Name", "Notes"] else 95
            self.patient_tree.column(col, width=width, anchor="center")
        self.patient_tree.pack(fill="both", expand=True, padx=8, pady=10)

    def _build_appointments_tab(self):
        top = ttk.LabelFrame(self.tab_appointments, text="Create Appointment")
        top.pack(fill="x", padx=8, pady=8)

        tk.Label(top, text="Patient ID*", bg="#f4f6f9").grid(row=0, column=0, padx=8, pady=6, sticky="w")
        tk.Label(top, text="Date & Time (YYYY-MM-DD HH:MM)*", bg="#f4f6f9").grid(row=1, column=0, padx=8, pady=6, sticky="w")
        tk.Label(top, text="Reason", bg="#f4f6f9").grid(row=2, column=0, padx=8, pady=6, sticky="w")

        self.app_patient_id = tk.Entry(top, width=30)
        self.app_date = tk.Entry(top, width=30)
        self.app_reason = tk.Entry(top, width=45)
        self.app_patient_id.grid(row=0, column=1, padx=8, pady=6, sticky="w")
        self.app_date.grid(row=1, column=1, padx=8, pady=6, sticky="w")
        self.app_reason.grid(row=2, column=1, padx=8, pady=6, sticky="w")

        tk.Button(
            top,
            text="Add Appointment",
            command=self.add_appointment,
            bg="#1d4ed8",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=7,
        ).grid(row=0, column=2, padx=10)

        status_frame = ttk.Frame(self.tab_appointments)
        status_frame.pack(fill="x", padx=8, pady=(2, 0))

        tk.Label(status_frame, text="Update selected appointment status:", bg="#f4f6f9", font=("Segoe UI", 10, "bold")).pack(side="left")
        for st in ["Waiting", "In Consultation", "Done"]:
            tk.Button(
                status_frame,
                text=st,
                command=lambda s=st: self.change_status(s),
                relief="groove",
                padx=10,
            ).pack(side="left", padx=6)

        cols = ("Appointment ID", "Patient Name", "Phone", "Date", "Reason", "Status")
        self.app_tree = ttk.Treeview(self.tab_appointments, columns=cols, show="headings", height=14)
        for col in cols:
            self.app_tree.heading(col, text=col)
            width = 170 if col in ["Patient Name", "Reason"] else 120
            self.app_tree.column(col, width=width, anchor="center")
        self.app_tree.pack(fill="both", expand=True, padx=8, pady=10)

    def add_patient(self):
        name, phone, birth, city, notes = [e.get().strip() for e in self.patient_entries]
        if not name:
            messagebox.showerror("Missing info", "Full name is required.")
            return

        self.db.add_patient(name, phone, birth, city, notes)
        for e in self.patient_entries:
            e.delete(0, tk.END)
        self.refresh_patients()
        self.refresh_dashboard()
        messagebox.showinfo("Success", "Patient added successfully.")

    def refresh_patients(self):
        for i in self.patient_tree.get_children():
            self.patient_tree.delete(i)

        rows = self.db.search_patients(self.patient_search_var.get())
        for r in rows:
            self.patient_tree.insert("", tk.END, values=(r["id"], r["full_name"], r["phone"], r["birth_date"], r["city"], r["notes"]))

    def add_appointment(self):
        patient_id = self.app_patient_id.get().strip()
        date_time = self.app_date.get().strip()
        reason = self.app_reason.get().strip()

        if not patient_id or not date_time:
            messagebox.showerror("Missing info", "Patient ID and date/time are required.")
            return

        try:
            datetime.strptime(date_time, "%Y-%m-%d %H:%M")
            int(patient_id)
        except ValueError:
            messagebox.showerror("Invalid format", "Use Patient ID as number and date as YYYY-MM-DD HH:MM")
            return

        self.db.add_appointment(int(patient_id), date_time, reason)
        self.app_patient_id.delete(0, tk.END)
        self.app_date.delete(0, tk.END)
        self.app_reason.delete(0, tk.END)
        self.refresh_appointments()
        self.refresh_dashboard()
        messagebox.showinfo("Success", "Appointment created.")

    def refresh_appointments(self):
        for i in self.app_tree.get_children():
            self.app_tree.delete(i)

        for row in self.db.list_appointments():
            self.app_tree.insert(
                "",
                tk.END,
                values=(
                    row["id"],
                    row["full_name"],
                    row["phone"],
                    row["appointment_date"],
                    row["reason"],
                    row["status"],
                ),
            )

    def change_status(self, status):
        selected = self.app_tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an appointment first.")
            return

        app_id = self.app_tree.item(selected[0])["values"][0]
        self.db.update_appointment_status(app_id, status)
        self.refresh_appointments()
        self.refresh_dashboard()

    def refresh_dashboard(self):
        stats = self.db.dashboard_stats()
        self.lbl_total_patients.config(text=str(stats["total_patients"]))
        self.lbl_today_appointments.config(text=str(stats["today_appointments"]))
        self.lbl_waiting.config(text=str(stats["waiting"]))


if __name__ == "__main__":
    app = ClinicApp()
    app.mainloop()
