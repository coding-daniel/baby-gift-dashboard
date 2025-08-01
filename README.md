# Baby Gift Dashboard 🎁

A lightweight, self-hosted baby gift registry built with **Flask**, **Tailwind CSS**, and **Python** — designed for easy sharing with friends and family, and customisable by the parents.

> Built as a personal tool to manage our baby’s gift list — and a proud part of my developer portfolio.

---

## Features

- 🔐 Simple admin login (password-protected)
- 📦 Add, edit, and delete gift items (name, link, image)
- 👀 Public view for friends and family to browse and mark gifts as purchased
- 📲 Mobile-friendly layout using Tailwind CSS
- 💬 Flash messages for feedback (e.g. “Item added” / “Thanks for purchasing”)

---

## Tech Stack

- [Flask](https://flask.palletsprojects.com/)
- [Tailwind CSS](https://tailwindcss.com/)
- [Python 3](https://www.python.org/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- Local development on macOS, deployable to Raspberry Pi 5 or any Linux server

---

## How to Run

### 🔧 Prerequisites

- Python 3.9+
- Node.js & npm
- Git

### 🧪 Setup

    git clone https://github.com/coding-daniel/baby-gift-dashboard.git
    cd baby-gift-dashboard

    # Create and activate virtual environment
    python3 -m venv .venv
    source .venv/bin/activate

    # Install Python dependencies
    pip install -r requirements.txt

    # Install Tailwind CSS
    npm install
    npx tailwindcss -i static/input.css -o static/tailwind.css --watch

### 🏃 Run the app

In a separate terminal:

    # Watch CSS
    npm run build:css

Then in another:

    make run

Then visit `http://localhost:5000` or `http://pi.local:5000` depending on your setup.

When you first run the app, it will create data/products.json if it doesn't exist. A sample file is included as data/products.sample.json for reference.

---

## Environment Variables

Create a `.env` file:

    SECRET_KEY=your-long-secret
    ADMIN_USERNAME=admin
    ADMIN_PASSWORD=yourpassword

---

## Planned Improvements

- ✅ Telegram notifications when a gift is marked as purchased
- ✅ Cloudflare Tunnel for public sharing
- 🖼️ Optional image uploads instead of just URLs
- 📈 Admin dashboard with gift stats

---

## License

MIT — use it, tweak it, share it.  
This was built to solve a real need in a simple way — if it helps someone else, that’s a bonus.

---

## Author

**Daniel** — [@coding-daniel](https://github.com/coding-daniel)  
Backend developer transitioning into Python, automation, and self-hosted tools.
