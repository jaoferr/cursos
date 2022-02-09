import flask
import flask_login
import werkzeug.urls
from flask_babel import _, get_locale
from app.auth import blueprint
import app.auth.forms as auth_forms
import app.auth.email as auth_email
from app import models, db



@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if flask_login.current_user.is_authenticated:  # if user is already logged in go to index
        return flask.redirect(flask.url_for('main.index'))

    form = auth_forms.LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=form.username.data).first()  # get username from db

        if user is None or not user.check_password(form.password.data):  # check password
            flask.flash(_('Invalid username or password'))
            return flask.redirect(flask.url_for('auth.login'))
        
        flask_login.login_user(user, remember=form.remember_me.data)
        # goes back to page that required login
        next_page = flask.request.args.get('next')
        if not next_page or werkzeug.urls.url_parse(next_page).netloc != '':
            next_page = flask.url_for('main.index')

        return flask.redirect(next_page)

    return flask.render_template('auth/login.html', title=_('Sign in'), form=form)

@blueprint.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('main.index'))

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.index'))

    form = auth_forms.RegistrationForm()
    if form.validate_on_submit():
        user = models.User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flask.flash(_('Registration confirmed!'))
        return flask.redirect(flask.url_for('auth.login'))
    return flask.render_template('auth/register.html', title=_('Register'), form=form)

@blueprint.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.index'))
    
    form = auth_forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user:
            auth_email.send_password_reset_email(user)
        
        flask.flash(_('Check your email.'))
        return flask.redirect(flask.url_for('auth.login'))
    
    page = flask.render_template('auth/reset_password_request.html', title=_('Reset password'), form=form)
    return page

@blueprint.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('main.index'))

    user = models.User.verify_reset_password_token(token)
    if not user:
        return flask.redirect(flask.url_for('main.index'))
    
    form = auth_email.ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flask.flash(_('Password successfully reset.'))
        return flask.redirect(flask.url_for('auth.login'))
    
    return flask.render_template('auth/reset_password.html', form=form)
