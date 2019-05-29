from flask_wtf import FlaskForm as Form
from wtforms import validators, StringField, PasswordField

class LoginForm(Form):
    username = StringField('Username',[validators.Required(),
                                       validators.length(min=4, max=25)])
    password = PasswordField('Password',[validators.Required(),
                                       validators.length(min=4, max=80)])
