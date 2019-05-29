from flask_wtf import FlaskForm as Form
from wtforms import validators, StringField, PasswordField
from wtforms.fields.html5 import EmailField
from flask_wtf.file import FileField, FileAllowed
from wtforms.validators import ValidationError

from user.models import User


class BaseUserForm(Form):
    username = StringField('Username',[validators.DataRequired(),
                                       validators.length(min=4, max=25)])
    email = EmailField('Email address', [validators.DataRequired(),
                                         validators.Email()])

class PasswordBaseForm(Form):
    password = PasswordField('Password', [validators.DataRequired(),
                                              validators.EqualTo('confirm', message='Password doesn\'t match'),
                                              validators.length(min=4, max = 60)])
    confirm = PasswordField('Confirm your password', [validators.DataRequired()])

class RegisterForm(BaseUserForm, PasswordBaseForm):
    def validate_username(form, field):
        if User.objects.filter(username=field.data).first():
            raise ValidationError("Username already exists")

    def validate_email(form, field):
        if User.objects.filter(email=field.data).first():
            raise ValidationError("Email already exists")


class LoginForm(Form):
    email = EmailField('Email address', [validators.DataRequired(),
                                         validators.Email()])
    password = PasswordField('Password',[validators.DataRequired(),
                                         validators.length(min=4,max=60)])

class ForgotForm(Form):
    email = EmailField('Email address', [validators.DataRequired(),
                                         validators.Email()])

class PasswordResetForm(PasswordBaseForm):
    current_password = PasswordField('Current password',
                                      [validators.DataRequired(),
                                      validators.length(min=4, max=60)])
class UsernameForm(Form):
    username = StringField('Username',[validators.DataRequired(),
                                       validators.length(min=4, max=60)])

    def validate_username(form, field):
        if User.objects.filter(username=field.data).first():
            raise ValidationError("Username already exists")


class EditForm(Form):
    username = StringField('Username',[validators.DataRequired(),
                                       validators.length(min=4, max=60)])
    image = FileField('Profile image', validators=[FileAllowed(['jpg','png','jpeg','gif'],'Only JPEG, PNG, JPG ,GIF')])
    first_name = StringField('First name',[validators.DataRequired(), validators.length(min=1,max=80)])
    last_name = StringField('Last name',[validators.DataRequired(), validators.length(min=1,max=90)])
    facebook_link = StringField('Facebook')
    tel = StringField('Tel', [validators.DataRequired(),validators.length(min=1,max=20)])
