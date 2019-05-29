from functools import wraps
from flask import session, abort


#this dec is to check if user is a store or username
#if user abort404
#if store but didn't login go to login
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('who') == 'user' or session.get('who') == 'store':
            return abort(404)
        return f(*args, **kwargs)
    return decorated_function
