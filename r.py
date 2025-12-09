import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
from tkcalendar import DateEntry
import datetime

DATA_FILE = "appointments.json"
appointments = []

# Weekdays (Mon-Fri)
ALLOWED_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
ALLOWED_TIMES = [
    "08:30 AM", "09:00 AM", "09:30 AM",
    "10:00 AM", "10:30 AM", "11:00 AM", "11:30 AM",
    "01:00 PM", "01:30 PM", "02:00 PM", "02:30 PM", "03:00 PM"
]

# Simple theme colors
PRIMARY = "#1E88E5"
PRIMARY_DARK = "#1669b2"
BG = "#F4F8FB"
CARD = "#FFFFFF"
TEXT = "#0B2545"

# Keep references to dynamic UI pieces for refresh
_main_stats_vars = {}
_view_window = None
_view_search_var = None
_view_card_container = None

# ---------------------- Data Persistence ---------------------- #
def load_data():
    global appointments
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                appointments = json.load(f)
        except Exception:
            appointments = []
    else:
        appointments = []

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(appointments, f, indent=4, ensure_ascii=False)

# ---------------------- UI Helpers / Theme ---------------------- #
def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    root.configure(bg=BG)
    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD, relief="raised")
    style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), background=BG, foreground=TEXT)
    style.configure("TLabel", background=BG, foreground=TEXT, font=("Segoe UI", 10))
    style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"))
    style.map("Accent.TButton",
              background=[("active", PRIMARY_DARK), ("!disabled", PRIMARY)],
              foreground=[("!disabled", "white")])
    style.configure("Outline.TButton", relief="flat", background=BG)
    style.configure("CardTitle.TLabel", font=("Segoe UI", 11, "bold"), background=CARD, foreground=TEXT)
    style.configure("Small.TLabel", font=("Segoe UI", 9), background=CARD, foreground=TEXT)
    style.configure("TEntry", padding=4)

# ---------------------- Utility ---------------------- #
def date_to_day(date_str):
    try:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%A")
    except Exception:
        return ""

def validate_allowed_date(date_str):
    d = date_to_day(date_str)
    return d in ALLOWED_DAYS

def find_appointment_index(app):
    for i, a in enumerate(appointments):
        if a is app:
            return i
    # fallback try matching unique combo
    for i, a in enumerate(appointments):
        if (a.get("name") == app.get("name") and a.get("date") == app.get("date")
                and a.get("time") == app.get("time")):
            return i
    return None

# ---------------------- Add Appointment ---------------------- #
def add_appointment(entries, refresh_main=True):
    data = {
        "name": entries["name"].get().strip(),
        "address": entries["address"].get().strip(),
        "contact": entries["contact"].get().strip(),
        "age": entries["age"].get().strip(),
        "date": entries["date"].get().strip(),
        # day will be computed from date to avoid mismatch
        "time": entries["time"].get().strip(),
        "purpose": entries["purpose"].get().strip(),
    }

    # Validation
    if any(v == "" for v in data.values()):
        return messagebox.showerror("Error", "Please fill all fields.")
    if not data["age"].isdigit():
        return messagebox.showerror("Error", "Age must be a number.")

    # Validate date/day
    if not validate_allowed_date(data["date"]):
        return messagebox.showerror(
            "Invalid Day",
            f"Appointments allowed only on weekdays: {', '.join(ALLOWED_DAYS)}."
        )
    data["day"] = date_to_day(data["date"])

    # Prevent exact duplicates (same name + date + time)
    for app in appointments:
        if (app.get("name") == data["name"] and app.get("date") == data["date"]
                and app.get("time") == data["time"]):
            return messagebox.showerror("Error", "An appointment with the same name, date and time already exists.")

    appointments.append(data)
    save_data()
    messagebox.showinfo("Success", "Appointment added successfully!")

    # Clear form
    for k, widget in entries.items():
        if isinstance(widget, ttk.Combobox):
            widget.set("")
        elif isinstance(widget, DateEntry):
            # reset to today
            widget.set_date(datetime.date.today())
        else:
            widget.delete(0, tk.END)

    if refresh_main:
        refresh_main_stats()
        refresh_view_window_if_open()

