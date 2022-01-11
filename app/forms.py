from flask_wtf import FlaskForm
import wtforms
import wtforms.validators
from app import models

class LoginForm(FlaskForm):
    username = wtforms.StringField('Username', validators=[wtforms.validators.DataRequired()])
    password = wtforms.PasswordField('Password', validators=[wtforms.validators.DataRequired()])
    remember_me = wtforms.BooleanField('Remember me')
    submit = wtforms.SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    username = wtforms.StringField('Username', validators=[wtforms.validators.DataRequired()])
    email = wtforms.StringField('Email', validators=[
        wtforms.validators.DataRequired(),
        wtforms.validators.Email()
    ])
    password = wtforms.PasswordField('Password', validators=[wtforms.validators.DataRequired()])
    password2 = wtforms.PasswordField(
        'Repeat password', validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.EqualTo('password')
        ])

    submit = wtforms.SubmitField('Register')

    def validate_username(self, username):
        user = models.User.query.filter_by(username=username.data).first()
        if user is not None:
            raise wtforms.validators.ValidationError('Username alreay taken.')
    
    def validate_email(self, email):
        user = models.User.query.filter_by(email=email.data).first()
        if user is not None:
            raise wtforms.validators.ValidationError('Email already in use.')

class EditProfileForm(FlaskForm):
    username = wtforms.StringField('Username:', validators=[wtforms.validators.DataRequired()])
    about_me = wtforms.TextAreaField('About me', validators=[wtforms.validators.Length(min=0, max=140)])
    submit = wtforms.SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super(EditProfileForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = models.User.query.filter_by(username=self.username.data).first()
            if user is not None:
                raise wtforms.validators.ValidationError('Username is already in use.')

class EmptyForm(FlaskForm):
    submit = wtforms.SubmitField('Submit')

class PostForm(FlaskForm):
    post = wtforms.TextAreaField('Say something', validators=[
        wtforms.validators.DataRequired(), wtforms.validators.Length(min=1, max=140)
    ])
    submit = wtforms.SubmitField('Submit')

class ResetPasswordRequestForm(FlaskForm):
    email = wtforms.StringField('Email', validators=[
        wtforms.validators.DataRequired(), wtforms.validators.Email()
    ])
    submit = wtforms.SubmitField('Request password reset')

class ResetPasswordForm(FlaskForm):
    password = wtforms.PasswordField('Password', validators=[wtforms.validators.DataRequired()])
    password = wtforms.PasswordField(
        'Repeat Password', validators=[
            wtforms.validators.DataRequired(),
            wtforms.validators.EqualTo('password')
        ]
    )
    submit = wtforms.SubmitField('Reset your password')
