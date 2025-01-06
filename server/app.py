#!/usr/bin/env python3

import os
from flask import Flask
import db
import rest


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.register_blueprint(rest.bp)

    db.open()

    @app.route('/ping', methods=['GET'])
    def ping_pong():
        return 'pong!'

    return app


if __name__ == '__main__':
    create_app().run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5001")),
        debug=True,
        use_evalex=False,
        # not thread safe (global db connection)
        threaded=False,
        # set more than one process to simulate normal usage.
        processes=2,
    )
