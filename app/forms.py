from wtforms import Form, BooleanField, RadioField, TextField,\
    IntegerField, StringField, PasswordField, validators
from wtforms.widgets import TextArea


class ZipForm(Form):
    zip = TextField('Zip: ', [
        validators.Length(min=5, max=5,
                          message="Zip codes must be five (5) characters long.")])

    
