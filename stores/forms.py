from flask_wtf import FlaskForm as Form
from wtforms import validators, StringField, PasswordField, SelectMultipleField, FormField
from wtforms.fields.html5 import EmailField
from wtforms.validators import ValidationError
from flask_wtf.file import FileField, FileAllowed
import re
from wtforms.widgets import CheckboxInput

from stores.models import Store

class OwnerBase(Form):
    storename = StringField('Storename', [validators.DataRequired(),
                                        validators.length(min=4, max=60)])
    username = StringField('Username', [validators.DataRequired(),
                                        validators.length(min=4, max=60)])

    store_image = FileField('Store Front', validators=[FileAllowed(['jpg','png','jpeg','gif'],'Only JPEG, PNG, JPG ,GIF')])

    owner_image = FileField('QR image', validators=[FileAllowed(['jpg','png','jpeg','gif'],'Only JPEG, PNG, JPG ,GIF')])

    email = EmailField('Email Adress', [validators.Email(),validators.optional()])

class PasswordBaseForm(Form):
    password = PasswordField('Password', [validators.DataRequired(),
                                         validators.EqualTo('confirm', message='Password does\'t match')])
    confirm = PasswordField('Confirm your password', [validators.DataRequired()])


class OwnerRegister(OwnerBase,PasswordBaseForm):

    code = StringField('Code', [validators.DataRequired()])
    storecode = StringField('Store code', [validators.DataRequired(),
                                        validators.length(min=4, max=60)])
##validate username#####

    def validate_username(form, field):
        if Store.objects.filter(username=field.data).first():
            raise ValidationError("Username already exists")
        if not re.match("^[a-zA-Z0-9_-]{4,25}$",field.data):
            raise ValidationError("Invalid username")

    def validate_email(form, field):
        if Store.objects.filter(email=field.data).first():
            raise ValidationError("Email already exists")

###validate storecode####
    def validate_storecode(form, field):
        if Store.objects.filter(storecode=field.data).first():
            raise ValidationError("Code already exists")
        if not re.match("^[a-zA-Z0-9_-]{4,25}$",field.data):
            raise ValidationError("Invalid Code")

    def validate_storename(form, field):
        if Store.objects.filter(storename=field.data).first():
            raise ValidationError("Storename already exists")
            

class PrizeForm(Form):
    bw_prize = StringField('BW',default = '-')
    clr_prize = StringField('Color',default = '-')
    

class Pagesize(Form):
    A0 = FormField(PrizeForm, default = '-')
    A1 = FormField(PrizeForm, default = '-')
    A2 = FormField(PrizeForm, default = '-')
    A3 = FormField(PrizeForm, default = '-')
    A4 = FormField(PrizeForm, default = '-')
    A5 = FormField(PrizeForm, default = '-')


class PageForm(Form):
    size = SelectMultipleField('Paper\'s size',choices=[('A0','A0'),
                                                        ('A1','A1'),
                                                        ('A2','A2'),
                                                        ('A3','A3'),
                                                        ('A4','A4'),
                                                        ('A5','A5'),
                                                        ],option_widget=CheckboxInput())


class LoginForm(Form):
    username = StringField('Username',[validators.Required(),
                                       validators.length(min=4, max=25)])
    password = PasswordField('Password',[validators.Required(),
                                       validators.length(min=4, max=80)])


class PrizingForm(Form):
    prize = StringField('ราคา')
