import os

from flask import Flask
from . import rest, db


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(rest.bp)

    # pylint:disable = no-member
    app.teardown_appcontext(db.recycle)

    @app.route('/ping', methods=['GET'])
    def ping_pong():
        return 'pong!'

    return app


def dev_run():
    create_app().run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5001")),
        debug=True,
        use_evalex=False,
        threaded=False,
        processes=1,
    )
