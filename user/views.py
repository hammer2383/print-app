from flask import render_template, session, request, abort, redirect, Blueprint, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug import secure_filename
import uuid
import os

from user.forms import RegisterForm, LoginForm, ForgotForm, EditForm, UsernameForm
from stores.models import Store
from user.models import User
from settings import UPLOAD_FOLDER_IMG
from core.models import Relationship
from utilities.common import email
from utilities.imaging import thumbnail_process
from user.decorators import login_required

user_app = Blueprint('user_app', __name__)


@user_app.route('/register', methods=('GET', 'POST'))
def register():
    form = RegisterForm()
    if request.args.get('storecode'):
        session['temp_storecode'] = request.args.get('storecode')

    # store storecode in temp_storecode session
    if form.validate_on_submit():
        code = str(uuid.uuid4())
        hash_pwd = generate_password_hash(form.password.data)
        user = User(
            username=form.username.data,
            password=hash_pwd,
            email=form.email.data,
            change_configuration={
                "new_email": form.email.data.lower(),
                "confirmation_code": code
            },
            email_confirmed=True
        )

        if session.get('temp_storecode'):
            body_html = render_template('mail/user/confirm.html', user=user, storecode = session.get('temp_storecode'))
            body_text = render_template('mail/user/confirm.txt', user=user, storecode = session.get('temp_storecode'))
        else:
            body_html = render_template('mail/user/confirm_n.html', user=user)
            body_text = render_template('mail/user/confirm_n.txt', user=user)
        email(user.email.lower(), "Email confirmation", body_html, body_text)
        user.save()
        return redirect(url_for('user_app.awaiting', user_email=form.email.data.lower()))
    return render_template('user/register.html', form=form)

##local user login##
@user_app.route('/login', methods=('GET', 'POST'))
def login():
    form = LoginForm()
    error = None
    ##check if user already logged in###
    if session.get('email') or session.get('username'):
        return redirect(url_for('user_app.home'))
    ####get next####
    if request.method == 'GET' and request.args.get('next'):
        session['next'] = request.args.get('next')
    #login
    if form.validate_on_submit():
        user = User.objects.filter(email=form.email.data).first()
        #only local user
        #this is to prevent user login without password
        if user and user.provider == 'local':
            #check if email has been confirmed
            if user.email_confirmed is False:
                error = "คุณยังไม่ได้ยืนยันอีเมล์ เช็คที่กล่องอีเมล์ของคุณดูสิ ลองดูในกล่อง spam ถ้าหาไม่เจอนะ"

            else:
                #if everything checked out
                if check_password_hash(user.password, form.password.data):
                    #put user type in session
                    session['who'] = 'user'
                    session['username'] = user.username
                    session['email'] = user.email

                    #go to home after login with username in session
                    #check if there is temp_storecode
                    if session.get('temp_storecode'):
                        storecode = session.get('temp_storecode')
                        session.pop('temp_storecode')
                        return redirect(url_for('store_app.store_front', storecode = storecode))
                    #redirect to next if any
                    elif 'next' in session:
                        next = session.get('next')
                        session.pop('next')
                        return redirect(next)
                    else:
                        return redirect(url_for('user_app.home'))
                else:
                    user = None
        #if no user or useris not local
        else:
            error = 'Wrong username or password'

    return render_template('user/login.html', form=form, error=error)

#this actually should be in core views but we're too lazy
#this let user enter an email to send email that contained a link to our website
@user_app.route('/intro/<storecode>', methods=('GET','POST'))
def intro(storecode):
    form = ForgotForm()
    if form.validate_on_submit():
        user_email = form.email.data.lower()
        body_html = render_template('mail/user/intro.html', storecode=storecode)
        body_text = render_template('mail/user/intro.txt', storecode=storecode)
        email(user_email,"Thank you for using Homing Pigeon",body_html,body_text)
        return render_template('home/welcome.html', user_email=user_email, storecode=storecode)
    return render_template('home/to_email.html', form = form, storecode = storecode)

# this is home view function
# it show all met stores
# with store seacrh on top
# dedicated to redirect
@user_app.route('/', methods = ('GET','POST'))
@login_required
def home():
    #this view is to redirect google user
    #check if google user set their username yet?
    #if not go to set_username view

    return redirect(url_for('core.allstore'))

#privacy policy
@user_app.route('/privacy')
def privacy_po():
    pass
    return render_template('legal_stuff/privacy_po.html')

#term and agreement
@user_app.route('/term')
def term():
    pass
    return render_template('legal_stuff/term_agree.html')

