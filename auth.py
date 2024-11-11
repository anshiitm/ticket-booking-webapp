from flask import request, current_app as app, jsonify, Flask, session
from functools import wraps
import jwt
from models import User, Admin
from datetime import date

def auth_token(func):
  @wraps(func)
  def wrapped(*args, **kwargs):
    headers = request.headers.get('Authentication-Token', '').split()

    invalid_token = {
            'message': 'The Token is Invalid',
            'authenticated': False
        }
    expired_msg = {
            'message': 'The Token has expired',
            'authenticated': False
        }

    if len(headers) != 1:
        return jsonify(invalid_token), 401
    
    try:
        token = headers[0]
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256', verify=True)
        # print(token)
        role = data['role']

        if role == 'admin':
           user = Admin.query.filter_by(username=data['user']).first()
           
        if role == 'user':
            user = User.query.filter_by(username=data['user']).first()
            
        if not user:
            raise RuntimeError('User not found')
        return func({"user": user, "role": role}, *args, **kwargs)
    except jwt.ExpiredSignatureError:
        return jsonify(expired_msg), 402 
    except (jwt.InvalidTokenError, Exception) as e:
        print(e)
        return jsonify(invalid_token), 403

  return wrapped
    

def admin_access(func):
   @wraps(func)
   def admin_wrapped(*args, **kwargs):
      role_info = args[0]
      role = role_info.get("role", None)
      if role != 'admin':
        return jsonify({'message': 'Only Admins can access this page'}), 401
      return func(*args, **kwargs)
   return admin_wrapped


def user_access(func):
   @wraps(func)
   def user_wrapped(*args, **kwargs):
      role_info = args[0]
      role = role_info.get("role", None)
      if role != 'user':
        return jsonify({'message': 'Only Users can access this page'}), 401
      return func(*args, **kwargs)
   return user_wrapped