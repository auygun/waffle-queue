from datetime import datetime, timedelta, timezone
from pathlib import Path
import time
from flask import Blueprint, Response, request, abort, send_file, stream_with_context
import werkzeug.exceptions as ex
from pymysql.err import OperationalError, IntegrityError
import lazy_object_proxy
import jwt
from ..build import Build
from ..request import Request
from ..logger import Logger
from . import db

logger = lazy_object_proxy.Proxy(lambda: Logger(0))
bp = Blueprint("rest", __name__, url_prefix="/api/v1")

JWT_SECRET = "IceCreamFruitWaffle"


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


@bp.route('/requests', methods=['GET'])
def get_requests():
    limit = request.args.get("limit", 25, type=int)
    offset = request.args.get("offset", 0, type=int)
    if limit < 1 or limit > 100 or offset < 0:
        return abort(400)
    return {
        "count": Request.count(),
        "limit": limit,
        "offset": offset,
        'content': Request.list(offset, limit, jsonify=True),
    }


@bp.route('/builds/<request_id>', methods=['GET'])
def get_builds(request_id):
    return {
        "request_id": request_id,
        'content': Build.list(request_id, jsonify=True),
    }


@bp.route("/new_request", methods=["POST"])
def new_request():
    project_name = request.form.get("project-name", "", type=str)
    request_type = request.form.get("request-type", "", type=str)
    source_branch = request.form.get("source-branch", "", type=str)
    target_branch = request.form.get("target-branch", "", type=str)
    if any(i == "" for i in [project_name, source_branch]):
        return abort(400)
    if request_type != "Integration" and request_type != "Build":
        return abort(400)
    if request_type == "Integration" and target_branch == "":
        return abort(400, "Missing target branch name")
    try:
        Request.create(project_name, request_type == "Integration",
                       source_branch, target_branch)
    except IntegrityError:
        return abort(400, "Unknown project")
    return {}


@bp.route("/abort/<request_id>", methods=["POST"])
def abort_request(request_id):
    Request(request_id).set_aborted()
    return {}


@bp.route('/log', methods=['GET'])
def get_log():
    server_id = request.args.get("server_id", -1, type=int)
    severity = request.args.get("max_severity", "TRACE", type=str)
    if server_id < 0:
        return abort(400, "Missing build id")
    return {
        'server_id': server_id,
        'max_severity': severity,
        'content': logger.list(server_id, max_severity=severity)
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
                            yield "\n..."
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
        JWT_SECRET,
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
            JWT_SECRET,
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