# ---------------------- Edit Appointment ---------------------- #
def open_edit_window(parent, app_obj):
    # modal for editing an appointment
    win = tk.Toplevel(parent)
    win.title("Edit Appointment")
    win.transient(parent)
    win.grab_set()
    win.geometry("420x420")
    win.configure(bg=BG)

    frame = ttk.Frame(win, style="Card.TFrame", padding=12)
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    ttk.Label(frame, text="Edit Appointment", style="Header.TLabel").pack(anchor="w", pady=(0,8))

    form = {}
    def mkrow(label_text, widget):
        row = ttk.Frame(frame, style="TFrame")
        row.pack(fill="x", pady=6)
        ttk.Label(row, text=label_text + ":", width=14).pack(side="left")
        widget.pack(side="left", fill="x", expand=True)
        return widget

    name_e = mkrow("Full Name", tk.Entry(row := ttk.Frame()))  # workaround; replaced below

    # create proper widgets
    for w in frame.winfo_children():
        w.destroy()
    ttk.Label(frame, text="Edit Appointment", style="Header.TLabel").pack(anchor="w", pady=(0,8))

    # Name
    name_ent = tk.Entry(frame, width=36)
    ttk.Label(frame, text="Full Name:").pack(anchor="w")
    name_ent.pack(fill="x", pady=2)

    # Address
    addr_ent = tk.Entry(frame, width=36)
    ttk.Label(frame, text="Address:").pack(anchor="w")
    addr_ent.pack(fill="x", pady=2)

    # Contact
    contact_ent = tk.Entry(frame, width=36)
    ttk.Label(frame, text="Contact Number:").pack(anchor="w")
    contact_ent.pack(fill="x", pady=2)

    # Age
    age_ent = tk.Entry(frame, width=36)
    ttk.Label(frame, text="Age:").pack(anchor="w")
    age_ent.pack(fill="x", pady=2)

    # Date
    date_ent = DateEntry(frame, date_pattern="yyyy-mm-dd", width=20)
    ttk.Label(frame, text="Date:").pack(anchor="w")
    date_ent.pack(fill="x", pady=2)

    # Time
    time_cb = ttk.Combobox(frame, values=ALLOWED_TIMES, state="readonly", width=34)
    ttk.Label(frame, text="Time:").pack(anchor="w")
    time_cb.pack(fill="x", pady=2)

    # Purpose
    purpose_ent = tk.Entry(frame, width=36)
    ttk.Label(frame, text="Purpose:").pack(anchor="w")
    purpose_ent.pack(fill="x", pady=2)

    # prefill
    name_ent.insert(0, app_obj.get("name", ""))
    addr_ent.insert(0, app_obj.get("address", ""))
    contact_ent.insert(0, app_obj.get("contact", ""))
    age_ent.insert(0, app_obj.get("age", ""))
    try:
        date_ent.set_date(datetime.datetime.strptime(app_obj.get("date"), "%Y-%m-%d").date())
    except Exception:
        pass
    time_cb.set(app_obj.get("time", ""))
    purpose_ent.insert(0, app_obj.get("purpose", ""))

    def save_changes():
        new_data = {
            "name": name_ent.get().strip(),
            "address": addr_ent.get().strip(),
            "contact": contact_ent.get().strip(),
            "age": age_ent.get().strip(),
            "date": date_ent.get().strip(),
            "time": time_cb.get().strip(),
            "purpose": purpose_ent.get().strip(),
        }
        if any(v == "" for v in new_data.values()):
            return messagebox.showerror("Error", "Please fill all fields.")
        if not new_data["age"].isdigit():
            return messagebox.showerror("Error", "Age must be a number.")
        if not validate_allowed_date(new_data["date"]):
            return messagebox.showerror("Invalid Day", f"Appointments allowed only on weekdays: {', '.join(ALLOWED_DAYS)}.")
        new_data["day"] = date_to_day(new_data["date"])

        # check for collision with other appointments
        for other in appointments:
            if other is app_obj:
                continue
            if (other.get("name") == new_data["name"] and other.get("date") == new_data["date"]
                    and other.get("time") == new_data["time"]):
                return messagebox.showerror("Error", "Another appointment with same name/date/time exists.")

        # apply changes
        idx = find_appointment_index(app_obj)
        if idx is not None:
            appointments[idx] = new_data
            save_data()
            messagebox.showinfo("Saved", "Appointment updated.")
            win.destroy()
            refresh_main_stats()
            refresh_view_window_if_open()
        else:
            messagebox.showerror("Error", "Failed to locate appointment to update.")

    def cancel_this():
        # allow cancellation from edit modal too
        if messagebox.askyesno("Confirm Cancel", "Cancel (delete) this appointment?"):
            idx = find_appointment_index(app_obj)
            if idx is not None:
                appointments.pop(idx)
                save_data()
                messagebox.showinfo("Cancelled", "Appointment deleted.")
                win.destroy()
                refresh_main_stats()
                refresh_view_window_if_open()
            else:
                messagebox.showerror("Error", "Failed to locate appointment to delete.")

    btn_frame = ttk.Frame(frame, style="TFrame")
    btn_frame.pack(fill="x", pady=(12,0))
    ttk.Button(btn_frame, text="Save Changes", style="Accent.TButton", command=save_changes).pack(side="left", padx=(0,6))
    ttk.Button(btn_frame, text="Cancel Appointment", style="Outline.TButton", command=cancel_this).pack(side="left")
    ttk.Button(btn_frame, text="Close", style="Outline.TButton", command=win.destroy).pack(side="right")

