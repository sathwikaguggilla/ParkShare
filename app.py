from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

# ---------------- DATABASE ----------------
def init_db():
    conn = sqlite3.connect("parkshare.db")
    c = conn.cursor()

    # Parking spaces (matches ER diagram idea)
    c.execute("""
    CREATE TABLE IF NOT EXISTS ParkingSpace (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        location TEXT,
        rate INTEGER,
        slots INTEGER
    )
    """)

    # Bookings
    c.execute("""
    CREATE TABLE IF NOT EXISTS Booking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        space_id INTEGER,
        hours INTEGER,
        total INTEGER
    )
    """)

    # Area traffic
    c.execute("""
    CREATE TABLE IF NOT EXISTS AreaTraffic (
        area TEXT PRIMARY KEY,
        status TEXT
    )
    """)

    # Sample data
    c.execute("INSERT OR IGNORE INTO AreaTraffic VALUES ('Market', 'Full')")
    c.execute("INSERT OR IGNORE INTO AreaTraffic VALUES ('Mall', 'Available')")
    c.execute("INSERT OR IGNORE INTO AreaTraffic VALUES ('Bus', 'Full')")

    conn.commit()
    conn.close()

init_db()

# ---------------- HOME ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    spots = []
    message = None
    color = "success"

    if request.method == "POST":
        area = request.form["area"]

        conn = sqlite3.connect("parkshare.db")
        c = conn.cursor()

        # Traffic check
        c.execute("SELECT status FROM AreaTraffic WHERE area=?", (area,))
        row = c.fetchone()

        if row and row[0] == "Full":
            message = "🚨 High traffic area. Showing nearby private parking."
            color = "danger"
        else:
            message = "✅ Parking available. Private options also shown."
            color = "success"

        # Show all available private spaces
        c.execute("SELECT * FROM ParkingSpace WHERE slots > 0")
        spots = c.fetchall()

        conn.close()

    return render_template("home.html", spots=spots, message=message, color=color)

# ---------------- HOST ----------------
@app.route("/host", methods=["GET", "POST"])
def host():
    if request.method == "POST":
        location = request.form["location"]
        rate = request.form["rate"]
        slots = request.form["slots"]

        conn = sqlite3.connect("parkshare.db")
        c = conn.cursor()

        c.execute(
            "INSERT INTO ParkingSpace(location, rate, slots) VALUES (?, ?, ?)",
            (location, rate, slots)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template("host.html")

# ---------------- BOOK ----------------
@app.route("/book/<int:id>")
def book(id):
    conn = sqlite3.connect("parkshare.db")
    c = conn.cursor()

    # Reduce slot safely
    c.execute("UPDATE ParkingSpace SET slots = slots - 1 WHERE id=? AND slots > 0", (id,))

    if c.rowcount == 0:
        conn.close()
        return "No slots available. <a href='/'>Back</a>"

    # Get rate
    c.execute("SELECT rate FROM ParkingSpace WHERE id=?", (id,))
    rate = c.fetchone()[0]

    hours = 2
    total = hours * rate

    c.execute("INSERT INTO Booking(space_id, hours, total) VALUES (?, ?, ?)", (id, hours, total))

    conn.commit()
    conn.close()

    return f"Booking successful! Paid ₹{total}. <a href='/'>Back</a>"

# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect("parkshare.db")
    c = conn.cursor()

    c.execute("SELECT COUNT(*) FROM Booking")
    bookings = c.fetchone()[0]

    c.execute("SELECT SUM(total) FROM Booking")
    earnings = c.fetchone()[0] or 0

    conn.close()

    return render_template("dashboard.html", bookings=bookings, earnings=earnings)

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)