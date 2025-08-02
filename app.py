from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
import json
import os

# Load environment variables
load_dotenv()

# Determine path prefix based on environment
APP_PREFIX = "/baby" if os.environ.get("APP_ENV") == "pi" else ""

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Set up Flask app
app = Flask(
    __name__,
    static_url_path=f"{APP_PREFIX}/static",
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates")
)
app.secret_key = os.getenv("SECRET_KEY", "dev")
app.config["APP_PREFIX"] = APP_PREFIX

# Credentials
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

# Data file path
DATA_FILE = BASE_DIR / "data/products.json"
os.makedirs(DATA_FILE.parent, exist_ok=True)

# Load and save helpers
def load_products():
    if not DATA_FILE.exists():
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_products(products):
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2)

def is_logged_in():
    return session.get("logged_in", False)

# Routes
@app.route("/")
def index():
    products = load_products()
    html_prefix = "/baby/baby" if os.environ.get("APP_ENV") == "pi" else ""
    route_prefix = "/baby" if os.environ.get("APP_ENV") == "pi" else ""
    return render_template("index.html", route_prefix=route_prefix, url_prefix=html_prefix, products=products)

@app.route("/admin", methods=["GET", "POST"])
def admin():
    html_prefix = "/baby/baby" if os.environ.get("APP_ENV") == "pi" else ""
    route_prefix = "/baby" if os.environ.get("APP_ENV") == "pi" else ""
    products = load_products()

    if request.method == "POST":
        # Handle login
        if "login" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["logged_in"] = True
                flash("Logged in successfully.", "info")
            else:
                flash("Invalid credentials.", "danger")
            return redirect(route_prefix + url_for("admin"))

        # Handle logout
        if "logout" in request.form:
            session.pop("logged_in", None)
            flash("Logged out.", "info")
            return redirect(route_prefix + url_for("admin"))

        # Require login for edits/adds/deletes
        if not is_logged_in():
            flash("Please log in to manage items.", "warning")
            return redirect(route_prefix + url_for("admin"))

        # Handle product edits
        if "edit_id" in request.form:
            for p in products:
                if p["id"] == request.form["edit_id"]:
                    p["name"] = request.form["name"]
                    p["link"] = request.form["link"]
                    p["image"] = request.form.get("image") or ""
                    flash("Product updated.", "info")
                    break
        else:
            # Handle new product addition
            name = request.form["name"]
            link = request.form["link"]
            image = request.form.get("image") or ""
            product_id = str(uuid4())

            products.append({
                "id": product_id,
                "name": name,
                "link": link,
                "image": image,
                "purchased": False
            })
            flash("Product added.", "info")

        save_products(products)
        return redirect(route_prefix + url_for("admin"))

    return render_template("admin.html", route_prefix=route_prefix, url_prefix=html_prefix, products=products, logged_in=is_logged_in())

@app.route("/mark/<product_id>", methods=["POST"])
def mark_purchased(product_id):
    route_prefix = "/baby" if os.environ.get("APP_ENV") == "pi" else ""
    products = load_products()
    for p in products:
        if p["id"] == product_id:
            p["purchased"] = True
            p["purchased_at"] = datetime.utcnow().isoformat()
            flash(f"Thanks! '{p['name']}' marked as purchased.", "success")
            break
    save_products(products)
    return redirect(route_prefix + url_for("index"))

@app.route("/delete/<product_id>", methods=["POST"])
def delete_product(product_id):
    route_prefix = "/baby" if os.environ.get("APP_ENV") == "pi" else ""
    if not is_logged_in():
        flash("Please log in to delete items.", "warning")
        return redirect(route_prefix + url_for("admin"))

    products = load_products()
    products = [p for p in products if p["id"] != product_id]
    save_products(products)
    flash("Product deleted.", "warning")
    return redirect(route_prefix + url_for("admin"))

@app.route("/clear/<product_id>", methods=["POST"])
def clear_flags(product_id):
    route_prefix = "/baby" if os.environ.get("APP_ENV") == "pi" else ""
    if not is_logged_in():
        flash("Please log in to clear product status.", "warning")
        return redirect(route_prefix + url_for("admin"))

    products = load_products()
    for p in products:
        if p["id"] == product_id:
            p["purchased"] = False
            p.pop("purchased_at", None)
            flash(f"Status for '{p['name']}' has been cleared.", "info")
            break
    save_products(products)
    return redirect(route_prefix + url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
