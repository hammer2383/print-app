from flask import Blueprint, render_template, redirect, session, url_for, request, abort
from werkzeug.security import generate_password_hash,check_password_hash
from werkzeug import secure_filename
import os
from mongoengine import Q

from settings import UPLOAD_FOLDER_IMG, UPLOAD_FOLDER_FILES
from stores.forms import OwnerRegister, LoginForm, OwnerBase, Pagesize, PrizingForm
from stores.models import Store
from utilities.imaging import thumbnail_process
from user.models import User
from core.models import Relationship, File, SendNumber, File_Record
from stores.decorators import store_login_required
from user.decorators import login_required
from user.models import Notification

store_app = Blueprint('store_app',__name__)

@store_app.route('/store_register', methods = ('GET', 'POST'))
def register():
    form = OwnerRegister()
    error = None
    if form.validate_on_submit():
        stimage_ts = None
        image_ts = None
        hash_pwd = generate_password_hash(form.password.data)
        if form.code.data == '10726629':
            ####save store_image#####
            if request.files.get('store_image'):
                #securing file's name
                filename = secure_filename(form.store_image.data.filename)
                #pathing
                file_path = os.path.join(UPLOAD_FOLDER_IMG, 'store', filename)
                #save image to path
                form.store_image.data.save(file_path)
                #image_ts=image name for img_src function to find images
                stimage_ts = str(thumbnail_process(file_path, 'store', str(form.storecode.data)))
            if request.files.get('owner_image'):
                #securing file's name
                filename = secure_filename(form.owner_image.data.filename)
                #pathing
                file_path = os.path.join(UPLOAD_FOLDER_IMG, 'owner', filename)
                #save image to path
                form.owner_image.data.save(file_path)
                #image_ts=image name for img_src function to find images
                image_ts = str(thumbnail_process(file_path, 'owner', str(form.storecode.data)))

            store = Store(
                username=form.username.data,
                password=hash_pwd,
                email = form.email.data,
                storename=form.storename.data,
                storecode=form.storecode.data
            )

            if stimage_ts:
                store.store_image = stimage_ts

            if image_ts:
                store.qr_image = image_ts
            store.save()

            return redirect(url_for('store_app.login'))
        else:
            error = 'Wrong code'

    return render_template('store/o_register.html', form=form, error=error)


###normal login function######
@store_app.route('/store_login', methods = ('GET', 'POST'))
def login():
    form = LoginForm()
    error = None
    s = True
    if session.get('email'):
        return redirect(url_for('user_app.home_store'))
    else:
        if form.validate_on_submit():
            store = Store.objects.filter(username = form.username.data).first()
            if store:
                if check_password_hash(store.password, form.password.data):
                    session['username'] = form.username.data
                    session['who'] = 'store'
                    return redirect(url_for('store_app.home_store'))
                else:
                    store = None
            if not store:
                error = "Wrong username or password"
        return render_template('store/o_login.html', form=form, error=error, s=s)

#####################################################
##this is home view that receive and dowload file
#for store end
####################################################
@store_app.route('/store/home', methods=('GET','POST'))
@store_login_required
def home_store():
    form = PrizingForm()
    store = Store.objects.filter(username = session.get('username')).first()
    pending_files = File.objects.filter(to_store = store, status = File.PENDING, approve = File.UNAPPROVE).order_by('create_date')
    paid_files = File.objects.filter(Q(approve = File.APPROVED) | Q(approve = File.APPROVED_END),to_store = store, status = File.PENDING).order_by('create_date')
    printing_files = File.objects.filter(to_store = store, status = File.PRINTING).order_by('create_date')
    printed_files = File.objects.filter(to_store = store, status = File.DONE).order_by('-create_date')
    notification = Notification.objects.filter(user_id = store.id).first()
    request_count = Relationship.objects.filter(what_store = store, verify = Relationship.PENDING).count()

    return render_template('store/home_store.html', store = store,
                                                    form = form,
                                                    pend_count = pending_files.count(),
                                                    paid_count = paid_files.count(),
                                                    printing_count = printing_files.count(),
                                                    printed_count = printed_files.count(),
                                                    pending_files = pending_files,
                                                    paid_files = paid_files,
                                                    printing_files = printing_files,
                                                    printed_files = printed_files,
                                                    notification = notification,
                                                    request_count = request_count,
                                                    status = store.status)

#this change store status open/close
@store_app.route('/store/open_close/<int:status>', methods=('GET','POST'))
def open_close(status):
    ref = request.referrer
    store_status = status
    store = Store.objects.filter(username = session.get('username')).first()
    store.status = store_status
    store.save()
    if ref:
        return redirect(ref)
    else:
        return redirect(url_for('store_app.home_store'))
