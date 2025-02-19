from datetime import datetime, timedelta, timezone
from pathlib import Path
import time

from flask import Blueprint, Response, request, abort, send_file, stream_with_context
import werkzeug.exceptions as ex
from pymysql.err import OperationalError
import lazy_object_proxy
import jwt

from ..build import Build
from ..logger import Logger
from . import db

logger = lazy_object_proxy.Proxy(lambda: Logger(0))
bp = Blueprint("rest", __name__, url_prefix="/api/v1")

_jwt_secret = "IceCreamFruitWaffle"


def result_dir():
    return Path.home() / "waffle_worker" / "result"


@bp.errorhandler(db.CreateConnectionError)
def db_create_connection_error(exc):
    print(exc)
    return 'The server is overloaded', 500


@bp.errorhandler(OperationalError)
def sql_operational_error(exc):
    print(exc)
    return exc.args[1], 500


@bp.errorhandler(ex.HTTPException)
def http_exception(exc):
    return exc.description, exc.code


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
        "limit": limit,
        "offset": offset,
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


@bp.route("/result/<int:build_id>/<path:item>", methods=['GET'])
def get_result(build_id, item):
    build = Build(build_id)
    path = result_dir() / f"{build_id}" / item

    if not path.is_file():
        return abort(404, "No such file or directory")

    if not build.is_building():
        return send_file(path, mimetype="text/plain")

    @stream_with_context
    def stream():
        try:
            with open(path, mode="r", encoding="utf-8") as f:
                # Yield all but the last line in case it is incomplete
                data = f.read()
                end = data.rfind("\n")
                if end > -1:
                    yield data[:end]
                    rest = data[end:]
                else:
                    rest = data

                timeout = 0
                while True:
                    line = f.readline()
                    if not line:
                        db.commit()  # Needed for query to be up-to-date
                        if not build.is_building():
                            break
                        time.sleep(1)
                        timeout += 1
                        if timeout > 30:
                            yield "\nTimeout!"
                            break
                        continue
                    timeout = 0
                    yield rest + line
                    rest = ""
        except OSError as e:
            yield str(e)

    return Response(stream(), mimetype="text/plain")


@bp.route("/public_url/<int:build_id>/<path:item>", methods=['GET'])
def get_public_url(build_id, item):
    build = Build(build_id)
    path = result_dir() / f"{build_id}" / item

    if build.is_building() or not path.is_file():
        return abort(404, "No such file or directory")

    ttl = timedelta(minutes=2)
    claims = {
        "build_id": build_id,
        "item": item,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + ttl,
    }
    token = jwt.encode(
        claims,
        _jwt_secret,
        algorithm="HS256",
    )
    return {
        "url": f"http://127.0.0.1:5001/api/v1/jwt/{token}",
        "ttl": int(ttl.total_seconds()),
    }


@bp.route("/jwt/<path:token>", methods=['GET'])
def public_download(token):
    try:
        decoded = jwt.decode(
            token,
            _jwt_secret,
            algorithms=["HS256"],
            options={"require": ["exp", "iat"]},
            leeway=2.0,
        )
        build = Build(decoded["build_id"])
        path = result_dir() / str(decoded["build_id"]) / decoded["item"]

        if build.is_building() or not path.is_file():
            return abort(404, "No such file or directory")

        return send_file(path)
    except (
        jwt.exceptions.InvalidTokenError,
        TypeError,
    ):
        return abort(404)
