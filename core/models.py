from application import db
from settings import STATIC_FILE_URL
from flask import url_for
import os

from utilities.common import utc_now_ts as now, utc_now_ts_ms as nowms, human_date, human_date_ms
from user.models import User
from stores.models import Store


class Relationship(db.Document):
    MET = 1
    UNMET = 0

    RELATIONSHIP_TYPE = (
        (MET, 'met'),
        (UNMET, 'unmet'),
    )

    VERIFIED = 1
    PENDING = -1
    UNVERIFIED = 0

    VERIFY = (
        (VERIFIED, 'verified'),
        (UNVERIFIED, 'unverified'),
        (PENDING, 'pending')
    )

    what_user = db.ReferenceField(User, db_field='wh')
    what_store = db.ReferenceField(Store, db_field='wst')
    rel_type = db.IntField(db_field='rt', choices=RELATIONSHIP_TYPE)
    met_date = db.IntField(db_field='md', default=now())
    request_date = db.IntField(db_field='rd')
    verify = db.IntField(db_field = 'vf', choices=VERIFY, default=UNVERIFIED)

    def time_human(self):
        time = human_date(self.met_date)
        return time

    def is_met(self, user):
        if user:
            return self.get_relationship(user, self.what_store)
        else:
            return None

    def is_verified(self):
        return self.get_verification(self.what_user, self.what_store)

    @staticmethod
    def get_relationship(what_user, what_store):
        rel = Relationship.objects.filter(
            what_user=what_user,
            what_store=what_store).first()

        if rel and rel.rel_type == Relationship.MET:
            return "MET"
        elif rel is None:
            return "UNMET"

    @staticmethod
    def get_verification(what_user, what_store):
        rel = Relationship.objects.filter(
            what_user=what_user,
            what_store=what_store).first()

        if rel and rel.verify == Relationship.VERIFIED:
            return "VERID"

        elif rel and rel.verify == Relationship.UNVERIFIED:
            return "UNVERI"
        elif rel and rel.verify == Relationship.PENDING:
            return "PENDING"

    meta = {
        'indexes': ['what_user', 'what_store', '-met_date', 'rel_type', '-request_date']
    }

#this class will create a record of file in str
class File_Record(db.Document):
    #store email
    from_user = db.ReferenceField(User, db_field="rfu")
    #store storecodes
    to_store = db.ReferenceField(Store, db_field="rt")
    date_time = db.StringField(db_field="dt")
    int_time = db.LongField(db_field="it")
    prize = db.StringField()
    size = db.StringField()
    descp = db.StringField()
    paid = db.BooleanField()
    type = db.StringField()
    parent = db.ObjectIdField(db_field="p")

    meta = {
        'indexes': ['type','to_store','from_user','int_time']
    }


class File(db.Document):
    BW = 0
    CLR = 1

    COLOR = (
        (BW, 'BW'),
        (CLR, 'CLR')
    )

    PENDING = 1
    PRINTING = 0
    DONE = -1

    STATUS = (
        (PENDING,'Pending'),
        (PRINTING,'Printing'),
        (DONE,'Done')
    )

    APPROVED = 1
    UNAPPROVE = 0
    APPROVED_END = 2

    APPROVE = (
        (APPROVED, 'approved'),
        (UNAPPROVE, 'unapprove'),
        (APPROVED_END, 'approve_end')
    )

    file = db.StringField(db_field = "f", required=True, unique=True)
    file_tn = db.StringField(db_field = "tn")
    file_tag = db.StringField(db_field = "t")
    descp = db.StringField(db_field="d", max_length=200)
    prize = db.StringField(db_field="p")
    size = db.IntField(db_field="s", required=True)
    create_date = db.LongField(db_field="c", default=nowms())
    from_user = db.ReferenceField(User, db_field="fu")
    to_store = db.ReferenceField(Store, db_field="ts")
    clr = db.IntField(db_field="cl", choices = COLOR, required=True)
    #Status
    approve = db.IntField(db_field="ap", choices=APPROVE, default=UNAPPROVE)
    status = db.IntField(db_field='st',default=PENDING, choices=STATUS)

    #is from_user verify
    def is_from_verified(self):
        return Relationship.get_verification(self.from_user, self.to_store)

    # create file record and has a name called type to easily tell why file's record was made
    def file_record(self, type, approve = False, parent=None):

        record = File_Record(from_user=self.from_user,
                             to_store = self.to_store,
                             date_time = f'{human_date_ms(self.create_date)}',
                             prize = str(self.prize),
                             size = f'A{self.size}',
                             descp = self.descp,
                             type = type,
                             int_time = self.create_date,
                             parent = parent,
                             paid = approve)
        record.save()

    def file_src(self):
        return url_for('static', filename = os.path.join(STATIC_FILE_URL, str(self.file))).replace('%5C','/')

    meta = {
        'indexes':['file','size','to_store','from_user','clr','prize','-create_date']
    }

#this model keeptrack of number for use in filename
class SendNumber(db.Document):
    UNPAID = 0
    PAID = 1

    PAID = (
        (UNPAID, 'UP'),
        (PAID, 'PD')
    )

    name = db.StringField(db_field="name")
    number_time = db.IntField(db_field="nt")
    for_who = db.ObjectIdField(db_field="fw")
    date_time = db.IntField(db_field="dt")
    readable_date = db.StringField(db_field="rdt")
    paid = db.IntField(db_field="p", choice = PAID, default=UNPAID)
    sale = db.StringField(db_field="s")

    #add 1 each time it was called
    def add_time(self):
        self.number_time = self.number_time + 1
        self.save()

    # add up record by one
    @staticmethod
    def set_record(name, object_id):
        rec = SendNumber.objects.filter(name=name, for_who = object_id).first()
        if rec:
            rec.add_time()
            return rec
        else:
            rec = SendNumber(
                name = name,
                for_who = object_id,
                number_time = 1
            ).save()
            return rec

    def get_rec(self):
        return self.number_time

    #create a total new record
    #of course this will have the same name only different would be date
    @staticmethod
    def attime_record(name, object_id, total, sale):

        rec = SendNumber(
            name = name,
            for_who = object_id,
            number_time = total,
            date_time = now(),
            readable_date = f'{human_date(now())}',
            sale = sale
        )
        rec.save()
        return rec

    #create a total record which add up with a record that has the same name
    #or create one if it doesn't exists
    @staticmethod
    def sum_record(name, object_id, total):
        rec = SendNumber.objects.filter(name=name, for_who = object_id).first()
        if rec:
            rec.number_time = rec.number_time + total
            rec.save()
        else:
            rec = SendNumber(
                name = name,
                for_who = object_id,
                number_time = total,

            ).save()

    meta = {
        'indexes':['name','-readable_date']
    }
