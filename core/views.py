from flask import Blueprint, render_template, redirect, session, url_for, abort, request, jsonify
from werkzeug import secure_filename
import os
from mongoengine import Q


from core.models import Relationship, File, SendNumber
from core.forms import StoreSearch, UpLoadForm, FileDetail
from stores.models import Store
from user.models import User, Notification, Tail
from user.decorators import login_required
from settings import UPLOAD_FOLDER_FILES
from utilities.naming import download_naming, name_tag
from utilities.common import utc_now_ts as now


core = Blueprint('core', __name__)

#view after loged in
@core.route('/allstore', methods=('GET','POST'))
@login_required
def allstore():
    logged_user = None
    error = None
    form = StoreSearch()
    logged_user = User.objects.filter(email = session.get('email')).first()
    if form.validate_on_submit():
        s_code = Store.objects.filter(storecode = form.storecode.data).first()
        if s_code:
            code = s_code.storecode
            return redirect(url_for('store_app.store_front', storecode = code))
        else:
            error = "storecode ไม่ถูกต้อง"
    #get relationship object filtered by what_user and rel_type
    met_stores = Relationship.objects.filter(what_user=logged_user,
                                            rel_type= Relationship.MET)

    return render_template('home/home.html',form=form,
                                            met_stores=met_stores,
                                            error = error)

#upload page##
#storehome page from userend
@core.route('/home/<storecode>', methods=('GET','POST'))
@login_required
def store_end(storecode):
    form = UpLoadForm()
    logged_user = User.objects.filter(email = session.get('email')).first()
    # get store from storecode
    store = Store.objects.filter(storecode= storecode).first()
    if store:
        form2 = FileDetail()
        #get choice for uploading file for store data
        form2.size.choices = store.pages

        #get that has status "pending"
        pending_files = File.objects.filter(Q(status = File.PRINTING) | Q(status = File.PENDING), to_store = store, from_user = logged_user).order_by('create_date')
        pending_total = pending_files.count()
        #get that has status "printed"
        printed_files = File.objects.filter(from_user = logged_user, to_store = store, status = File.DONE).order_by('create_date')
        printed_total = printed_files.count()

        #sending static notification
        notification = Notification.objects.filter(user_id = logged_user.id).first()
        #send relationship
        rel = Relationship.get_verification(logged_user, store)

        return render_template('home/userend_store.html', form=form,
                                                          form2 = form2,
                                                          pending_files = pending_files,
                                                          printed_files = printed_files,
                                                          store = store,
                                                          notification = notification,
                                                          pending_total = pending_total,
                                                          printed_total = printed_total,
                                                          rel = rel,
                                                          store_status = store.status
                                                           )
    else:
        return abort(404)
#this function is for upload files
@core.route('/file/upload', methods=('GET','POST'))
@login_required
def upload():
    ref = request.referrer
    form = UpLoadForm()
    store = Store.objects.get(storecode = request.values.get('to_store'))
    form2 = FileDetail()
    form2.size.choices = store.pages
    logged_user = User.objects.filter(email = session.get('email')).first()
    if form.validate_on_submit():
        if request.files.get('files'):

            #set a set_record for how many user have upload
            #this will store SendNumber instance in rec
            rec = SendNumber.set_record('upload', store.id)

            #get file number from how many time its has uploaded
            send_num = rec.get_rec()
            t_filename = secure_filename(form.files.data.filename)
            #create new filename
            filename = download_naming(send_num,
                                       form2.color.data,
                                       form2.size.data,
                                       form2.descp.data,
                                       logged_user.username,
                                       t_filename)

            filepath = os.path.join(UPLOAD_FOLDER_FILES, filename)
            form.files.data.save(filepath)

            file = File(
                file = filename,
                file_tn = t_filename,
                clr = form2.color.data,
                size = form2.size.data,
                descp = form2.descp.data,
                from_user = logged_user,
                to_store = store
            )
            file.save()

            #send notification to store that file had uploaded
            store.add_notification('uncheck_notification', 'recieved file, please refresh the page')
            #save name tag for calling in html (T+username+id)
            file.file_tag = name_tag(file.to_store.username, file.id)
            file.save()

        file = None
        if ref:
            return redirect(ref)
        else:
            #redirec to storeend instead
            return redirect(url_for('core.store_end', storecode = store.storecode))
    else:
        return "'jpg','jpeg','png','gif','pdf','docx' ที่นั้นรับ"


@core.route('/<file>/approved', methods=('GET','POST'))
@login_required
def pay_approve(file):
    ref = request.referrer
    file = File.objects.get(file = file)
    store = file.to_store
    file.approve = File.APPROVED

    #set a record for how many user have paid to this store
    SendNumber.set_record('upload', store.id)

    file.save()
    store.add_notification('uncheck_notification', 'Payment Approved, Please refresh')
    if ref:
        return redirect(ref)
    else:
        redirect(url_for('core.allstore'))


