import tkinter as tk
from tkinter import messagebox, ttk
import mysql.connector
from mysql.connector import Error

# ══════════════════════════════════════════════════════
#  CONFIGURATION  –  edit to match your MySQL setup
# ══════════════════════════════════════════════════════
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",             # ← your MySQL username
    "password": "karish@111",   # ← your MySQL password
    "database": "employee_db",
}
DB_NAME    = "employee_db"
TABLE_NAME = "employees"


# ══════════════════════════════════════════════════════
#  DATABASE HELPERS
# ══════════════════════════════════════════════════════

def get_connection(with_db=True):
    cfg = DB_CONFIG.copy()
    if not with_db:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)


def setup_database():
    conn   = get_connection(with_db=False)
    cursor = conn.cursor()

    # 1. Create DB if missing
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}`")
    cursor.execute(f"USE `{DB_NAME}`")

    # 2. Create table with all columns if it doesn't exist
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS `{TABLE_NAME}` (
            id           INT AUTO_INCREMENT PRIMARY KEY,
            emp_name     VARCHAR(100)   NOT NULL,
            age          INT            NOT NULL DEFAULT 0,
            phone        VARCHAR(15)    NOT NULL DEFAULT '',
            aadhar       VARCHAR(12)    NOT NULL DEFAULT '',
            salary       DECIMAL(12,2)  NOT NULL DEFAULT 0,
            place        VARCHAR(100)   NOT NULL DEFAULT '',
            dept_id      VARCHAR(20)    NOT NULL DEFAULT '',
            email        VARCHAR(150)   NOT NULL DEFAULT '',
            created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 3. Auto-migrate: add any missing columns to an existing old table
    cursor.execute(f"SHOW COLUMNS FROM `{TABLE_NAME}`")
    existing_cols = {row[0].lower() for row in cursor.fetchall()}

    migrations = [
        ("age",        "INT           NOT NULL DEFAULT 0    AFTER emp_name"),
        ("phone",      "VARCHAR(15)   NOT NULL DEFAULT ''   AFTER age"),
        ("aadhar",     "VARCHAR(12)   NOT NULL DEFAULT ''   AFTER phone"),
        ("salary",     "DECIMAL(12,2) NOT NULL DEFAULT 0"),
        ("place",      "VARCHAR(100)  NOT NULL DEFAULT ''"),
        ("dept_id",    "VARCHAR(20)   NOT NULL DEFAULT ''"),
        ("email",      "VARCHAR(150)  NOT NULL DEFAULT ''   AFTER dept_id"),
        ("created_at", "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
    ]

    for col_name, col_def in migrations:
        if col_name not in existing_cols:
            cursor.execute(
                f"ALTER TABLE `{TABLE_NAME}` ADD COLUMN `{col_name}` {col_def}"
            )

    conn.commit()
    cursor.close()
    conn.close()


# ── CRUD ─────────────────────────────────────────────

def insert_employee(data: dict):
    conn   = get_connection()
    cursor = conn.cursor()
    sql = f"""INSERT INTO `{TABLE_NAME}`
              (emp_name, age, phone, aadhar, salary, place, dept_id, email)
              VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
    cursor.execute(sql, (
        data["name"], data["age"], data["phone"], data["aadhar"],
        data["salary"], data["place"], data["dept_id"], data["email"]
    ))
    conn.commit()
    new_id = cursor.lastrowid
    cursor.close(); conn.close()
    return new_id


def update_employee(emp_id: int, data: dict):
    conn   = get_connection()
    cursor = conn.cursor()
    sql = f"""UPDATE `{TABLE_NAME}` SET
              emp_name=%s, age=%s, phone=%s, aadhar=%s,
              salary=%s, place=%s, dept_id=%s, email=%s
              WHERE id=%s"""
    cursor.execute(sql, (
        data["name"], data["age"], data["phone"], data["aadhar"],
        data["salary"], data["place"], data["dept_id"], data["email"],
        emp_id
    ))
    conn.commit()
    cursor.close(); conn.close()


def delete_employee(emp_id: int):
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM `{TABLE_NAME}` WHERE id=%s", (emp_id,))
    conn.commit()
    cursor.close(); conn.close()


def fetch_all_employees():
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(f"""SELECT id, emp_name, age, phone, aadhar,
                              salary, place, dept_id, email
                       FROM `{TABLE_NAME}` ORDER BY id DESC""")
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


def search_employees(keyword: str):
    conn   = get_connection()
    cursor = conn.cursor()
    like   = f"%{keyword}%"
    cursor.execute(f"""SELECT id, emp_name, age, phone, aadhar,
                              salary, place, dept_id, email
                       FROM `{TABLE_NAME}`
                       WHERE emp_name LIKE %s OR dept_id LIKE %s
                          OR place LIKE %s OR phone LIKE %s
                       ORDER BY id DESC""", (like, like, like, like))
    rows = cursor.fetchall()
    cursor.close(); conn.close()
    return rows


# ══════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════

COLS      = ("ID","Name","Age","Phone","Aadhar","Salary","Place","Dept ID","Email")
COL_W     = [45, 130, 45, 100, 120, 90, 100, 70, 150]

class EmployeeApp(tk.Tk):
    # ── palette ──────────────────────────────────────
    BG       = "#1e1e2e"
    PANEL    = "#2a2a3e"
    ACCENT   = "#7c6af7"
    ACCENT2  = "#5a4fcf"
    FG       = "#e0e0f0"
    ENTRY_BG = "#13131f"
    SUCCESS  = "#50fa7b"
    ERROR    = "#ff5555"
    WARN     = "#ffb86c"
    BORDER   = "#3a3a5c"

    def __init__(self):
        super().__init__()
        self.title("Employee Management System — CRUD")
        self.geometry("1200x700")
        self.minsize(900, 600)
        self.configure(bg=self.BG)
        self._edit_id = None          # tracks which row is being edited
        self._build_ui()
        self._load_table()

    # ══ UI BUILD ══════════════════════════════════════

    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=self.ACCENT, height=52)
        hdr.pack(fill="x")
        tk.Label(hdr, text="  👤  Employee Management System",
                 font=("Segoe UI", 16, "bold"),
                 bg=self.ACCENT, fg="white", anchor="w", padx=14
                 ).pack(fill="x", pady=10)

        # body
        body = tk.Frame(self, bg=self.BG)
        body.pack(fill="both", expand=True, padx=14, pady=12)

        # left panel (form)
        self.left = tk.Frame(body, bg=self.PANEL, width=270)
        self.left.pack(side="left", fill="y", padx=(0,12))
        self.left.pack_propagate(False)

        # right panel (table)
        right = tk.Frame(body, bg=self.BG)
        right.pack(side="left", fill="both", expand=True)

        self._build_form(self.left)
        self._build_table(right)

    # ── form ─────────────────────────────────────────

    def _lbl(self, p, t):
        tk.Label(p, text=t, bg=self.PANEL, fg=self.FG,
                 font=("Segoe UI", 9), anchor="w"
                 ).pack(fill="x", padx=14, pady=(7,1))

    def _ent(self, p, var, show=""):
        e = tk.Entry(p, textvariable=var, show=show,
                     bg=self.ENTRY_BG, fg=self.FG,
                     insertbackground=self.FG,
                     relief="flat", font=("Segoe UI", 10),
                     bd=0, highlightthickness=2,
                     highlightbackground=self.BORDER,
                     highlightcolor=self.ACCENT)
        e.pack(fill="x", padx=14, ipady=5)
        return e

    def _build_form(self, p):
        # title pinned at top
        top_bar = tk.Frame(p, bg=self.PANEL)
        top_bar.pack(fill="x")
        self.form_title = tk.Label(top_bar, text="➕  Add New Employee",
            bg=self.PANEL, fg=self.ACCENT,
            font=("Segoe UI", 12, "bold"))
        self.form_title.pack(pady=(12,6), padx=14, anchor="w")

        # buttons PINNED at bottom
        btn_area = tk.Frame(p, bg=self.PANEL)
        btn_area.pack(fill="x", side="bottom", pady=(4,8), padx=14)

        self.btn_create = tk.Button(btn_area, text="  ✚  Create",
            command=self._on_create,
            bg=self.ACCENT, fg="white",
            activebackground=self.ACCENT2,
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=7)
        self.btn_create.pack(fill="x", pady=(0,3))

        self.btn_update = tk.Button(btn_area, text="  ✎  Update",
            command=self._on_update,
            bg="#f1a800", fg="#1e1e2e",
            activebackground="#c98900",
            font=("Segoe UI", 10, "bold"),
            relief="flat", cursor="hand2", pady=7,
            state="disabled")
        self.btn_update.pack(fill="x", pady=3)

        self.btn_cancel = tk.Button(btn_area, text="  ✕  Cancel Edit",
            command=self._cancel_edit,
            bg=self.BORDER, fg=self.FG,
            activebackground="#555577",
            font=("Segoe UI", 10),
            relief="flat", cursor="hand2", pady=7,
            state="disabled")
        self.btn_cancel.pack(fill="x", pady=3)

        tk.Button(btn_area, text="  ⌫  Clear Form",
            command=self._clear_form,
            bg="#3a3a5c", fg=self.FG,
            activebackground="#555577",
            font=("Segoe UI", 10),
            relief="flat", cursor="hand2", pady=7
            ).pack(fill="x", pady=(3,0))

        # scrollable fields area in the middle
        scroll_frame = tk.Frame(p, bg=self.PANEL)
        scroll_frame.pack(fill="both", expand=True)

        canvas = tk.Canvas(scroll_frame, bg=self.PANEL, highlightthickness=0)
        sb     = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        fi     = tk.Frame(canvas, bg=self.PANEL)

        fi.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=fi, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        fields = [
            ("Employee Name",    "v_name"),
            ("Age",              "v_age"),
            ("Phone Number",     "v_phone"),
            ("Aadhar Card No.",  "v_aadhar"),
            ("Salary (₹)",       "v_salary"),
            ("Place",            "v_place"),
            ("Department ID",    "v_dept"),
            ("Email Address",    "v_email"),
        ]
        for label, attr in fields:
            setattr(self, attr, tk.StringVar())
            self._lbl(fi, label)
            self._ent(fi, getattr(self, attr))

        self.status_var = tk.StringVar()
        self.status_lbl = tk.Label(fi, textvariable=self.status_var,
            bg=self.PANEL, fg=self.SUCCESS,
            font=("Segoe UI", 9, "italic"), wraplength=230)
        self.status_lbl.pack(pady=(6,4), padx=14)

    # ── table ────────────────────────────────────────

    def _build_table(self, p):
        # toolbar
        tb = tk.Frame(p, bg=self.BG)
        tb.pack(fill="x", pady=(0,8))

        tk.Label(tb, text="Employee Records",
                 bg=self.BG, fg=self.ACCENT,
                 font=("Segoe UI", 13, "bold")
                 ).pack(side="left")

        # search
        self.v_search = tk.StringVar()
        se = tk.Entry(tb, textvariable=self.v_search,
                      bg=self.ENTRY_BG, fg=self.FG,
                      insertbackground=self.FG,
                      relief="flat", font=("Segoe UI", 10),
                      bd=0, highlightthickness=2,
                      highlightbackground=self.BORDER,
                      highlightcolor=self.ACCENT,
                      width=22)
        se.pack(side="right", ipady=4, padx=(4,0))
        se.bind("<KeyRelease>", lambda e: self._on_search())
        tk.Label(tb, text="🔍 Search:",
                 bg=self.BG, fg=self.FG,
                 font=("Segoe UI", 9)
                 ).pack(side="right", padx=(8,2))

        tk.Button(tb, text="⟳ Refresh",
            command=self._load_table,
            bg=self.PANEL, fg=self.FG,
            activebackground=self.BORDER,
            font=("Segoe UI", 9),
            relief="flat", cursor="hand2",
            padx=8, pady=3
            ).pack(side="right", padx=(0,8))

        # delete button in toolbar
        tk.Button(tb, text="🗑  Delete Selected",
            command=self._on_delete,
            bg="#ff5555", fg="white",
            activebackground="#cc3333",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2",
            padx=8, pady=3
            ).pack(side="right", padx=(0,4))

        # edit button in toolbar
        tk.Button(tb, text="✎  Edit Selected",
            command=self._on_edit_selected,
            bg="#f1a800", fg="#1e1e2e",
            activebackground="#c98900",
            font=("Segoe UI", 9, "bold"),
            relief="flat", cursor="hand2",
            padx=8, pady=3
            ).pack(side="right", padx=(0,4))

        # treeview
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("E.Treeview",
            background=self.PANEL, foreground=self.FG,
            fieldbackground=self.PANEL, rowheight=26,
            font=("Segoe UI", 9))
        style.configure("E.Treeview.Heading",
            background=self.ACCENT, foreground="white",
            font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("E.Treeview",
            background=[("selected", self.ACCENT2)],
            foreground=[("selected", "white")])

        frame = tk.Frame(p, bg=self.BG)
        frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(frame, columns=COLS,
            show="headings", style="E.Treeview", selectmode="browse")
        for col, w in zip(COLS, COL_W):
            self.tree.heading(col, text=col,
                command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=w, anchor="center", minwidth=40)

        xsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        vsb = ttk.Scrollbar(frame, orient="vertical",   command=self.tree.yview)
        self.tree.configure(xscrollcommand=xsb.set, yscrollcommand=vsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        xsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        # double-click to edit
        self.tree.bind("<Double-1>", lambda e: self._on_edit_selected())

        # row count label
        self.count_var = tk.StringVar(value="")
        tk.Label(p, textvariable=self.count_var,
                 bg=self.BG, fg="#888", font=("Segoe UI", 8)
                 ).pack(anchor="e", pady=(4,0))

    # ══ ACTIONS ═══════════════════════════════════════

    def _collect_form(self):
        """Validate and return a dict, or None on error."""
        name   = self.v_name.get().strip()
        age    = self.v_age.get().strip()
        phone  = self.v_phone.get().strip()
        aadhar = self.v_aadhar.get().strip()
        salary = self.v_salary.get().strip()
        place  = self.v_place.get().strip()
        dept   = self.v_dept.get().strip()
        email  = self.v_email.get().strip()

        if not all([name, age, phone, aadhar, salary, place, dept, email]):
            messagebox.showwarning("Missing Fields",
                "All 8 fields are required. Please fill every field.")
            return None

        try:
            age_v = int(age)
            if not (18 <= age_v <= 80):
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Age", "Age must be a whole number between 18 and 80.")
            return None

        if not phone.isdigit() or len(phone) != 10:
            messagebox.showerror("Invalid Phone",
                "Phone number must be exactly 10 digits.")
            return None

        if not aadhar.isdigit() or len(aadhar) != 12:
            messagebox.showerror("Invalid Aadhar",
                "Aadhar card number must be exactly 12 digits.")
            return None

        try:
            sal_v = float(salary)
            if sal_v < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Salary",
                "Salary must be a positive number (e.g. 45000).")
            return None

        if "@" not in email or "." not in email.split("@")[-1]:
            messagebox.showerror("Invalid Email",
                "Please enter a valid email address.")
            return None

        return dict(name=name, age=age_v, phone=phone, aadhar=aadhar,
                    salary=sal_v, place=place, dept_id=dept, email=email)

    # ── Create ────────────────────────────────────────
    def _on_create(self):
        data = self._collect_form()
        if data is None:
            return
        try:
            new_id = insert_employee(data)
            messagebox.showinfo("Success",
                f"✅  Database created!\n\nEmployee record saved successfully.\nEmployee ID: {new_id}")
            self._set_status(f"✔ Record #{new_id} saved.", self.SUCCESS)
            self._clear_form()
            self._load_table()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not save record:\n\n{e}")
            self._set_status("✘ Save failed.", self.ERROR)

    # ── Edit (load into form) ─────────────────────────
    def _on_edit_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                "Please click a row in the table to edit.")
            return
        row = self.tree.item(sel[0])["values"]
        # row: ID, Name, Age, Phone, Aadhar, Salary, Place, Dept, Email
        self._edit_id = row[0]
        self.v_name.set(row[1])
        self.v_age.set(row[2])
        self.v_phone.set(row[3])
        self.v_aadhar.set(row[4])
        self.v_salary.set(str(row[5]).replace("₹","").replace(",","").strip())
        self.v_place.set(row[6])
        self.v_dept.set(row[7])
        self.v_email.set(row[8])

        self.form_title.config(text=f"✎  Editing ID #{self._edit_id}")
        self.btn_create.config(state="disabled")
        self.btn_update.config(state="normal")
        self.btn_cancel.config(state="normal")
        self._set_status(f"Editing employee #{self._edit_id}", self.WARN)

    # ── Update ────────────────────────────────────────
    def _on_update(self):
        if self._edit_id is None:
            return
        data = self._collect_form()
        if data is None:
            return
        try:
            update_employee(self._edit_id, data)
            messagebox.showinfo("Updated",
                f"✅  Employee #{self._edit_id} updated successfully!")
            self._set_status(f"✔ Record #{self._edit_id} updated.", self.SUCCESS)
            self._cancel_edit()
            self._load_table()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not update record:\n\n{e}")
            self._set_status("✘ Update failed.", self.ERROR)

    # ── Delete ────────────────────────────────────────
    def _on_delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                "Please click a row in the table to delete.")
            return
        row    = self.tree.item(sel[0])["values"]
        emp_id = row[0]
        name   = row[1]
        confirm = messagebox.askyesno("Confirm Delete",
            f"Are you sure you want to delete:\n\n  🧑 {name}  (ID #{emp_id})?\n\nThis cannot be undone.")
        if not confirm:
            return
        try:
            delete_employee(emp_id)
            messagebox.showinfo("Deleted",
                f"🗑  Employee '{name}' (ID #{emp_id}) deleted.")
            self._set_status(f"✔ Record #{emp_id} deleted.", self.SUCCESS)
            self._cancel_edit()
            self._load_table()
        except Error as e:
            messagebox.showerror("Database Error", f"Could not delete record:\n\n{e}")
            self._set_status("✘ Delete failed.", self.ERROR)

    # ── Search ────────────────────────────────────────
    def _on_search(self):
        kw = self.v_search.get().strip()
        if kw:
            rows = search_employees(kw)
        else:
            rows = fetch_all_employees()
        self._populate_table(rows)

    # ── helpers ───────────────────────────────────────
    def _cancel_edit(self):
        self._edit_id = None
        self.form_title.config(text="➕  Add New Employee")
        self.btn_create.config(state="normal")
        self.btn_update.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self._clear_form()
        self._set_status("", self.SUCCESS)

    def _clear_form(self):
        for attr in ("v_name","v_age","v_phone","v_aadhar",
                     "v_salary","v_place","v_dept","v_email"):
            getattr(self, attr).set("")

    def _set_status(self, msg, color):
        self.status_var.set(msg)
        self.status_lbl.config(fg=color)

    def _load_table(self):
        rows = fetch_all_employees()
        self._populate_table(rows)

    def _populate_table(self, rows):
        for r in self.tree.get_children():
            self.tree.delete(r)
        for r in rows:
            self.tree.insert("", "end", values=(
                r[0], r[1], r[2], r[3], r[4],
                f"₹{float(r[5]):,.2f}", r[6], r[7], r[8]
            ))
        n = len(rows)
        self.count_var.set(f"{n} record{'s' if n != 1 else ''} found")

    _sort_order = {}
    def _sort_col(self, col):
        items = [(self.tree.set(k, col), k) for k in self.tree.get_children("")]
        rev   = self._sort_order.get(col, False)
        try:
            items.sort(key=lambda t: float(t[0].replace("₹","").replace(",","")), reverse=rev)
        except ValueError:
            items.sort(reverse=rev)
        for i, (_, k) in enumerate(items):
            self.tree.move(k, "", i)
        self._sort_order[col] = not rev


# ══════════════════════════════════════════════════════
#  ENTRY POINT
# ══════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        setup_database()
    except Error as err:
        import sys
        root = tk.Tk(); root.withdraw()
        messagebox.showerror("Connection Failed",
            f"Cannot connect to MySQL.\n\nEdit DB_CONFIG at top of file.\n\nError: {err}")
        sys.exit(1)

    app = EmployeeApp()
    app.mainloop()