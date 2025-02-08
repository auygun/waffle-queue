from flask import Blueprint, request, abort
from pymysql.err import OperationalError

import lazy_object_proxy
from ..build import Build
from ..logger import Logger
from . import db

logger = lazy_object_proxy.Proxy(lambda: Logger(0))
bp = Blueprint("rest", __name__, url_prefix="/api/v1")


@bp.errorhandler(db.CreateConnectionError)
def db_create_connection_error(exc):
    print(exc)
    return 'Systems is too busy', 500


@bp.errorhandler(OperationalError)
def sql_operational_error(exc):
    print(exc)
    return str(exc.args), 500


@bp.after_request
def add_cache_controls(response):
    response.cache_control.no_store = True
    return response


@bp.teardown_request
def db_commit(_exc):
    # pylint:disable = bare-except
    try:
        db.commit()
    except:
        pass


@bp.route('/builds', methods=['GET'])
def get_builds():
    limit = request.args.get("limit", 25, type=int)
    offset = request.args.get("offset", 0, type=int)
    if limit < 1 or limit > 100 or offset < 0:
        return abort(400)
    return {
        "count": Build.count(),
        'content': Build.list(offset, limit, jsonify=True),
    }


@bp.route("/integrate", methods=["POST"])
def integrate():
    branch = request.form.get("branch", "")
    if branch == "":
        return abort(400)
    Build.new(branch)
    return {}


@bp.route("/abort/<build_id>", methods=["POST"])
def abort_build(build_id):
    Build(build_id).abort()
    return {}


@bp.route("/dev/clear", methods=["POST"])
def clear():
    Build.clear()
    return {}


@bp.route('/log', methods=['GET'])
def get_log():
    return {
        'content': logger.list(jsonify=True)
    }
