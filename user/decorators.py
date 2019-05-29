from functools import wraps
from flask import session, request, redirect, url_for
from user.models import User

def login_required(f):
    @wraps(f)
    #also check if user have username
    def decorated_function(*args, **kwargs):
        user = User.objects.filter(email=session.get('email')).first()
        if session.get('who') == 'store':
            return redirect(url_for('store_app.home_store'))            
        elif user and user.username is None:
            return redirect(url_for('user_app.set_username'))
        elif session.get('email') is None:
            return redirect(url_for('user_app.login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function
