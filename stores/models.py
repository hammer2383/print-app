from application import db
from flask import url_for
from utilities.common import utc_now_ts as now
from settings import STATIC_IMAGE_URL, AWS_BUCKET, AWS_CONTENT_URL
import os
import json

from user.models import Notification


class Store(db.Document):

    OPEN = 1
    AWAY = 0
    CLOSED = 2

    STATUS_TYPE = (
        (OPEN, 'Opening'),
        (CLOSED, 'Closed'),
        (AWAY, 'Away'))

    storename = db.StringField(db_field="sn", default=None, unique=True)
    username = db.StringField(db_field="u", required=True, unique=True)
    password = db.StringField(db_field="pwd", required=True)
    store_image = db.StringField(db_field="si", default=None)
    qr_image = db.StringField(db_field="qr", default=None)
    status = db.IntField(db_field="st", choices=STATUS_TYPE, default=CLOSED)
    created = db.IntField(db_field="c", default=now())
    storecode = db.StringField(db_field="sc", unique=True, required=True)
    email = db.StringField(db_field="em")
    pageprize = db.DictField(db_field='pp')
    pages = db.ListField(db_field='p')

    #store user ,name, and message for use to notify store
    #store message as str
    def add_notification(self, name, data):
        Notification.objects.filter(name = name, user_id = self.id).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user_id = self.id)
        n.save()
        return n

    def store_imgsrc(self,size):
        #This models function take size as parameter
        #then return a path base on storename and size
        #file name is base on Thumbnail_process()
        if self.store_image:
            if AWS_BUCKET:
                return os.path.join(AWS_CONTENT_URL, AWS_BUCKET, 'store', '%s.%s.%s.jpg' % (self.storecode, self.store_image, size)).replace("%5C", "/")  #Locate img location and have size as parameter for using in different templates
            else:
                return url_for('static', filename=os.path.join(STATIC_IMAGE_URL, 'store', '%s.%s.%s.jpg' % (self.storecode, self.store_image, size))).replace("%5C", "/")
        else:
            return url_for('static', filename = os.path.join('assets','default_image','logo-store-png.png')).replace('%5C','/')

    def owner_imgsrc(self,size):
        #This models function take size as parameter
        #then return a path base on owner and size
        #file name is base on Thumbnail_process()
        if self.qr_image:
            if AWS_BUCKET:
                return os.path.join(AWS_CONTENT_URL, AWS_BUCKET, 'owner', '%s.%s.jpg' % (self.storecode, self.qr_image)).replace('%5C','/')  #Locate img location and have size as parameter for using in different templates
            else:
                return url_for('static', filename=os.path.join(STATIC_IMAGE_URL, 'owner', '%s.%s.%s.jpg' % (self.storecode, self.qr_image, size))).replace('%5C','/')
        else:
            return url_for('static', filename = os.path.join('assets','default_image','non-qr.png')).replace('%5C','/')

    meta = {
        'indexes': ['storecode', 'username', '-created', 'status']
    }




