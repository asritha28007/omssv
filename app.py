from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
import json, os, random
from datetime import datetime, date
from functools import wraps
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "omssv_secret_2024"

DATA_FILE = "data.json"
UPLOAD_FOLDER = "static/gallery"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_GALLERY_PHOTOS = 20

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    if not os.path.exists(DATA_FILE):
        return default_data()
    with open(DATA_FILE) as f:
        return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f:
        json.dump(d, f, indent=2)

def default_data():
    return {
        "rooms": {
            "3_sharing_ac":    {"total": 10, "occupied": 7},
            "3_sharing_nonac": {"total": 10, "occupied": 5},
            "4_sharing_ac":    {"total": 8,  "occupied": 6},
            "4_sharing_nonac": {"total": 8,  "occupied": 4},
            "5_sharing_ac":    {"total": 6,  "occupied": 3},
            "5_sharing_nonac": {"total": 6,  "occupied": 2},
        },
        "dishes": {
            "breakfast": ["Idli Sambar", "Poha", "Upma", "Puri Bhaji", "Dosa", "Paratha", "Bread Butter", "Cornflakes Milk"],
            "lunch":     ["Rice Dal", "Chapati Sabzi", "Biryani", "Curd Rice", "Rajma Rice", "Palak Paneer", "Mixed Veg"],
            "snacks":    ["Tea Biscuits", "Samosa", "Vada Pav", "Maggi", "Banana Shake", "Lemon Rice", "Bhel Puri"],
            "dinner":    ["Roti Sabzi", "Dal Khichdi", "Paneer Curry", "Mixed Dal", "Fried Rice", "Noodles Veg", "South Thali"]
        },
        "today_menu": {},
        "menu_date": "",
        "gallery_photos": [
            {"src": "/static/room.jpeg",   "label": "Our Room"},
            {"src": "/static/room2.jpeg",  "label": "Cozy Living"},
            {"src": "/static/hostel.jpeg", "label": "Hostel Building"},
            {"src": "/static/food1.jpeg",  "label": "Fresh Meals"},
            {"src": "/static/food2.jpeg",  "label": "Nutritious Food"},
            {"src": "/static/food3.jpeg",  "label": "Daily Menu"},
            {"src": "/static/food4.jpeg",  "label": "Homely Cooking"},
            {"src": "/static/doc.jpeg",    "label": "Our Facilities"}
        ],
        "reviews": [
            {"name": "Priya Sharma",          "type": "student", "rating": 5, "text": "Best hostel experience! Safe, clean, and the food is homely. The warden aunty is very caring. Highly recommended for girls!", "date": "2024-12-15", "approved": True},
            {"name": "Mrs. Lakshmi (Parent)", "type": "parent",  "rating": 5, "text": "Very satisfied. My daughter feels at home. Security is tight, meals are nutritious. Best decision we made.",              "date": "2024-12-10", "approved": True},
            {"name": "Anjali Reddy",          "type": "student", "rating": 4, "text": "Comfortable rooms, good WiFi, friendly atmosphere. The mess food is tasty and varied. Would recommend!",                  "date": "2024-11-28", "approved": True},
            {"name": "Mrs. Kavitha (Parent)", "type": "parent",  "rating": 5, "text": "Staff is very responsive. My daughter is safe and happy. Regular updates from warden gives us peace of mind.",            "date": "2024-11-20", "approved": True},
            {"name": "Sneha Patel",           "type": "student", "rating": 4, "text": "Good facilities, nice common room. The virtual tour on website helped me decide. A homely environment.",                  "date": "2024-11-15", "approved": True},
        ],
        "complaints": [],
        "enquiries": [],
    }

def get_today_menu(d):
    today = str(date.today())
    if d.get("menu_date") != today or not d.get("today_menu"):
        menu = {meal: random.choice(items) for meal, items in d["dishes"].items()}
        d["today_menu"] = menu
        d["menu_date"] = today
        save_data(d)
    return d["today_menu"]

