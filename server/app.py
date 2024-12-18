import uuid
from flask import Flask
from flask_cors import CORS
import db
import rest


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(rest.bp)

    # enable CORS
    CORS(app, resources={r'/*': {'origins': '*'}})

    db.init_app(app)

    return app


if __name__ == '__main__':
    print("Usage: flask run --port=5001 --debug")