@core.route('/<file>/approved_end', methods=('GET','POST'))
@login_required
def pay_approve_end(file):
    ref = request.referrer
    file = File.objects.get(file = file)
    store = file.to_store
    file.approve = File.APPROVED_END

    #set a record for how many user have paid to this store
    SendNumber.set_record('approved', store.id)

    file.save()
    store.add_notification('uncheck_notification', 'Payment Approved, Please refresh')
    if ref:
        return redirect(ref)
    else:
        redirect(url_for('core.allstore'))


# @core.route('/testing')
# def index():
#     return render_template('store/test2.html')
#
# @core.route('/process', methods=['POST'])
# def process():
#
#     email = request.form['email']
#     name = request.form['name']
#
#     if name and email:
#         newName = f'{name} fuckyeahhh'
#         return jsonify({'name' : newName})
#     return jsonify({'error' : 'Missing data!'})


#this will delete every notification
@core.route('/reload_page')
def reload():
    ref = request.referrer
    current_user = User.objects.filter(email = session.get('email')).first()
    Notification.objects.filter(user_id = current_user.id).delete()
    Tail.objects.filter(user = current_user.id).delete()
    if ref:
        return redirect(ref)
    else:
        return redirect(url_for('core.store_end'))

@core.route('/reload_page_store')
def reload_st():
    ref = request.referrer
    current_user = Store.objects.filter(username = session.get('username')).first()
    Notification.objects.filter(user_id = current_user.id).delete()
    Tail.objects.filter(user = current_user.id).delete()
    if ref:
        return redirect(ref)
    else:
        return redirect(url_for('store_app.home_store'))


#this will work with js in hmtl
#this will send notification to user every 2s
#for user
@core.route('/notification')
def notification():
    ping = True
    current_user = User.objects.filter(email = session.get('email')).first()

    noti = Notification.objects.filter(user_id = current_user.id).first()

    if noti:
        #look for if there is any Tail
        assert current_user.id

        pre = Tail.objects.filter(noti = noti.id, user = current_user.id).first()
        if not pre:
            pre = Tail(noti = noti.id, user = current_user.id, pre = noti.get_message())
            pre.save()
        elif noti.get_message() == pre.pre:
            ping = False

        return jsonify([{
            'name': noti.name,
            'notice': noti.get_message(),
            'isping' : ping
            }])
    else:
        return jsonify([{
            'name': None,
            'notice': None,
            'isping' : False
            }])

#for store
@core.route('/notification_store')
def notification_store():
    ping = True
    current_user = Store.objects.filter(username = session.get('username')).first()
    assert current_user
    noti = Notification.objects.filter(user_id = current_user.id).first()
    assert current_user

    if noti:
        #look for if there is any Tail
        assert current_user.id

        pre = Tail.objects.filter(noti = noti.id, user = current_user.id).first()
        if not pre:
            pre = Tail(noti = noti.id, user = current_user.id, pre = noti.get_message())
            pre.save()
        elif noti.get_message() == pre.pre:
            ping = False

        return jsonify([{
            'name': noti.name,
            'notice': noti.get_message(),
            'isping' : ping
            }])
    else:
        return jsonify([{
            'name': None,
            'notice': None,
            'isping' : False
            }])

#this is delete file function after user cancle
#check first if file is printing
@core.route('/usercancle/<file>')
def cancle(file):
    ref = request.referrer
    file = File.objects.filter(file = file).first()
    store = file.to_store
    store.add_notification('uncheck_notification', f'file {file.file} has been Deleted, Please refresh')
    #create record
    file.file_record('user cancle')
    file.delete()
    os.remove(os.path.join(UPLOAD_FOLDER_FILES, file.file))
    #send notification to store_end
    if ref:
        return redirect(ref)
    else:
        return redirect(url_for('core.store_end', storecode = store.storecode))

#send verification request to store
@core.route('/request_verification/<storecode>')
def request_veri(storecode):
    ref = request.referrer
    store = Store.objects.filter(storecode = storecode).first()
    logged_user = User.objects.filter(email = session.get('email')).first()
    if store:
        rel = Relationship.objects.filter(what_user=logged_user, what_store = store).first()
        rel.verify = Relationship.PENDING
        rel.request_date = now()
        rel.save()
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('core.store_end', storecode = storecode))
    else:
        abort(404)

#create notification system that notify user of message
#it will show how many message user have
#
# @core.route('/send_message', methods = ('GET','POST'))
# def send_message():
#     form = MessageForm()
#     end_user = User.objects.filter(email = form.to_user.data).first()
#     sender = User.objects.filter(email = session.get('email')).first()
#     #save message and add Notification
#     if form.validate_on_submit():
#         message = Message(sender = sender,
#                           recipient = end_user,
#                           message = form.message.data)
#         message.save()
#         end_user.add_notification('uncheck_notification', 'Fuck you bitchhhh')
#         return redirect(url_for('core.send_message'))
#     return render_template('store/test2.html', form = form,
#                                                 logged = sender)
#