# ── PUBLIC ROUTES ──────────────────────────────────────────────────────────────

@app.route("/")
def index():
    d = load_data()
    menu = get_today_menu(d)
    rooms = d["rooms"]
    vacancies = {k: v["total"] - v["occupied"] for k, v in rooms.items()}
    approved_reviews = [r for r in d["reviews"] if r.get("approved")]
    gallery_photos = d.get("gallery_photos", [])
    return render_template("index.html",
        menu=menu,
        vacancies=vacancies,
        rooms=rooms,
        reviews=approved_reviews,
        gallery_photos=gallery_photos
    )

@app.route("/api/vacancies")
def api_vacancies():
    d = load_data()
    return jsonify({k: {"total": v["total"], "vacant": v["total"] - v["occupied"]} for k, v in d["rooms"].items()})

@app.route("/api/menu")
def api_menu():
    d = load_data()
    return jsonify(get_today_menu(d))
# ← ADD HERE ↓

@app.route("/robots.txt")
def robots():
    content = """User-agent: *
Allow: /
Sitemap: https://omssv.in/sitemap.xml"""
    return Response(content, mimetype="text/plain")

@app.route("/sitemap.xml")
def sitemap():
    content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://omssv.in/</loc>
    <priority>1.0</priority>
  </url>
</urlset>"""
    return Response(content, mimetype="application/xml")

@app.route("/submit_review", methods=["POST"])
def submit_review():
    d = load_data()
    d["reviews"].append({
        "name":     request.form.get("name", "Anonymous"),
        "type":     request.form.get("type", "student"),
        "rating":   int(request.form.get("rating", 5)),
        "text":     request.form.get("text", ""),
        "date":     str(date.today()),
        "approved": False
    })
    save_data(d)
    return jsonify({"success": True, "message": "Review submitted for approval!"})

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():
    d = load_data()
    d["complaints"].append({
        "id":       len(d["complaints"]) + 1,
        "name":     request.form.get("name", "Anonymous"),
        "category": request.form.get("category", "General"),
        "message":  request.form.get("message", ""),
        "date":     str(date.today()),
        "status":   "pending"
    })
    save_data(d)
    return jsonify({"success": True, "message": "Complaint submitted!"})

@app.route("/submit_enquiry", methods=["POST"])
def submit_enquiry():
    d = load_data()
    d["enquiries"].append({
        "id":        len(d["enquiries"]) + 1,
        "name":      request.form.get("name"),
        "phone":     request.form.get("phone"),
        "email":     request.form.get("email", ""),
        "room_type": request.form.get("room_type", ""),
        "message":   request.form.get("message", ""),
        "date":      str(date.today())
    })
    save_data(d)
    return jsonify({"success": True, "message": "Enquiry received! We'll contact you shortly."})

# ── ADMIN AUTH ─────────────────────────────────────────────────────────────────

ADMIN_PASSWORD = "omssv@admin"

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html", error="Invalid password")
    return render_template("admin_login.html")

@app.route("/admin_logout")
def admin_logout():
    session.pop("admin", None)
    return redirect(url_for("index"))

# ── ADMIN DASHBOARD ────────────────────────────────────────────────────────────

@app.route("/admin")
@admin_required
def admin_dashboard():
    d = load_data()
    return render_template("admin_dashboard.html", data=d, menu=get_today_menu(d))

@app.route("/admin/update_rooms", methods=["POST"])
@admin_required
def update_rooms():
    d = load_data()
    for key in d["rooms"]:
        if key in request.form:
            d["rooms"][key]["occupied"] = int(request.form[key])
    save_data(d)
    return jsonify({"success": True})

@app.route("/admin/add_dish", methods=["POST"])
@admin_required
def add_dish():
    d = load_data()
    meal = request.form.get("meal")
    dish = request.form.get("dish", "").strip()
    if meal in d["dishes"] and dish:
        d["dishes"][meal].append(dish)
        save_data(d)
        return jsonify({"success": True})
    return jsonify({"success": False})

@app.route("/admin/remove_dish", methods=["POST"])
@admin_required
def remove_dish():
    d = load_data()
    meal = request.form.get("meal")
    dish = request.form.get("dish")
    if meal in d["dishes"] and dish in d["dishes"][meal]:
        d["dishes"][meal].remove(dish)
        save_data(d)
    return jsonify({"success": True})

@app.route("/admin/regenerate_menu", methods=["POST"])
@admin_required
def regenerate_menu():
    d = load_data()
    menu = {meal: random.choice(items) for meal, items in d["dishes"].items()}
    d["today_menu"] = menu
    d["menu_date"] = str(date.today())
    save_data(d)
    return jsonify({"success": True, "menu": menu})

@app.route("/admin/review_action", methods=["POST"])
@admin_required
def review_action():
    d = load_data()
    idx    = int(request.form.get("idx"))
    action = request.form.get("action")
    if action == "approve":
        d["reviews"][idx]["approved"] = True
    elif action == "delete":
        d["reviews"].pop(idx)
    save_data(d)
    return jsonify({"success": True})

@app.route("/admin/resolve_complaint", methods=["POST"])
@admin_required
def resolve_complaint():
    d = load_data()
    cid = int(request.form.get("id"))
    for c in d["complaints"]:
        if c["id"] == cid:
            c["status"] = "resolved"
    save_data(d)
    return jsonify({"success": True})

# ── GALLERY ROUTES ─────────────────────────────────────────────────────────────

@app.route("/admin/upload_gallery_photo", methods=["POST"])
@admin_required
def upload_gallery_photo():
    d = load_data()
    photos = d.get("gallery_photos", [])
    if len(photos) >= MAX_GALLERY_PHOTOS:
        return jsonify({"success": False, "message": f"Gallery limit of {MAX_GALLERY_PHOTOS} photos reached."})
    if "photo" not in request.files:
        return jsonify({"success": False, "message": "No file provided."})
    file  = request.files["photo"]
    label = request.form.get("label", "Photo").strip() or "Photo"
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"success": False, "message": "Only JPG, PNG, WEBP files allowed."})
    ext         = file.filename.rsplit(".", 1)[1].lower()
    unique_name = f"gallery_{int(datetime.now().timestamp()*1000)}.{ext}"
    file.save(os.path.join(UPLOAD_FOLDER, unique_name))
    src = f"/static/gallery/{unique_name}"
    photos.append({"src": src, "label": label})
    d["gallery_photos"] = photos
    save_data(d)
    return jsonify({"success": True, "src": src, "label": label})

@app.route("/admin/delete_gallery_photo", methods=["POST"])
@admin_required
def delete_gallery_photo():
    d   = load_data()
    src = request.form.get("src", "")
    d["gallery_photos"] = [p for p in d.get("gallery_photos", []) if p["src"] != src]
    save_data(d)
    if src.startswith("/static/gallery/"):
        filepath = src.lstrip("/")
        if os.path.exists(filepath):
            try: os.remove(filepath)
            except OSError: pass
    return jsonify({"success": True})

@app.route("/admin/reorder_gallery", methods=["POST"])
@admin_required
def reorder_gallery():
    d         = load_data()
    new_order = (request.get_json() or {}).get("order", [])
    photo_map = {p["src"]: p for p in d.get("gallery_photos", [])}
    reordered = [photo_map[src] for src in new_order if src in photo_map]
    # Append any photos not in the new order list (safety net)
    seen = set(new_order)
    for p in d.get("gallery_photos", []):
        if p["src"] not in seen:
            reordered.append(p)
    d["gallery_photos"] = reordered
    save_data(d)
    return jsonify({"success": True})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
