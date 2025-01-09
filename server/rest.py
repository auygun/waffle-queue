from flask import Blueprint, request, abort
import db

bp = Blueprint("rest", __name__, url_prefix="/api/v1")


@bp.after_request
def add_cache_controls(response):
    response.cache_control.no_store = True
    return response


@bp.route('/builds', methods=['GET'])
def get_builds():
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute('SELECT * FROM builds')
        return {
            'builds': cursor.fetchall()
        }


@bp.route("/integrate", methods=["POST"])
def integrate():
    branch = request.form.get("branch", "")
    if branch == "":
        return abort(400)
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute(
            'INSERT INTO builds (branch, state) VALUES (%s, %s)', (branch, 'REQUESTED'))
        conn.commit()
    return {}


@bp.route("/abort/<build_id>", methods=["POST"])
def abort(build_id):
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute("UPDATE builds SET state = CASE WHEN (state='REQUESTED' OR state='BUILDING') THEN 'ABORTED' ELSE state END WHERE id=%s",
                       (build_id))
        conn.commit()
    return {}


@bp.route("/dev/clear", methods=["POST"])
def clear():
    with db.connection() as conn, conn.cursor() as cursor:
        cursor.execute('DELETE FROM builds')
        conn.commit()
    return {}


# @bp.route('/books', methods=['GET', 'POST'])
# def all_books():
#     response_object = {'status': 'success'}
#     if request.method == 'POST':
#         post_data = request.get_json()
#         BOOKS.append({
#             'id': uuid.uuid4().hex,
#             'title': post_data.get('title'),
#             'author': post_data.get('author'),
#             'read': post_data.get('read')
#         })
#         response_object['message'] = 'Book added!'
#     else:
#         response_object['books'] = BOOKS
#     return jsonify(response_object)


# @bp.route('/books/<book_id>', methods=['PUT', 'DELETE'])
# def single_book(book_id):
#     response_object = {'status': 'success'}
#     if request.method == 'PUT':
#         post_data = request.get_json()
#         remove_book(book_id)
#         BOOKS.append({
#             'id': uuid.uuid4().hex,
#             'title': post_data.get('title'),
#             'author': post_data.get('author'),
#             'read': post_data.get('read')
#         })
#         response_object['message'] = 'Book updated!'
#     if request.method == 'DELETE':
#         remove_book(book_id)
#         response_object['message'] = 'Book removed!'
#     return jsonify(response_object)
