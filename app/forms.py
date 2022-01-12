from flask_wtf import FlaskForm
import wtforms
import wtforms.validators
from flask_babel import _, lazy_gettext as _l
from app import models

class LoginForm(FlaskForm):
    username = wtforms.StringField(_l('Username'), validators=[wtforms.validators.DataRequired()])
    password = wtforms.PasswordField(_l('Password'), validators=[wtforms.validators.DataRequired()])
    remember_me = wtforms.BooleanField(_l('Remember me'))
    submit = wtforms.SubmitField(_l('Sign in'))

class RegistrationForm(FlaskForm):
    username = wtforms.StringField(_l('Username'), validators=[wtforms.validators.DataRequired()])
    email = wtforms.StringField(_l('Email'), validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email()
    ])
    password = wtforms.PasswordField(_l('Password'), validators=[wtforms.validators.DataRequired()])
    password2 = wtforms.PasswordField(
        _l('Repeat password'), validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.EqualTo('password')
        ])

    submit = wtforms.SubmitField(_l('Register'))

    def validate_username(self, username):
        user = models.User.query.filter_by(username=username.data).first()
        if user is not None:
            raise wtforms.validators.ValidationError(_('Username already taken.'))
    
    def validate_email(self, email):
        user = models.User.query.filter_by(email=email.data).first()
        if user is not None:
            raise wtforms.validators.ValidationError(_('Email already in use.'))

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

class ResetPasswordRequestForm(FlaskForm):
    email = wtforms.StringField(_l('Email'), validators=[
        wtforms.validators.DataRequired(), wtforms.validators.Email()
    ])
    submit = wtforms.SubmitField(_l('Request password reset'))

class ResetPasswordForm(FlaskForm):
    password = wtforms.PasswordField(_l('Password'), validators=[wtforms.validators.DataRequired()])
    password = wtforms.PasswordField(
        _l('Repeat Password'), validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.EqualTo('password')
        ]
    )
    submit = wtforms.SubmitField(_l('Reset your password'))
