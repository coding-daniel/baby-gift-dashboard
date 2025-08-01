from flask import Flask, render_template, request, redirect, url_for, flash, session
import json
import os
from uuid import uuid4
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")

DATA_FILE = "data/products.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs("data", exist_ok=True)

# Load products from JSON file
def load_products():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Save products to JSON file
def save_products(products):
    with open(DATA_FILE, "w") as f:
        json.dump(products, f, indent=2)

def is_logged_in():
    return session.get("logged_in", False)

@app.route("/")
def index():
    products = load_products()
    return render_template("index.html", products=products)

@app.route("/mark/<product_id>", methods=["POST"])
def mark_purchased(product_id):
    products = load_products()
    for p in products:
        if p["id"] == product_id:
            p["purchased"] = True
            p["purchased_at"] = datetime.utcnow().isoformat()
            flash(f"Thanks! '{p['name']}' marked as purchased.", "success")
            break
    save_products(products)
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin():
    print("Session state:", session)
    products = load_products()

    if request.method == "POST":
        if "login" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["logged_in"] = True
                flash("Logged in successfully.", "info")
            else:
                flash("Invalid credentials.", "danger")
            return redirect(url_for("admin"))

        if "logout" in request.form:
            session.pop("logged_in", None)
            flash("Logged out.", "info")
            return redirect(url_for("admin"))

        if not is_logged_in():
            flash("Please log in to manage items.", "warning")
            return redirect(url_for("admin"))

        if "edit_id" in request.form:
            for p in products:
                if p["id"] == request.form["edit_id"]:
                    p["name"] = request.form["name"]
                    p["link"] = request.form["link"]
                    p["image"] = request.form.get("image") or ""
                    flash("Product updated.", "info")
                    break
        else:
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
        return redirect(url_for("admin"))

    return render_template("admin.html", products=products, logged_in=is_logged_in())

@app.route("/delete/<product_id>", methods=["POST"])
def delete_product(product_id):
    if not is_logged_in():
        flash("Please log in to delete items.", "warning")
        return redirect(url_for("admin"))

    products = load_products()
    products = [p for p in products if p["id"] != product_id]
    save_products(products)
    flash("Product deleted.", "warning")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
