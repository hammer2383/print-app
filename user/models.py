from mongoengine import signals
from application import db
from utilities.common import utc_now_ts as now
from flask import url_for
import json
import os

from settings import STATIC_IMAGE_URL, AWS_BUCKET, AWS_CONTENT_URL


#this is Notification objects
#this will store message
class Notification(db.Document):
    name = db.StringField(db_field="n")
    user_id = db.ObjectIdField(db_field='uid')
    payload_json = db.StringField(db_field="pj")

    def get_message(self):
        return json.loads(str(self.payload_json))

    def save_tail(self):
        pre = Tail(pre = self.get_message())
        pre.save()
        return pre.pre

    meta = {
        'indexes':['user_id']
    }

class Tail(db.Document):
    pre = db.StringField(db_field="pre")
    noti = db.ObjectIdField()
    user = db.ObjectIdField()


class User(db.Document):
    username = db.StringField(db_field = 'u', unique=True)
    password = db.StringField(db_field = 'pwd')
    email = db.EmailField(db_field = 'em', required=True, unique=True)
    first_name = db.StringField(db_field="fn", max_length=50, default = None)
    last_name = db.StringField(db_field="ln", max_length=50, default = None)
    created = db.IntField(db_field='c', default=now())
    email_confirmed = db.BooleanField(db_field="ecf", default=False)
    change_configuration = db.DictField(db_field="cc")
    profile_image = db.StringField(db_field="i", default = None)
    facebook_link = db.StringField(db_field="fb")
    tel = db.StringField(db_field="tl")
    provider = db.StringField(db_field="pv", default = 'local')

    @classmethod
    def pre_save(cls, sender, document, **kwargs):  #don't understand
        if document.username:
            document.username = document.username.lower()
        document.email = document.email.lower()

    def user_imgsrc(self, size):
        if self.profile_image:
            if AWS_BUCKET:
                return os.path.join(AWS_CONTENT_URL, AWS_BUCKET, 'user', '%s.%s.%s.png' % (self.id, self.profile_image, size))
            else:
                return url_for('static', filename=os.path.join(STATIC_IMAGE_URL, 'user', '%s.%s.%s.jpg' % (self.id, self.profile_image, size))).replace("%5C","/")
        else:
            return url_for('static', filename = os.path.join('assets','default_image','default-profile.png')).replace('%5C','/')

    #Class method to add Notification delete old one
    def add_notification(self, name, data):
        Notification.objects.filter(name = name, user_id = self.id).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user_id = self.id)
        n.save()
        return n

    meta = {
        'indexes': ['username', 'email', '-created']
    }


signals.pre_save.connect(User.pre_save, sender = User)


class Message(db.Document):
    sender = db.ReferenceField(User, db_field='sds')
    recipient = db.ReferenceField(User, db_field='rc')
    message = db.StringField(db_field='ms')

    def __repr__(self):
        return f'{self.message}'
