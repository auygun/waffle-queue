from flask import Blueprint, request, abort
import werkzeug.exceptions as ex
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
    return 'The server is overloaded', 500


@bp.errorhandler(OperationalError)
def sql_operational_error(exc):
    print(exc)
    return str(exc.args), 500


@bp.errorhandler(ex.HTTPException)
def http_exception(exc):
    return str(exc.description), exc.code


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


@bp.route("/request", methods=["POST"])
def integrate():
    request_type = request.form.get("request-type", "", type=str)
    remote_url = request.form.get("remote-url", "", type=str)
    source_branch = request.form.get("source-branch", "", type=str)
    target_branch = request.form.get("target-branch", "", type=str)
    build_script = request.form.get("build-script", "", type=str)
    work_dir = request.form.get("work-dir", "", type=str)
    if any(i == "" for i in [remote_url, source_branch, build_script]):
        return abort(400)
    if request_type != "Integration" and request_type != "Build":
        return abort(400)
    if request_type == "Integration" and target_branch == "":
        return abort(400, "Missing target branch name")
    Build.new(request_type == "Integration", remote_url, source_branch,
              target_branch, build_script, work_dir)
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
    build_id = request.args.get("build_id", -1, type=int)
    severity = request.args.get("max_severity", "TRACE", type=str)
    print(build_id)
    if build_id < 0:
        return abort(400, "Missing build id")
    return {
        'content': logger.list(build_id, max_severity=severity, jsonify=True)
    }
