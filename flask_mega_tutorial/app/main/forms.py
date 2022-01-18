import flask
from flask_wtf import FlaskForm
import wtforms
import wtforms.validators
from flask_babel import _, lazy_gettext as _l
from app import models


class EditProfileForm(FlaskForm):
    username = wtforms.StringField(_l('Username:'), validators=[wtforms.validators.DataRequired()])
    about_me = wtforms.TextAreaField(_l('About me'), validators=[wtforms.validators.Length(min=0, max=140)])
    submit = wtforms.SubmitField(_l('Submit'))

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = models.User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise wtforms.validators.ValidationError(_('Username is already in use.'))

class EmptyForm(FlaskForm):
    submit = wtforms.SubmitField('Submit')

class PostForm(FlaskForm):
    post = wtforms.TextAreaField(_l('Say something'), validators=[
        wtforms.validators.DataRequired(), wtforms.validators.Length(min=1, max=140)
    ])
    submit = wtforms.SubmitField(_l('Submit'))
