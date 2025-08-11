from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
import json
import os
import re
import requests
import json as pyjson
from urllib.parse import urlparse

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

RETAILER_MAP = {
    r"(?:^|\.)amazon\.(co\.uk|com)$": "Amazon",
    r"(?:^|\.)argos\.co\.uk$": "Argos",
    r"(?:^|\.)boots\.com$": "Boots",
    r"(?:^|\.)johnlewis\.com$": "John Lewis",
    r"(?:^|\.)mamasandpapas\.com$": "Mamas & Papas",
    r"(?:^|\.)mabelandfox\.com$": "Mabel & Fox",
    r"(?:^|\.)boots\.com$": "Boots",
    r"(?:^|\.)pippeta\.com$": "Pippeta",
    r"(?:^|\.)currys\.co\.uk$": "Currys",
    r"(?:^|\.)argos\.co\.uk$": "Argos",
    r"(?:^|\.)sainsburys\.co\.uk$": "Sainsburys",
    
}

def guess_retailer_from_url(url: str):
    try:
        if not url:
            return None
        # Add a scheme if the user pasted a bare domain
        if not re.match(r'^[a-z]+://', url, flags=re.I):
            url = 'http://' + url

        hostname = (urlparse(url).hostname or "").lower()

        # Match against regex patterns in RETAILER_MAP
        for pattern, name in RETAILER_MAP.items():
            if re.search(pattern, hostname):
                return name

        # Fallback: derive something readable from the hostname
        parts = hostname.split('.')
        if len(parts) >= 2:
            base = parts[-2]
            return base.capitalize()

        return None
    except Exception:
        return None

def _fmt_price(price, currency=None):
    # Normalise number or string + optional currency to a single string
    try:
        # If numeric (e.g., 250 or "250.0")
        v = float(str(price).strip())
        # keep two decimals like "250.00"
        p = f"{v:.2f}"
    except Exception:
        # if not numeric, just string
        p = str(price).strip()

    if currency:
        c = str(currency).strip().upper()
        # put GBP/£ niceties here if you want locale-aware formatting later
        return f"{c} {p}"
    return p

def try_fetch_price_from_structured_data(link: str):
    """
    Try to fetch product price from JSON-LD, OpenGraph, or itemprop-based HTML tags.
    Falls back to scanning nearby visible text if no content attribute is found.
    """
    try:
        resp = requests.get(link, timeout=6, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        html = resp.text

        import re as _re
        import json as _json

        # Helper to format price
        def _fmt_price(price, currency=None):
            price_str = str(price).strip()
            if currency and not price_str.startswith(currency):
                return f"{currency} {price_str}".strip()
            return price_str

        # -------- 1) JSON-LD <script type="application/ld+json"> --------
        blocks = _re.findall(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            html, flags=_re.I | _re.S
        )
        for txt in blocks:
            try:
                data = _json.loads(txt.strip())
            except Exception:
                continue
            objs = data if isinstance(data, list) else [data]
            for obj in objs:
                offers = obj.get("offers")
                if not offers:
                    continue
                offers_list = offers if isinstance(offers, list) else [offers]
                for offer in offers_list:
                    price = offer.get("price") or offer.get("priceSpecification", {}).get("price")
                    currency = offer.get("priceCurrency") or offer.get("priceSpecification", {}).get("priceCurrency")
                    if price:
                        return _fmt_price(price, currency)

        # -------- 2) Meta tags: og:price, product:price, itemprop="price" --------
        def find_meta(content_html, key, attr="property"):
            rgx = rf'<meta[^>]+{attr}=["\']{_re.escape(key)}["\'][^>]*content=["\']([^"\']+)["\']'
            m = _re.search(rgx, content_html, flags=_re.I)
            return m.group(1).strip() if m else None

        price = (
            find_meta(html, "og:price:amount", "property")
            or find_meta(html, "product:price:amount", "property")
            or find_meta(html, "price", "name")
            or find_meta(html, "price", "itemprop")
        )

        currency = (
            find_meta(html, "og:price:currency", "property")
            or find_meta(html, "product:price:currency", "property")
            or find_meta(html, "priceCurrency", "itemprop")
            or find_meta(html, "currency", "name")
        )

        # -------- 3) Non-meta tags with itemprop="price" and content= --------
        if not price:
            m = _re.search(
                r'<[^>]+itemprop=["\']price["\'][^>]+content=["\']([^"\']+)["\']',
                html, flags=_re.I
            )
            if m:
                price = m.group(1).strip()

        # -------- 4) Last resort: Look for visible text prices --------
        if not price:
            m = _re.search(
                r'<[^>]+itemprop=["\']price["\'][^>]*>([^<£€$]*[£€$]?\s?\d+[.,]?\d*)',
                html, flags=_re.I
            )
            if m:
                price = m.group(1).strip()

        if price:
            return _fmt_price(price, currency)

        return None
    except Exception:
        return None

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
        # --- Login ---
        if "login" in request.form:
            username = request.form.get("username")
            password = request.form.get("password")
            if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
                session["logged_in"] = True
                flash("Logged in successfully.", "info")
            else:
                flash("Invalid credentials.", "danger")
            return redirect(route_prefix + url_for("admin"))

        # --- Logout ---
        if "logout" in request.form:
            session.pop("logged_in", None)
            flash("Logged out.", "info")
            return redirect(route_prefix + url_for("admin"))

        # --- Require auth for changes ---
        if not is_logged_in():
            flash("Please log in to manage items.", "warning")
            return redirect(route_prefix + url_for("admin"))

        # --- Common fields ---
        name = (request.form.get("name") or "").strip()
        link = (request.form.get("link") or "").strip()
        image = (request.form.get("image") or "").strip()
        price = (request.form.get("price") or "").strip()
        retailer = (request.form.get("retailer") or "").strip()

        # Auto-guess retailer if empty and we have a link
        if not retailer and link:
            guessed = guess_retailer_from_url(link)
            if guessed:
                retailer = guessed

        # --- Fetch price when button pressed ---
        if "fetch_price" in request.form and link:
            fetched = try_fetch_price_from_structured_data(link)
            if fetched:
                price = fetched
                flash("Price fetched from page.", "info")
            else:
                flash("Couldn’t find a price on that page.", "warning")
            # We continue to save with the (possibly) updated price

        # --- Edit existing item ---
        if "edit_id" in request.form:
            edit_id = request.form["edit_id"]
            for p in products:
                if p["id"] == edit_id:
                    p["name"] = name
                    p["link"] = link
                    p["image"] = image
                    p["price"] = price
                    p["retailer"] = retailer
                    if price:
                        p["price_checked_at"] = datetime.utcnow().isoformat()
                    flash("Product updated.", "info")
                    break

        # --- Add a new item ---
        else:
            product_id = str(uuid4())
            new_item = {
                "id": product_id,
                "name": name,
                "link": link,
                "image": image,
                "price": price,
                "retailer": retailer,
                "purchased": False,
                "reserved": False
            }
            if price:
                new_item["price_checked_at"] = datetime.utcnow().isoformat()
            products.append(new_item)
            flash("Product added.", "info")

        save_products(products)
        return redirect(route_prefix + url_for("admin"))

    return render_template(
        "admin.html",
        route_prefix=route_prefix,
        url_prefix=html_prefix,
        products=products,
        logged_in=is_logged_in()
    )

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