# set prize
# with simple form
@store_app.route('/file/przing', methods = ('GET','POST'))
@store_login_required
def prizing():
    ref = request.referrer
    form = PrizingForm()
    if form.validate_on_submit():
        file = File.objects.get(file = request.values.get('file'))
        file.prize = str(int(form.prize.data) + 1)
        end_user = file.from_user
        file.save()
        end_user.add_notification('uncheck_notification', 'ร้านได้คิดเงินแล้ว กรุณาคลิกที่นี่เพื่อโหลดหน้าใหม่')
        if ref:
            return redirect(ref)
        else:
            redirect(url_for('core.allstore'))


#CHANGE FILE STATUS
#change back to pending
@store_app.route('/<file>/<status>', methods=('GET','POST'))
@store_login_required
def change_st(file, status):
    ref = request.referrer
    file = File.objects.filter(file = file).first()
    if file:
        file.status = int(status)
        end_user = file.from_user
        file.save()
    #check if file is printed
    if int(status) == -1:
        end_user.add_notification('uncheck_notification', 'ไฟล์ของคุณได้ทำการปริ้นแล้วเรียบร้อย')
    elif int(status) == 0:
        end_user.add_notification('uncheck_notification', 'ไฟล์ของคุณกำลังปริ้น')

    if ref:
        return redirect(ref)
    else:
        redirect(url_for('core.allstore'))

##########################################################################
###########store front that display store image and pagesprize###########
#########################################################################
#can be access freely
@store_app.route('/store/front/<storecode>', methods=('GET','POST'))
def store_front(storecode):
    store = Store.objects.filter(storecode = storecode).first()
    Pages = [('A0'), ('A1'), ('A2'), ('A3'), ('A4'), ('A5')]
    bw = []
    clr = []
    ##########show pages prize and both bw and clr prize to store_card.html##############
    if store:
        for Page in Pages:
            #store each prize for each Pages in list
            bw.append(store.pageprize.get(Page,{}).get('bw_prize','-'))
            clr.append(store.pageprize.get(Page,{}).get('clr_prize','-'))
            # st
        return render_template('store/store_card.html', store = store, bw = bw, clr = clr, Pages = Pages)
    else:
        return "404"

@store_app.route('/mystore')
@store_login_required
def mystore():
    #this is for nav bar since we don't want to store storecode in session
    #this is just redirect to store_front function with storecode as variable
    store = Store.objects.filter(username = session.get('username')).first()
    storecode = store.storecode
    return redirect(url_for('store_app.store_front', storecode = storecode))

#this function lets user view store_front
#if it is a first time user viewed the store it will automaticly add store
@store_app.route('/addstore/<storecode>', methods=('GET','POST'))
@login_required
def add_store(storecode):
    #get store objects form stoercode
    store = Store.objects.filter(storecode = storecode).first()
    #get logged user
    user = User.objects.filter(email = session.get('email')).first()
    #check Relationship
    rel = Relationship.objects.filter(what_user=user, what_store=store).first()
    #if never met
    if rel is None:
        Relationship(
            what_user=user,
            what_store=store,
            rel_type=Relationship.MET
        ).save()
        # return "redirect(url_for('store_app.store_page'))"
        return redirect(url_for('core.store_end', storecode = storecode))
    #if already met
    elif rel:
        return redirect(url_for('core.store_end', storecode = storecode))
    else:
        return abort(404)