#set username
#this view is only for OAuth user since local user need to set username early
@user_app.route('/set_username', methods=('GET','POST'))
@login_required
def set_username():
    form = UsernameForm()
    guser = User.objects.filter(email = session.get('email')).first()
    if guser and guser.username is None:
        if form.validate_on_submit():
            guser.username = form.username.data
            guser.save()
            #use session for that we don't have to sent user
            session['username'] = guser.username
            return redirect(url_for('core.allstore'))
        return render_template('user/set_username.html', form=form)
    else:
        return redirect(url_for('user_app.login'))

#searh profile by username
@user_app.route('/profile_u/<username>')
def profile_by_u(username):
    user = User.objects.filter(username= username).first()
    if user:
        rel = ''
        username = user.username
        tel = user.tel
        fn = user.first_name
        ln = user.last_name
        user_email = user.email
        fb = user.facebook_link
        if session.get('username') and session.get('who') == 'store':
            logged_store = Store.objects.filter(username = session.get('username')).first()
            rel = Relationship.get_verification(user, logged_store)
        return render_template('user/profile.html', username = username,
                                                    tel = tel,
                                                    fn = fn,
                                                    ln = ln,
                                                    email = user_email,
                                                    fb = fb,
                                                    user = user,
                                                    rel = rel)

@user_app.route('/profile/<useremail>')
def profile(useremail=None):
    user = User.objects.filter(email= useremail).first()
    if user:
        rel = ''
        username = user.username
        tel = user.tel
        fn = user.first_name
        ln = user.last_name
        user_email = user.email
        fb = user.facebook_link
        #check if store is looking at user profile
        if session.get('username') and session.get('who') == 'store':
            logged_store = Store.objects.filter(username = session.get('username')).first()
            rel = Relationship.get_verification(user, logged_store)
        return render_template('user/profile.html', username = username,
                                                    tel = tel,
                                                    fn = fn,
                                                    ln = ln,
                                                    email = user_email,
                                                    fb = fb,
                                                    user = user,
                                                    rel = rel)
    else:
        return abort(404)

#this will check if user has confirmation_code in change_configuration
#then change email_confirmed to True
@user_app.route('/confirm/<username>/<code>', methods=('GET','POST'))
def confirm(username, code):
    user = User.objects.filter(username = username).first()
    if user and user.change_configuration.get('confirmation_code') == code:
        user.email_confirmed = True
        user.change_configuration = {}
        user.save()
        #check if there storecode it request args
        #then store storecode in session temp_storecode
        if request.args.get('storecode'):
            if session.get('temp_storecode'):
                session.pop('temp_storecode')
            session['temp_storecode'] = request.args.get('storecode')
        return render_template('user/email_confirmed.html')
    else:
        return abort(404)


@user_app.route('/awaiting/<user_email>', methods=('GET','POST'))
def awaiting(user_email):
    return render_template('user/await_confirm.html', email = user_email)

@user_app.route('/profile/edit', methods=('GET', 'POST'))
@login_required
def edit():
    error = None
    message = None
    user = User.objects.filter(email = session.get('email')).first()
    if user:
        form = EditForm()
        if form.validate_on_submit():
            # check if image
            image_ts = None
            if request.files.get('image'):
                if user.profile_image:
                    sizes = ["sm","lg","raw"]
                    for size in sizes:
                        filename = '%s.%s.%s.jpg' % (user.id, user.profile_image, size)
                        os.remove(os.path.join(UPLOAD_FOLDER_IMG, 'user', filename))
                filename = secure_filename(form.image.data.filename)
                file_path = os.path.join(UPLOAD_FOLDER_IMG, 'user', filename)
                form.image.data.save(file_path)
                image_ts = str(thumbnail_process(file_path, 'user', str(user.id)))

            if user.username != form.username.data.lower():
                if User.objects.filter(username = form.username.data.lower()).first():
                    error = "Username already exists"
                else:
                    session['username'] = form.username.data.lower()
                    user.username = form.username.data.lower()
            if not error:
                if image_ts:
                    user.profile_image = image_ts
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.facebook_link = form.facebook_link.data
                user.tel = form.tel.data
                user.save()
                if not message:
                    message = "Profile updated"
        elif request.method == 'GET':
            form.username.data = user.username
            form.facebook_link.data = user.facebook_link
            form.first_name.data = user.first_name
            form.last_name.data = user.last_name
            form.tel.data = user.tel

        return render_template("user/edit.html", form=form, error=error, message=message, user=user)
    else:
        abort(404)

#send verfication request
#grant verification function
@user_app.route('/request_verification/<storecode>', methods=('GET','POST'))
@login_required
def re_verification(storecode):
    ref = request.referrer
    user = User.objects.filter(email = session.get('email')).first()
    store = Store.objects.filter(storecode = storecode).first()
    rel = Relationship.objects.filter(what_user = user, what_store = store).first()
    if user:
        rel.verify = Relationship.PENDING
        rel.save()
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', useremail = user.email))
    else:
        abort(404)
