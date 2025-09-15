# teg_app.py
# TEG Carwash - Generator app (Tkinter). Saves to local SQLite and optionally to Access.
import os, sqlite3, time
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from PIL import Image, ImageTk, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter

# optional Access support
try:
    import pyodbc
    HAVE_PYODBC = True
except Exception:
    HAVE_PYODBC = False

# ---------- Config ----------
OUT_FOLDER = "barcodes"
DB_FILE = "teg.db"
ACCESS_PATH = "TEG.accdb"   # put file here next to exe if you want Access logging
os.makedirs(OUT_FOLDER, exist_ok=True)

# ---------- SQLite init ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS tickets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT,
        created_at TEXT,
        car_type TEXT,
        brand TEXT,
        plate TEXT,
        filename TEXT
    )
    """)
    conn.commit()
    conn.close()

def create_ticket_row_get_id(car_type, brand, plate):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO tickets (token, created_at, car_type, brand, plate, filename) VALUES (?, ?, ?, ?, ?, ?)",
              ("", created_at, car_type, brand, plate, ""))
    conn.commit()
    rowid = c.lastrowid
    conn.close()
    return rowid

def update_ticket_token_and_file(rowid, token, filename):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE tickets SET token = ?, filename = ? WHERE id = ?", (token, filename, rowid))
    conn.commit()
    conn.close()

def insert_ticket_record(token, car_type, brand, plate, filename):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO tickets (token, created_at, car_type, brand, plate, filename) VALUES (?, ?, ?, ?, ?, ?)",
              (token, created_at, car_type, brand, plate, filename))
    conn.commit()
    conn.close()

# ---------- Barcode + ticket image ----------
def make_token_from_id(rowid):
    return f"TEG-{rowid:06d}"

def generate_barcode_image_with_text(token, car_type, brand, plate):
    CODE128 = barcode.get_barcode_class('code128')
    writer = ImageWriter()
    tmp_path = os.path.join(OUT_FOLDER, f"{token}_tmp")
    barcode_obj = CODE128(token, writer=writer)
    barcode_obj.save(tmp_path)  # creates tmp_path + .png
    barcode_png = tmp_path + ".png"

    # open and resize barcode
    img = Image.open(barcode_png).convert("RGB")
    w, h = img.size
    new_w = 800
    new_h = int(h * (new_w / w))
    img = img.resize((new_w, new_h))

    text_lines = [
        f"Token: {token}",
        f"Car type: {car_type}",
        f"Brand: {brand}",
        f"Plate: {plate}",
        f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ]
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except Exception:
        from PIL import ImageFont
        font = ImageFont.load_default()

    draw = ImageDraw.Draw(img)
    line_height = font.getsize("Ay")[1] + 6
    text_area_h = line_height * len(text_lines) + 20
    final = Image.new("RGB", (new_w, new_h + text_area_h), "white")
    final.paste(img, (0, 0))
    draw = ImageDraw.Draw(final)
    y = new_h + 10
    x = 10
    for line in text_lines:
        draw.text((x, y), line, fill="black", font=font)
        y += line_height

    out_filename = os.path.join(OUT_FOLDER, f"{token}.png")
    final.save(out_filename, dpi=(300,300))
    return out_filename

# ---------- Try to log in Access (best-effort) ----------
def try_insert_access(token, car_type, brand, plate, filename):
    if not HAVE_PYODBC:
        return False, "pyodbc not installed"
    if not os.path.exists(ACCESS_PATH):
        return False, "Access DB not found"
    try:
        connstr = r"Driver={Microsoft Access Driver (*.mdb, *.accdb)};DBQ=" + os.path.abspath(ACCESS_PATH) + ";"
        conn = pyodbc.connect(connstr)
        cur = conn.cursor()
        # Adjust columns/table names if your Access schema differs
        cur.execute("INSERT INTO Tickets (Code, Client, CarType, Brand, Plate, CreatedAt, Filename) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (token, "", car_type, brand, plate, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), filename))
        conn.commit()
        conn.close()
        return True, "ok"
    except Exception as e:
        return False, str(e)

# ---------- UI ----------
init_db()

root = tk.Tk()
root.title("TEG Carwash")
root.geometry("820x700")

frm = ttk.Frame(root, padding=12)
frm.pack(fill="both", expand=True)

ttk.Label(frm, text="Car type:").grid(column=0, row=0, sticky="w", pady=6)
combocar = ttk.Combobox(frm, values=["Car","Truck","Motorcycle","Other"], state="readonly")
combocar.grid(column=1, row=0, sticky="w", pady=6)
combocar.set("Car")

ttk.Label(frm, text="Brand:").grid(column=0, row=1, sticky="w", pady=6)
entry_brand = ttk.Entry(frm, width=30)
entry_brand.grid(column=1, row=1, sticky="w", pady=6)

ttk.Label(frm, text="Plate:").grid(column=0, row=2, sticky="w", pady=6)
entry_plate = ttk.Entry(frm, width=30)
entry_plate.grid(column=1, row=2, sticky="w", pady=6)

# Image display area
lbl_status = ttk.Label(frm, text="Ready")
lbl_status.grid(column=0, row=3, columnspan=2, pady=8)
lbl_image = ttk.Label(root)
lbl_image.pack(padx=8, pady=8)

def display_image(filepath, msg):
    try:
        img = Image.open(filepath)
        disp_w = 760
        w, h = img.size
        new_h = int(h * (disp_w / w))
        img_disp = img.resize((disp_w, new_h), Image.ANTIALIAS)
        img_tk = ImageTk.PhotoImage(img_disp)
        lbl_image.config(image=img_tk)
        lbl_image.image = img_tk
        lbl_status.config(text=msg)
    except Exception as e:
        messagebox.showerror("Error", f"Cannot display image: {e}")

def generate_ticket():
    car_type = combocar.get()
    brand = entry_brand.get().strip()
    plate = entry_plate.get().strip()

    if not car_type:
        messagebox.showerror("Error", "Please select car type")
        return

    # create row to get id
    rowid = create_ticket_row_get_id(car_type, brand, plate)
    token = make_token_from_id(rowid)
    filename = generate_barcode_image_with_text(token, car_type, brand, plate)
    update_ticket_token_and_file(rowid, token, filename)

    # try Access logging
    ok, msg = try_insert_access(token, car_type, brand, plate, filename)
    if ok:
        display_image(filename, f"Ticket generated and saved to Access: {token}")
    else:
        display_image(filename, f"Ticket generated (SQLite). Access: {msg}")

def generate_master():
    car_type = combocar.get() or "N/A"
    brand = entry_brand.get().strip() or "N/A"
    plate = entry_plate.get().strip() or "N/A"
    token = "MASTER"
    filename = generate_barcode_image_with_text(token, car_type, brand, plate)
    insert_ticket_record(token, car_type, brand, plate, filename)
    ok, msg = try_insert_access(token, car_type, brand, plate, filename)
    if ok:
        display_image(filename, f"MASTER generated and saved to Access")
    else:
        display_image(filename, f"MASTER generated. Access: {msg}")

def export_db_to_csv():
    path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files","*.csv")])
    if not path:
        return
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    rows = c.execute("SELECT id, token, created_at, car_type, brand, plate, filename FROM tickets ORDER BY id").fetchall()
    conn.close()
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id","token","created_at","car_type","brand","plate","filename"])
        writer.writerows(rows)
    messagebox.showinfo("Export", f"Database exported to {path}")

btn_ticket = ttk.Button(frm, text="Generate Ticket", command=generate_ticket)
btn_ticket.grid(column=0, row=4, pady=10)

btn_master = ttk.Button(frm, text="Generate MASTER", command=generate_master)
btn_master.grid(column=1, row=4, pady=10)

btn_export = ttk.Button(frm, text="Export DB to CSV", command=export_db_to_csv)
btn_export.grid(column=0, row=5, columnspan=2, pady=6)

root.mainloop()