@store_app.route('/store/edit', methods=('GET','POST'))
@store_login_required
def edit():
    error = None
    message = None
    store = Store.objects.filter(username = session.get('username')).first()
    if store:
        form = OwnerBase(obj=store)
        if form.validate_on_submit():
            #check if  there is any image upload
            stimage_ts = None
            image_ts = None
            if request.files.get('store_image'):
                if store.store_image:
                    sizes = ["sm","lg","raw"]
                    for size in sizes:
                        filename = '%s.%s.%s.jpg' % (store.storecode, store.store_image, size)
                        os.remove(os.path.join(UPLOAD_FOLDER_IMG, 'store', filename))
                #securing file's name
                filename = secure_filename(form.store_image.data.filename)
                #pathing
                file_path = os.path.join(UPLOAD_FOLDER_IMG, 'store', filename)
                #save image to path
                form.store_image.data.save(file_path)
                #image_ts=image name for img_src function to find images
                stimage_ts = str(thumbnail_process(file_path, 'store', str(store.storecode)))
            if request.files.get('owner_image'):
                if store.qr_image:
                    sizes = ["sm","lg","raw"]
                    for size in sizes:
                        filename = '%s.%s.%s.jpg' % (store.storecode, store.qr_image, size)
                        os.remove(os.path.join(UPLOAD_FOLDER_IMG, 'owner', filename))
                #securing file's name
                filename = secure_filename(form.owner_image.data.filename)
                #pathing
                file_path = os.path.join(UPLOAD_FOLDER_IMG, 'owner', filename)
                #save image to path
                form.owner_image.data.save(file_path)
                #image_ts=image name for img_src function to find images
                image_ts = str(thumbnail_process(file_path, 'owner', str(store.storecode)))
            ##########################################################################
            #########check if uesrname and email existed or just in lower case#######
            if store.username != form.username.data.lower():
                    if Store.objects.filter(username = form.username.data.lower()).first():
                        error = "Username already exists"

                    else:
                        session['username'] = form.username.data.lower()
                        form.username.data = form.username.data.lower()

            if form.email.data != '':
                if store.email != form.email.data.lower():
                    if Store.objects.filter(email=form.email.data.lower()).first():
                        error = "Email already exists"
                    else:
                        form.email.data = form.email.data.lower()

            if not error:
                form.populate_obj(store)
                if stimage_ts:
                    store.store_image = stimage_ts

                if image_ts:
                    store.qr_image = image_ts
                store.save()
                if not message:
                    message = "Store updated"
                    return redirect(url_for('store_app.store_front', storecode = store.storecode))
        return render_template('store/edit.html', form = form, store = store)
    else:
        abort(404)

#edit page prize function
@store_app.route('/store/edit/pages', methods=('GET','POST'))
@store_login_required
def page_prize():
    form = Pagesize()
    store = Store.objects.filter(username = session.get('username')).first()

    #if more pages were added Pagesize will need to be add manually
    Pages = [('A0'), ('A1'), ('A2'), ('A3'), ('A4'), ('A5')]
    if form.validate_on_submit():
        pritntpage = []
        printchoice = []
        pages = {}
        ####get and store data as dict###########################################################
        ###{"size":{"bw":"przie","clr":"prize"},"size2":{"bw":"prize","clr":"prize"}}###########
        #######################################################################################
        pagesprizes = {}
        for Page in Pages:
            #####get attribute form form########
            p = getattr(form, Page)
            pagesprizes[Page] = {"bw_prize": p.bw_prize.data,
                                 "clr_prize": p.clr_prize.data}

        #filter out none data to store in Store and use in fileform
        pages = {k: v for k, v in pagesprizes.items() if v["bw_prize"] != '-' and v["clr_prize"] != '-'}
        pritntpage = list(pages.keys())
        printchoice = [(int(v.replace("A","")), v) for v in pritntpage]
        store.pageprize = pagesprizes
        store.pages = printchoice
        store.save()

        return render_template('store/pages_prize.html', form = form, store = store)
    #populate pageprize form
    elif request.method == 'GET':
        #check  if pageprize didn't empty
        if store.pageprize != {''}:
            for Page in Pages:
                #####get attribute form Pagesize Form#######
                #p is form.page
                p = getattr(form, Page)
                #######use double get method to get each prize in nested dict ###########
                p.bw_prize.data = store.pageprize.get(Page,{}).get('bw_prize','-')
                p.clr_prize.data = store.pageprize.get(Page,{}).get('clr_prize','-')

    return render_template('store/pages_prize.html', form = form, store = store)

#this will NUKE every file and make a log
@store_app.route('/store/done', methods=('GET','POST'))
@store_login_required
def done():
    ref = request.referrer
    store = Store.objects.filter(username = session.get('username')).first()
    files = File.objects.filter(to_store = store)

    #store all file that has been marked as DONE
    done_files = File.objects.filter(to_store = store, status=File.DONE)
    #count how many file has been DONE
    total_done_files = done_files.count()

    #sum up sale record
    sale = []
    for file in done_files:
        try:
            if isinstance(int(file.prize), int):
                sale.append(int(file.prize))
        except (ValueError, TypeError):
            sale.append(0)
    sale = sum(sale)
    #store all file that has been approved
    approved_files = File.objects.filter(Q(approve=File.APPROVED) | Q(approve=File.APPROVED_END), to_store = store)
    total_ap_files = approved_files.count()
    ap_sale = []
    for file in approved_files:
        try:
            if isinstance(int(file.prize), int):
                ap_sale.append(int(file.prize))
        except (ValueError, TypeError):
            pass
    ap_sale = sum(ap_sale)

    #this will add up a day record only DONE file would be count and make a record
    SendNumber.sum_record('endrecord', store.id, total_done_files)

    #save day record
    dayrec = SendNumber.attime_record('dayrecord', store.id, total_done_files, str(sale))
    SendNumber.attime_record('approve dayrecord', store.id, total_ap_files, str(ap_sale))

    #delete every file not just DONE file
    #this will link every file_record to the dayrecord with objid
    for file in files:
        os.remove(os.path.join(UPLOAD_FOLDER_FILES, file.file))
        #create record for each file
        if file.approve == File.APPROVED or file.approve == File.APPROVED_END:
            file.file_record('store endrecord', True, dayrec.id,)
        else:
            file.file_record('store endrecord', False, dayrec.id,)
        #then delete all
        file.delete()
    if ref:
        return redirect(ref)
    else:
        return redirect(url_for('store_app.home_store'))

