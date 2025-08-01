# Babylist App - Makefile

APP_NAME=app.py
VENV=.venv
PYTHON=$(VENV)/bin/python
PIP=$(VENV)/bin/pip
FLASK=$(VENV)/bin/flask
ENV_FILE=.env
PORT ?= 5000

# 1. Create Python virtual environment
venv:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip

# 2. Install Python packages
requirements:
	$(PIP) install -r requirements.txt

# 3. Install correct Tailwind CLI and deps
tailwind-install:
	rm -rf node_modules package-lock.json
	npm install -D tailwindcss@3.4.3 postcss autoprefixer

# 4. Compile Tailwind CSS (watch mode)
tailwind:
	npm run build:css

# 5. Run Flask app using virtualenv
run:
	FLASK_APP=$(APP_NAME) FLASK_ENV=development $(FLASK) run --host=0.0.0.0 --port=$(PORT)

# Format Python code
format:
	$(VENV)/bin/black .

# Lint Python code
lint:
	$(VENV)/bin/flake8 .

# Copy .env if needed
env:
	@test -f $(ENV_FILE) || cp .env.example $(ENV_FILE)

# Run Flask in screen session
screen:
	screen -S babylist make run
