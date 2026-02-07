from flask import Flask, render_template, request, redirect
import sqlite3
from reportlab.pdfgen import canvas

app = Flask(__name__)
DB = "database.db"

# ---------- Database Setup ----------
def init_db():
    conn = sqlite3.connect(DB)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS events(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            club TEXT,
            date TEXT,
            description TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS registrations(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            event_id INTEGER,
            attended INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- Home ----------
@app.route("/")
def home():
    conn = sqlite3.connect(DB)
    events = conn.execute("SELECT * FROM events").fetchall()
    conn.close()
    return render_template("index.html", events=events)

# ---------- Events Page ----------
@app.route("/events")
def events():
    club = request.args.get("club")

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    if club:
        events = conn.execute(
            "SELECT * FROM events WHERE club=?",
            (club,)
        ).fetchall()
    else:
        events = conn.execute("SELECT * FROM events").fetchall()

    clubs = conn.execute("SELECT DISTINCT club FROM events").fetchall()
    conn.close()

    return render_template("events.html", events=events, clubs=clubs)


# ---------- Admin Create Event ----------
@app.route("/admin/create_event", methods=["GET", "POST"])
def create_event():
    if request.method == "POST":
        title = request.form["title"]
        club = request.form["club"]
        date = request.form["date"]
        description = request.form["description"]

        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO events(title,club,date,description) VALUES(?,?,?,?)",
            (title, club, date, description)
        )
        conn.commit()
        conn.close()

        return redirect("/events")

    return render_template("admin/create_event.html")

# ---------- Registration ----------
@app.route("/register/<int:event_id>", methods=["GET", "POST"])
def register(event_id):
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]

        conn = sqlite3.connect(DB)
        conn.execute(
            "INSERT INTO registrations(name,email,event_id) VALUES(?,?,?)",
            (name, email, event_id),
        )
        conn.commit()
        conn.close()

        return redirect("/events")

    return render_template("register.html", event_id=event_id)

# ---------- Admin Dashboard ----------
@app.route("/dashboard/<int:event_id>")
def dashboard(event_id):
    conn = sqlite3.connect(DB)
    users = conn.execute(
        "SELECT * FROM registrations WHERE event_id=?",
        (event_id,),
    ).fetchall()
    conn.close()

    return render_template("dashboard.html", users=users, event_id=event_id)

# ---------- Attendance ----------
@app.route("/attend/<int:user_id>/<int:event_id>")
def attend(user_id, event_id):
    conn = sqlite3.connect(DB)
    conn.execute(
        "UPDATE registrations SET attended=1 WHERE id=?",
        (user_id,),
    )
    conn.commit()
    conn.close()

    return redirect(f"/dashboard/{event_id}")

# ---------- Certificate ----------
@app.route("/certificate/<int:user_id>")
def certificate(user_id):
    conn = sqlite3.connect(DB)

    user = conn.execute(
        "SELECT name,event_id FROM registrations WHERE id=?",
        (user_id,),
    ).fetchone()

    event = conn.execute(
        "SELECT title FROM events WHERE id=?",
        (user[1],),
    ).fetchone()

    conn.close()

    filename = f"certificates/{user[0]}.pdf"

    c = canvas.Canvas(filename)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(150, 700, "Certificate of Participation")

    c.setFont("Helvetica", 16)
    c.drawString(100, 600, "This certifies that")
    c.drawString(100, 560, user[0])
    c.drawString(100, 520, f"participated in {event[0]}")
    c.save()

    return f"Certificate created: {filename}"

if __name__ == "__main__":
    app.run(debug=True)
