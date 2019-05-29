from flask_wtf import FlaskForm as Form
from wtforms import StringField, validators, SelectField
from flask_wtf.file import FileField, FileAllowed
from wtforms.widgets import TextArea

class StoreSearch(Form):
    storecode = StringField('Store code')

#dynamic choice form
class UpLoadForm(Form):
    files = FileField('File', validators=[FileAllowed(['jpg','jpeg','png','gif','pdf','docx'], 'Only JPEG,PNG and GIFs allowed'),validators.DataRequired()])


class FileDetail(Form):
    size = SelectField('Paper\'s size',[validators.DataRequired()], coerce=int)
    color = SelectField('สีหรือขาวดำ', [validators.DataRequired()], choices=[(1,"Color"),
                                                                           (0,"Mono")])
    descp = StringField('Description',widget=TextArea())

class MessageForm(Form):
    message = StringField('Text')
    to_user = StringField('To_user')