# this view is to view a set_record
# endrecord an dayrecord
@store_app.route('/store/journal/detail/<objid>', endpoint='detail-rec')
@store_app.route('/store/journal/', methods=('GET','POST'))
@store_login_required
def journal(objid=None):
    logged_store = Store.objects.filter(username = session.get('username')).first()
    sum = ''
    detail = False
    file_recs = []
    dayrecord = SendNumber.objects.filter(name = 'dayrecord', for_who = logged_store.id).order_by('-date_time')[:30]
    endrecord = SendNumber.objects.filter(name = 'endrecord', for_who = logged_store.id).first()

    #this will send every file record assosicated with particular dayrecords
    if 'detail' in request.url:
        detail = True
        file_recs = File_Record.objects.filter(to_store = logged_store, parent=objid).order_by('-int_time')
        day_rec = SendNumber.objects.filter(id = objid).first()
        apday_rec = SendNumber.objects.filter(date_time = day_rec.date_time, name = 'approve dayrecord').first()
        sum = apday_rec.sale

    return render_template('store/journal.html',
        dayrec = dayrecord,
        endrec = endrecord,
        detail = detail,
        file_recs = file_recs,
        sum = sum
        )


#grant verification function
@store_app.route('/grant/<username>', methods=('GET','POST'))
@store_login_required
def grant(username):
    ref = request.referrer
    user = User.objects.filter(username = username).first()
    store = Store.objects.filter(username = session.get('username')).first()
    rel = Relationship.objects.filter(what_user = user, what_store = store).first()
    if user:
        rel.verify = Relationship.VERIFIED
        rel.save()
        if ref:
            return redirect(ref)
        else:
            return redirect(url_for('user_app.profile', useremail = user.email))
    else:
        abort(404)


#revoke verifiaction
@store_app.route('/revoke/<username>' , methods=('GET','POST'))
@store_login_required
def revoke(username):
        ref = request.referrer
        user = User.objects.filter(username = username).first()
        store = Store.objects.filter(username = session.get('username')).first()
        rel = Relationship.objects.filter(what_user = user, what_store = store).first()
        if user:
            rel.verify = Relationship.UNVERIFIED
            rel.save()
            if ref:
                return redirect(ref)
            else:
                return redirect(url_for('user_app.profile', useremail = user.email))
        else:
            abort(404)

#query every pending user
@store_app.route('/request/list', methods=('GET','POST'))
@store_login_required
def request_list():
    store = Store.objects.filter(username = session.get('username')).first()
    rel = Relationship.objects.filter(what_store = store, verify = Relationship.PENDING).order_by('-request_date')
    return render_template('store/request_list.html', rels = rel)

#this will show every user that intereacted with store
@store_app.route('/user_list', methods=('GET','POST'))
@store_login_required
def user_list():
    store = Store.objects.filter(username = session.get('username')).first()
    rel = Relationship.objects.filter(what_store = store, verify = Relationship.VERIFIED).order_by('-request_date')
    nvrel = Relationship.objects.filter(what_store = store, verify = Relationship.UNVERIFIED).order_by('-request_date')
    penrel = Relationship.objects.filter(what_store = store, verify = Relationship.PENDING).order_by('-request_date')
    rel_count = rel.count()
    nvrel_count = nvrel.count()
    penrel_count = penrel.count()
    return render_template('store/user_list.html', rels = rel,
                                                   nvrels = nvrel,
                                                   penrels = penrel,
                                                   rel_count = rel_count,
                                                   nvrel_count = nvrel_count,
                                                   penrel_count = penrel_count)
