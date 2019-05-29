from flask import Blueprint, render_template, redirect, session, url_for, abort, request

from stores.models import Store
from core.models import SendNumber, File_Record
from admin_tool.form import LoginForm
from admin_tool.decorators import admin_login_required

console_app = Blueprint('console_app', __name__)


#admin login
@console_app.route('/console/login/10726629', methods=('GET','POST'))
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if form.username.data == 'hammer2383' and form.password.data == 'Hiotqix009':
            session['who'] = 'admin'
            return redirect(url_for('console_app.journal'))
    return render_template('console/login.html', form = form)

@console_app.route('/console/logout', methods=('GET','POST'))
@admin_login_required
def logout():
    session.pop('who')
    return redirect(url_for("console_app.login"))


#this is admin tool to view every store
@console_app.route('/console/journal/store/<store_id>', endpoint='store-rec')
@console_app.route('/console/journal/', methods=('GET','POST'))
@admin_login_required
def journal(store_id=None):
    detail = False
    store = ''
    dayrecord = ''
    endrecord = ''
    #get all store objects
    all_store = Store.objects.all()

    if 'store' in request.url:
        detail = True
        store = Store.objects.filter(id = store_id).first()
        dayrecord = SendNumber.objects.filter(name = 'dayrecord', for_who = store_id).order_by('-date_time')
        endrecord = SendNumber.objects.filter(name = 'endrecord', for_who = store_id).first()

    return render_template('console/console_journal.html', stores = all_store,
                                                   dayrec = dayrecord,
                                                   endrec = endrecord,
                                                   store = store,
                                                   detail = detail)


@console_app.route('/console/journal/rec/<store_id>/<object_id>', methods=('GET','POST'))
@admin_login_required
def detail(store_id,object_id):
    store = Store.objects.filter(id = store_id).first()
    if store:
        #get file record
        file_recs = File_Record.objects.filter(to_store = store, parent=object_id).order_by('-int_time')
        day_rec = SendNumber.objects.filter(id = object_id).first()
        apday_rec = SendNumber.objects.filter(date_time = day_rec.date_time, name = 'approve dayrecord').first()
        sum = apday_rec.sale
        return render_template('console/detail_journal.html', file_recs = file_recs,
                                                              sum = sum)
    else:
        abort(404)
