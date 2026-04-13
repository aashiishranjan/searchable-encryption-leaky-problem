from flask import Flask
from flask import Blueprint

app = Flask(__name__)

# Import blueprints
from routes.documents import documents
from routes.search import search
from routes.analysis import analysis

app.register_blueprint(documents)
app.register_blueprint(search)
app.register_blueprint(analysis)

if __name__ == '__main__':
    app.run(debug=True)