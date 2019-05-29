from functools import wraps
from flask import session, redirect, url_for, abort


#this dec is to check if user is a store or username
#if user abort404
#if store but didn't login go to login
def store_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('who') == 'user':
            return abort(404)
        if session.get('username') is None:
            return redirect(url_for('store_app.login'))
        return f(*args, **kwargs)
    return decorated_function
