import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import pandas as pd

# ----------------------- DATABASE SETUP -----------------------
def init_db():
    conn = sqlite3.connect("donor_ai.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS donors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    blood_group TEXT,
                    organ TEXT,
                    contact TEXT,
                    address TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS hospitals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    contact TEXT,
                    address TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS emergency_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hospital_id INTEGER,
                    request_type TEXT,
                    location TEXT,
                    timestamp TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    action TEXT,
                    details TEXT,
                    timestamp TEXT
                )''')
    conn.commit()
    conn.close()

def add_log(action, details):
    conn = sqlite3.connect("donor_ai.db")
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (action, details, timestamp) VALUES (?, ?, ?)",
              (action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# ----------------------- FUNCTIONS -----------------------
def register_hospital():
    def save_hospital():
        name, contact, address = name_var.get(), contact_var.get(), address_var.get("1.0", "end").strip()
        if name and contact and address:
            conn = sqlite3.connect("donor_ai.db")
            c = conn.cursor()
            c.execute("INSERT INTO hospitals (name, contact, address) VALUES (?, ?, ?)", (name, contact, address))
            conn.commit()
            conn.close()
            add_log("Hospital Registered", f"{name} - {contact}")
            messagebox.showinfo("Success", "Hospital registered successfully!")
            top.destroy()
        else:
            messagebox.showwarning("Warning", "All fields are required!")

    top = tk.Toplevel(root)
    top.title("Register Hospital")
    tk.Label(top, text="Hospital Name").pack()
    name_var = tk.Entry(top)
    name_var.pack()
    tk.Label(top, text="Contact Number").pack()
    contact_var = tk.Entry(top)
    contact_var.pack()
    tk.Label(top, text="Address").pack()
    address_var = tk.Text(top, height=3, width=30)
    address_var.pack()
    tk.Button(top, text="Register", command=save_hospital).pack(pady=5)

def register_donor():
    def save_donor():
        name, contact, address = name_var.get(), contact_var.get(), address_var.get("1.0", "end").strip()
        blood_group, organ = blood_group_var.get(), organ_var.get()
        if name and contact and address:
            conn = sqlite3.connect("donor_ai.db")
            c = conn.cursor()
            c.execute("INSERT INTO donors (name, blood_group, organ, contact, address) VALUES (?, ?, ?, ?, ?)",
                      (name, blood_group, organ, contact, address))
            conn.commit()
            conn.close()
            add_log("Donor Registered", f"{name} ({blood_group}) from {address}")
            messagebox.showinfo("Success", "Donor registered successfully!")
            top.destroy()
        else:
            messagebox.showwarning("Warning", "All fields are required!")

    top = tk.Toplevel(root)
    top.title("Register Donor")
    tk.Label(top, text="Donor Name").pack()
    name_var = tk.Entry(top)
    name_var.pack()
    tk.Label(top, text="Blood Group").pack()
    blood_group_var = ttk.Combobox(top, values=["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"])
    blood_group_var.pack()
    tk.Label(top, text="Organ Donating").pack()
    organ_var = ttk.Combobox(top, values=["Blood", "Kidney", "Liver", "Heart", "Lungs", "Eyes", "Other"])
    organ_var.pack()
    tk.Label(top, text="Contact Number").pack()
    contact_var = tk.Entry(top)
    contact_var.pack()
    tk.Label(top, text="Address (Area / City)").pack()
    address_var = tk.Text(top, height=3, width=30)
    address_var.pack()
    tk.Button(top, text="Register", command=save_donor).pack(pady=5)

def emergency_request():
    def submit_request():
        hospital_name, request_type, location = hospital_var.get(), request_type_var.get(), location_var.get()
        if not hospital_name or not location:
            messagebox.showwarning("Warning", "Please fill all fields!")
            return
        hospital_id = hospitals[hospitals["name"] == hospital_name]["id"].iloc[0]
        conn = sqlite3.connect("donor_ai.db")
        c = conn.cursor()
        c.execute("INSERT INTO emergency_requests (hospital_id, request_type, location, timestamp) VALUES (?, ?, ?, ?)",
                  (hospital_id, request_type, location, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
        add_log("Emergency Request", f"{request_type} emergency at {location} by {hospital_name}")
        messagebox.showinfo("Request", "Emergency request submitted successfully!")

        # Find donors
        conn = sqlite3.connect("donor_ai.db")
        query = "SELECT * FROM donors WHERE address LIKE ? AND organ LIKE ?"
        df = pd.read_sql_query(query, conn, params=(f"%{location}%", f"%{request_type}%"))
        conn.close()

        if not df.empty:
            result_window = tk.Toplevel(top)
            result_window.title("Matching Donors Found")
            cols = list(df.columns)
            tree = ttk.Treeview(result_window, columns=cols, show="headings")
            for col in cols:
                tree.heading(col, text=col)
            for _, row in df.iterrows():
                tree.insert("", "end", values=list(row))
            tree.pack(expand=True, fill="both")
        else:
            messagebox.showerror("No Match", "No donors found near this area.")

    conn = sqlite3.connect("donor_ai.db")
    hospitals = pd.read_sql_query("SELECT id, name FROM hospitals", conn)
    conn.close()
    if hospitals.empty:
        messagebox.showwarning("No Hospitals", "Please register a hospital first!")
        return

    top = tk.Toplevel(root)
    top.title("Emergency Request")
    tk.Label(top, text="Select Hospital").pack()
    hospital_var = ttk.Combobox(top, values=hospitals["name"].tolist())
    hospital_var.pack()
    tk.Label(top, text="Request Type").pack()
    request_type_var = ttk.Combobox(top, values=["Blood", "Organ"])
    request_type_var.pack()
    tk.Label(top, text="Emergency Location (Area / City)").pack()
    location_var = tk.Entry(top)
    location_var.pack()
    tk.Button(top, text="Submit Request", command=submit_request).pack(pady=5)

def view_donors():
    top = tk.Toplevel(root)
    top.title("All Registered Donors")
    conn = sqlite3.connect("donor_ai.db")
    df = pd.read_sql_query("SELECT * FROM donors", conn)
    conn.close()
    cols = list(df.columns)
    tree = ttk.Treeview(top, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(expand=True, fill="both")

def view_logs():
    top = tk.Toplevel(root)
    top.title("Audit Logs")
    conn = sqlite3.connect("donor_ai.db")
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY id DESC", conn)
    conn.close()
    cols = list(df.columns)
    tree = ttk.Treeview(top, columns=cols, show="headings")
    for col in cols:
        tree.heading(col, text=col)
    for _, row in df.iterrows():
        tree.insert("", "end", values=list(row))
    tree.pack(expand=True, fill="both")

# ----------------------- MAIN GUI -----------------------
root = tk.Tk()
root.title("🩸 AI-Based Donor Management System")
root.geometry("600x400")

init_db()

tk.Label(root, text="AI Donor Connect", font=("Arial", 18, "bold"), fg="red").pack(pady=10)

tk.Button(root, text="🏥 Register Hospital", command=register_hospital, width=30, bg="#cfe2f3").pack(pady=5)
tk.Button(root, text="🩸 Register Donor", command=register_donor, width=30, bg="#f4cccc").pack(pady=5)
tk.Button(root, text="🚨 Emergency Request", command=emergency_request, width=30, bg="#ffe599").pack(pady=5)
tk.Button(root, text="📋 View Donors", command=view_donors, width=30, bg="#d9ead3").pack(pady=5)
tk.Button(root, text="📘 View Audit Logs", command=view_logs, width=30, bg="#d0e0e3").pack(pady=5)
tk.Button(root, text="Exit", command=root.destroy, width=30, bg="#ead1dc").pack(pady=10)

root.mainloop()
