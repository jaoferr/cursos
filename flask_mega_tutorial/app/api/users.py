from flask import jsonify, request, url_for, abort
from app.api import blueprint
from app.models import User
from app import db
import app.api.errors as api_errors
from app.api.auth import token_auth

@blueprint.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())

@blueprint.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')

    return jsonify(data)

@blueprint.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_user_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 1, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page, 
                                   'api.get_user_followers', id=id)

    return jsonify(data)

@blueprint.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_user_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 1, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_user_followed', id=id)

    return jsonify(data)

@blueprint.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if ('username' not in data) or ('email' not in data) or ('password' not in data):
        return api_errors.bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return api_errors.bad_request('username already taken')
    if User.query.filter_by(email=data['email']).first():
        return api_errors.bad_request('email already taken')
    
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)

    return response

@blueprint.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    if token_auth.current_user().id != id:
        abort(403)
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if ('username' in data) and (data['username'] != user.username) and \
        (User.query.filter_by(username=data['username']).first()):
        return api_errors.bad_request('username already taken')

    if ('email' in data) and (data['email'] != user.email) and \
        (User.query.filter_by(email=data['email']).first()):
        return api_errors.bad_request('email already taken')
    
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())
