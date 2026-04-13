"""
app.py - Main Flask application entry point.

Run with:
    python app.py   # → http://127.0.0.1:5000
"""

import os
import sys

# Make the repository root importable so the routes can access src/
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from flask import Flask
from flask_cors import CORS

from config import CORS_ORIGIN, DEBUG, HOST, PORT, SECRET_KEY
from routes.documents import documents_bp
from routes.search import search_bp
from routes.analysis import analysis_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Allow the React dev-server (and same-origin fetch in production)
CORS(app, origins=[CORS_ORIGIN], supports_credentials=True)

# Register blueprints – all routes live under /api
app.register_blueprint(documents_bp, url_prefix="/api")
app.register_blueprint(search_bp, url_prefix="/api")
app.register_blueprint(analysis_bp, url_prefix="/api")


@app.route("/")
def index():
    return {"status": "ok", "message": "Searchable Encryption Leaky Problem API"}


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
