from flask import Flask
from flask_cors import CORS

from config import SECRET_KEY, DEBUG, HOST, PORT, CORS_ORIGIN
from routes.documents import documents_bp
from routes.search import search_bp
from routes.analysis import analysis_bp

app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY

CORS(app, origins=[CORS_ORIGIN], supports_credentials=True)

app.register_blueprint(documents_bp, url_prefix="/api")
app.register_blueprint(search_bp, url_prefix="/api")
app.register_blueprint(analysis_bp, url_prefix="/api")

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
