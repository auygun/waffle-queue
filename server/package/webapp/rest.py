from flask import Blueprint, request, abort
from pymysql.err import OperationalError
from . import db

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
    try:
        db.commit()
    finally:
        pass


@bp.route('/builds', methods=['GET'])
def get_builds():
    with db.cursor() as cursor:
        cursor.execute('SELECT * FROM builds')
        return {
            'builds': cursor.fetchall()
        }


@bp.route("/integrate", methods=["POST"])
def integrate():
    branch = request.form.get("branch", "")
    if branch == "":
        return abort(400)
    with db.cursor() as cursor:
        cursor.execute("INSERT INTO builds (branch, state) "
                       "VALUES (%s, %s)", (branch, 'REQUESTED'))
    return {}


@bp.route("/abort/<build_id>", methods=["POST"])
def abort_build(build_id):
    with db.cursor() as cursor:
        cursor.execute("UPDATE builds SET state = CASE "
                       "WHEN (state='REQUESTED' OR state='BUILDING') "
                       "THEN 'ABORTED' ELSE state "
                       "END WHERE id=%s", (build_id))
    return {}


@bp.route("/dev/clear", methods=["POST"])
def clear():
    with db.cursor() as cursor:
        cursor.execute('DELETE FROM builds')
    return {}
