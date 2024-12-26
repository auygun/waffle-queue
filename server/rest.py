from flask import Blueprint, request, jsonify
import db

bp = Blueprint("rest", __name__, url_prefix="/api/v1")


@bp.route('/ping', methods=['GET'])
def ping_pong():
    return jsonify('pong!')


@bp.route('/builds', methods=['GET'])
def get_builds():
    response = {'status': 'success'}
    # response['builds'] = db.query_db('select * from builds')
    response['builds'] = db.query_db('select * from builds')
    return jsonify(response)


@bp.route("/integrate", methods=["POST"])
def integrate():
    response = {}
    branch = request.form.get("branch", "")
    if branch == "":
        response['status'] = 'failure'
        response['message'] = 'No branch name was specified'
    else:
        print(f'branch: {branch}')
        db.get_db().execute(
            "INSERT INTO builds VALUES(NULL, ?, ?)", [branch, 'requested'])
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