# ---------------------- Cancel Appointment ---------------------- #
def cancel_appointment(parent, app_obj):
    if not messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel this appointment?"):
        return
    idx = find_appointment_index(app_obj)
    if idx is None:
        messagebox.showerror("Error", "Appointment not found.")
        return
    appointments.pop(idx)
    save_data()
    messagebox.showinfo("Cancelled", "Appointment cancelled.")
    refresh_main_stats()
    refresh_view_window_if_open()

# ---------------------- View All (Card Layout) ---------------------- #
def open_view_all(parent):
    global _view_window, _view_search_var, _view_card_container
    if _view_window is not None and tk.Toplevel.winfo_exists(_view_window):
        _view_window.lift()
        return

    _view_window = tk.Toplevel(parent)
    _view_window.title("All Appointments — Card View")
    _view_window.geometry("880x520")
    _view_window.configure(bg=BG)

    top_frame = ttk.Frame(_view_window, padding=10, style="TFrame")
    top_frame.pack(fill="x", padx=10, pady=(10,0))

    ttk.Label(top_frame, text="Appointments", style="Header.TLabel").pack(side="left")
    # Search
    _view_search_var = tk.StringVar()
    search_entry = ttk.Entry(top_frame, textvariable=_view_search_var, width=36)
    search_entry.pack(side="left", padx=(12,6))
    search_entry.insert(0, "Search by name, date (YYYY-MM-DD) or purpose...")
    # clear placeholder on focus
    def on_focus_in(e):
        if search_entry.get().startswith("Search by"):
            search_entry.delete(0, tk.END)
    def on_focus_out(e):
        if search_entry.get().strip() == "":
            search_entry.insert(0, "Search by name, date (YYYY-MM-DD) or purpose...")
    search_entry.bind("<FocusIn>", on_focus_in)
    search_entry.bind("<FocusOut>", on_focus_out)

    def on_search_change(*_):
        refresh_view_cards()
    _view_search_var.trace_add("write", lambda *a: on_search_change())

    ttk.Button(top_frame, text="Refresh", style="Outline.TButton", command=refresh_view_cards).pack(side="right")

    # Scrollable area for cards
    canvas_frame = ttk.Frame(_view_window, style="TFrame")
    canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)

    canvas = tk.Canvas(canvas_frame, bg=BG, highlightthickness=0)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)

    inner = ttk.Frame(canvas, style="TFrame")
    canvas.create_window((0,0), window=inner, anchor="nw")

    def _on_mousewheel(event):
        canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    # bind scroll
    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>", _on_mousewheel)

    _view_card_container = inner

    refresh_view_cards()

