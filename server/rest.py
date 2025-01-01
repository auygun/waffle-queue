from flask import Blueprint, request, jsonify, abort
import db

bp = Blueprint("rest", __name__, url_prefix="/api/v1")


@bp.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@bp.route('/builds', methods=['GET'])
def get_builds():
    response = {'status': 'success'}
    with db.cursor() as cursor:
        cursor.execute('select * from builds')
        response['builds'] = cursor.fetchall()
    return jsonify(response)


@bp.route("/integrate", methods=["POST"])
def integrate():
    response = {}
    branch = request.form.get("branch", "")
    if branch == "":
        return abort(400)
    with db.cursor() as cursor:
        cursor.execute('INSERT INTO builds (branch, state) VALUES (%s, %s)', (branch, 'REQUESTED'))
    db.commit()
    response['status'] = 'success'
    return jsonify(response)

@bp.route("/abort/<build_id>", methods=["POST"])
def abort(build_id):
    print(build_id)
    response = {}
    with db.cursor() as cursor:
        cursor.execute('UPDATE builds SET state=%s WHERE id=%s', ('ABORTED', build_id))
    db.commit()
    response['status'] = 'success'
    return jsonify(response)

@bp.route("/dev/clear", methods=["POST"])
def clear():
    response = {}
    with db.cursor() as cursor:
        cursor.execute('DELETE FROM builds')
    db.commit()
    response['status'] = 'success'
    return jsonify(response)


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