def refresh_view_cards():
    """Rebuild cards inside the view window according to search filter."""
    global _view_window, _view_card_container, _view_search_var
    if _view_window is None or not tk.Toplevel.winfo_exists(_view_window):
        return

    container = _view_card_container
    # clear current cards
    for w in container.winfo_children():
        w.destroy()

    q = (_view_search_var.get().strip() if _view_search_var else "").lower()
    def matches(app):
        if not q or q.startswith("search by"):
            return True
        return (
            q in (app.get("name","").lower()) or
            q in (app.get("date","").lower()) or
            q in (app.get("purpose","").lower())
        )

    # sort appointments by date then time
    def sort_key(a):
        try:
            dt = datetime.datetime.strptime(a.get("date","1970-01-01"), "%Y-%m-%d")
        except Exception:
            dt = datetime.datetime(1970,1,1)
        # simple time parsing for sorting
        t = a.get("time","")
        return (dt, t)
    visible = [a for a in sorted(appointments, key=sort_key) if matches(a)]

    if not visible:
        ttk.Label(container, text="No appointments found.", background=BG).pack(pady=8)
        return

    for idx, app in enumerate(visible):
        card = ttk.Frame(container, style="Card.TFrame", padding=10)
        card.pack(fill="x", pady=8, padx=6)

        top = ttk.Frame(card, style="Card.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text=app.get("name",""), style="CardTitle.TLabel").pack(side="left")
        ttk.Label(top, text=f"{app.get('date','')} ({app.get('day','')}) • {app.get('time','')}", style="Small.TLabel").pack(side="right")

        mid = ttk.Frame(card, style="Card.TFrame")
        mid.pack(fill="x", pady=(6,4))
        ttk.Label(mid, text=f"Address: {app.get('address','')}", style="Small.TLabel").pack(anchor="w")
        ttk.Label(mid, text=f"Contact: {app.get('contact','')}    Age: {app.get('age','')}", style="Small.TLabel").pack(anchor="w")
        ttk.Label(mid, text=f"Purpose: {app.get('purpose','')}", style="Small.TLabel").pack(anchor="w")

        btns = ttk.Frame(card, style="Card.TFrame")
        btns.pack(fill="x", pady=(6,0))
        ttk.Button(btns, text="Edit", style="Accent.TButton", command=lambda a=app: open_edit_window(_view_window, a)).pack(side="left")
        ttk.Button(btns, text="Cancel", style="Outline.TButton", command=lambda a=app: cancel_from_view(a)).pack(side="left", padx=(6,0))
        # small spacer
        ttk.Label(btns, text="").pack(side="left", expand=True)
        # index label (optional)
        ttk.Label(btns, text=f"#{idx+1}", style="Small.TLabel").pack(side="right")

def cancel_from_view(app):
    cancel_appointment(_view_window if _view_window else None, app)

def refresh_view_window_if_open():
    global _view_window
    if _view_window is not None and tk.Toplevel.winfo_exists(_view_window):
        refresh_view_cards()

# ---------------------- Analytics / Stats ---------------------- #
def open_analytics(parent):
    win = tk.Toplevel(parent)
    win.title("Analytics")
    win.geometry("420x360")
    win.configure(bg=BG)

    frame = ttk.Frame(win, style="Card.TFrame", padding=12)
    frame.pack(fill="both", expand=True, padx=12, pady=12)

    ttk.Label(frame, text="📊 Appointment Analytics", style="Header.TLabel").pack(anchor="w", pady=(0,8))

    # totals by weekday
    day_count = {d: 0 for d in ALLOWED_DAYS}
    upcoming = []
    today = datetime.date.today()
    for app in appointments:
        d = app.get("day")
        if d in day_count:
            day_count[d] += 1
        # upcoming next 7 days
        try:
            dt = datetime.datetime.strptime(app.get("date",""), "%Y-%m-%d").date()
            if dt >= today and dt <= (today + datetime.timedelta(days=7)):
                upcoming.append((dt, app))
        except Exception:
            pass

    ttk.Label(frame, text=f"Total Appointments: {len(appointments)}", font=("Segoe UI", 11)).pack(anchor="w", pady=(0,6))

    for d in ALLOWED_DAYS:
        ttk.Label(frame, text=f"• {d}: {day_count[d]}", font=("Segoe UI", 10)).pack(anchor="w", padx=6)

    ttk.Label(frame, text="Upcoming (next 7 days):", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8,0))
    if upcoming:
        upcoming.sort(key=lambda x: x[0])
        for dt, app in upcoming[:6]:
            ttk.Label(frame, text=f"{dt.isoformat()} — {app.get('name')} ({app.get('time')})", font=("Segoe UI", 9)).pack(anchor="w", padx=8)
    else:
        ttk.Label(frame, text="No upcoming appointments in next 7 days.", font=("Segoe UI", 9)).pack(anchor="w", padx=8)

    ttk.Button(win, text="Close", style="Outline.TButton", command=win.destroy).pack(pady=10)

# ---------------------- Main Application Window ---------------------- #
def build_main_gui():
    load_data()
    root = tk.Tk()
    root.title("Health Check-up Appointment System")
    root.geometry("980x700")
    root.resizable(False, False)
    setup_style(root)

    # Header
    header = ttk.Frame(root, padding=(18,10), style="TFrame")
    header.pack(fill="x", padx=16, pady=(12,6))

    ttk.Label(header, text="Health Check-up Appointment", style="Header.TLabel").pack(side="left", padx=(6,0))
    ttk.Label(header, text="Manage appointments simply and quickly", font=("Segoe UI", 10), background=BG).pack(side="left", padx=(12,0))

    # Content area: left form, right quick cards & actions
    content = ttk.Frame(root, padding=(16,12))
    content.pack(fill="both", expand=True, padx=16, pady=6)

    # Left: Form Card
    form_card = ttk.Frame(content, style="Card.TFrame", padding=14)
    form_card.grid(row=0, column=0, sticky="nsew", padx=(0,12), pady=6)
    content.columnconfigure(0, weight=2)

    ttk.Label(form_card, text="Add New Appointment", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0,8))

    labels = [
        ("Full Name", "name"),
        ("Address", "address"),
        ("Contact Number", "contact"),
        ("Age", "age"),
        ("Date", "date"),
        ("Time", "time"),
        ("Purpose", "purpose"),
    ]

    entries = {}
    row = 1
    for lbl, key in labels:
        ttk.Label(form_card, text=f"{lbl}:").grid(row=row, column=0, sticky="w", pady=6)
        if key == "time":
            w = ttk.Combobox(form_card, values=ALLOWED_TIMES, state="readonly", width=28)
            w.grid(row=row, column=1, sticky="w")
        elif key == "date":
            w = DateEntry(form_card, date_pattern="yyyy-mm-dd", width=26)
            w.grid(row=row, column=1, sticky="w")
        else:
            w = tk.Entry(form_card, width=30)
            w.grid(row=row, column=1, sticky="w")
        entries[key] = w
        row += 1

    # date -> day auto hint label
    day_hint = ttk.Label(form_card, text="Allowed days: Mon–Fri. Day will be set from date.", font=("Segoe UI", 9))
    day_hint.grid(row=row, column=0, columnspan=2, sticky="w", pady=(6,0))

    add_btn = ttk.Button(form_card, text="Add Appointment", style="Accent.TButton", command=lambda: add_appointment(entries))
    add_btn.grid(row=row+1, column=0, columnspan=2, pady=(12,0))

    # Right: Quick Actions & Info
    right_card = ttk.Frame(content, style="Card.TFrame", padding=14)
    right_card.grid(row=0, column=1, sticky="nsew", padx=(12,0), pady=6)
    content.columnconfigure(1, weight=1)

    ttk.Label(right_card, text="Quick Actions", font=("Segoe UI", 11, "bold")).pack(anchor="w")
    ttk.Button(right_card, text="View All Appointments", style="Accent.TButton", command=lambda: open_view_all(root)).pack(fill="x", pady=(8,6))
    ttk.Button(right_card, text="Analytics", style="Accent.TButton", command=lambda: open_analytics(root)).pack(fill="x", pady=(0,8))

    # small stats card
    stats_frame = ttk.Frame(right_card, padding=10, style="Card.TFrame")
    stats_frame.pack(fill="x", pady=(8,6))
    ttk.Label(stats_frame, text="Appointments Summary", font=("Segoe UI", 10, "bold")).pack(anchor="w")

    # compute totals by day and add labels to be updated
    for d in ALLOWED_DAYS:
        var = tk.StringVar(value=f"{d}: 0")
        _main_stats_vars[d] = var
        ttk.Label(stats_frame, textvariable=var, font=("Segoe UI", 10)).pack(anchor="w", padx=6)

    refresh_main_stats()

    # footer
    footer = ttk.Frame(root, padding=8)
    footer.pack(fill="x", padx=16, pady=(8,14))
    ttk.Label(footer, text="Tip: Use the calendar control to choose a date. Allowed days: Mon–Fri", font=("Segoe UI", 9)).pack(side="left")

    root.mainloop()

def refresh_main_stats():
    # update side stats
    day_count = {d: 0 for d in ALLOWED_DAYS}
    for app in appointments:
        d = app.get("day")
        if d in day_count:
            day_count[d] += 1
    for d in ALLOWED_DAYS:
        if d in _main_stats_vars:
            _main_stats_vars[d].set(f"{d}: {day_count[d]}")

#  Welcome Launcher #
def open_main_window():
    welcome.destroy()
    build_main_gui()

welcome = tk.Tk()
welcome.title("Welcome")
welcome.geometry("520x320")
welcome.resizable(False, False)
welcome.configure(bg=BG)
setup_style(welcome)

ttk.Label(welcome, text="Welcome to the Health Check-up", font=("Segoe UI", 18, "bold"), background=BG).pack(pady=(28,6))
ttk.Label(welcome, text="Appointment Management System", font=("Segoe UI", 12), background=BG).pack(pady=(0,12))
ttk.Button(welcome, text="Enter System", style="Accent.TButton", command=open_main_window).pack(pady=(10,6), ipadx=12, ipady=6)

load_data()
welcome.mainloop()
