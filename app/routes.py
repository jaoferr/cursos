import flask
import flask_login
from flask_login.utils import login_required
import app.forms as app_forms
import app.email as app_email
from app import app
from app import models
from app import db
import werkzeug.urls
from datetime import datetime, time


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = app_forms.PostForm()
    if form.validate_on_submit():
        post = models.Post(body=form.post.data, author=flask_login.current_user)
        db.session.add(post)
        db.session.commit()
        flask.flash('Posted.')
        return flask.redirect(flask.url_for('index'))

    page = flask.request.args.get('page', 1, type=int)
    posts = flask_login.current_user.followed_posts()
    paginated_posts = posts.paginate(page, app.config['POSTS_PER_PAGE'], False)
    
    if paginated_posts.has_next:
        next_url = flask.url_for('index', page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('index', page=paginated_posts.prev_num)
    else:
        prev_url = None

    index_page = flask.render_template(
        'index.html', title='Home',
        posts=paginated_posts.items,
        form=form,
        next_url=next_url,
        prev_url=prev_url
    )
    return index_page

@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask_login.current_user.is_authenticated:  # if user is already logged in go to index
        return flask.redirect(flask.url_for('index'))

    form = app_forms.LoginForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=form.username.data).first()  # get username from db

        if user is None or not user.check_password(form.password.data):  # check password
            flask.flash('Invalid username or password')
            return flask.redirect(flask.url_for('login'))
        
        flask_login.login_user(user, remember=form.remember_me.data)
        # goes back to page that required login
        next_page = flask.request.args.get('next')
        if not next_page or werkzeug.urls.url_parse(next_page).netloc != '':
            next_page = flask.url_for('index')

        return flask.redirect(next_page)

    return flask.render_template('login.html', title='Sign in', form=form)

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return flask.redirect(flask.url_for('index'))

@app.route('/restricted')
@login_required
def restricted():
    return '<b> A restricted page </b>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('index'))

    form = app_forms.RegistrationForm()
    if form.validate_on_submit():
        user = models.User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flask.flash('Registration confirmed!')
        return flask.redirect(flask.url_for('login'))
    return flask.render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    page = flask.request.args.get('page', type=int)
    posts = user.posts.order_by(models.Post.timestamp.desc())
    paginated_posts = posts.paginate(page, app.config['POSTS_PER_PAGE'], False)

    if paginated_posts.has_next:
        next_url = flask.url_for('user', username=user.username,page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('user', username=user.username, page=paginated_posts.prev_num)
    else:
        prev_url = None

    form = app_forms.EmptyForm()

    user_page = flask.render_template(
        'user.html', user=user, posts=paginated_posts.items, form=form,
        next_url=next_url, prev_url=prev_url
    )

    return user_page

@app.before_request
def update_last_seen():
    if flask_login.current_user.is_authenticated:
        flask_login.current_user.last_seen = datetime.utcnow()
        db.session.commit()

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = app_forms.EditProfileForm(flask_login.current_user.username)
    if form.validate_on_submit():
        flask_login.current_user.username = form.username.data
        flask_login.current_user.about_me = form.about_me.data
        db.session.commit()
        flask.flash('Changes saved.')
        return flask.redirect(flask.url_for('edit_profile'))
    elif flask.request.method == 'GET':
        form.username.data = flask_login.current_user.username
        form.about_me.data = flask_login.current_user.about_me
    
    return flask.render_template('edit_profile.html', title='Edit profile', form=form)

@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = app_forms.EmptyForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            flask.flash(f'User {username} not found.')
            return flask.redirect(flask.url_for('index'))
        if user == flask_login.current_user:
            flask.flash('You can\'t follow yourself.')
            return flask.redirect(flask.url_for('user', username=username))

        flask_login.current_user.follow(user)
        db.session.commit()
        flask.flash(f'Followed {username}')
        return flask.redirect(flask.url_for('user', username=username))
    else:
        return flask.redirect(flask.url_for('index'))

@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = app_forms.EmptyForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            flask.flash(f'User {username} not found.')
            return flask.redirect(flask.url_for('index'))
        if user == flask_login.current_user:
            flask.flask('You can\'t unfollow youself.')
            return flask.redirect(flask.url_for('user', username=username))
        
        flask_login.current_user.unfollow(user)
        db.session.commit()
        flask.flash(f'Unfollowed {username}.')
        return flask.redirect(flask.url_for('user', username=username))
    else:
        return flask.redirect(flask.url_for('index'))

@app.route('/explore')
@login_required
def explore():
    page = flask.request.args.get('page', 1, type=int)
    posts = models.Post.query.order_by(models.Post.timestamp.desc())
    paginated_posts = posts.paginate(page, app.config['POSTS_PER_PAGE'], False)

    if paginated_posts.has_next:
        next_url = flask.url_for('explore', page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('explore', page=paginated_posts.prev_num)
    else:
        prev_url = None

    explore = flask.render_template(
        'index.html', title='Explore',
        posts=paginated_posts.items,
        next_url=next_url,
        prev_url=prev_url
    )
    return explore

@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('index'))
    
    form = app_forms.ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(email=form.email.data).first()
        if user:
            app_email.send_password_reset_email(user)
        
        flask.flash('Check your email.')
        return flask.redirect(flask.url_for('login'))
    
    page = flask.render_template('reset_password_request.html', title='Reset password', form=form)
    return page

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if flask_login.current_user.is_authenticated:
        return flask.redirect(flask.url_for('index'))

    user = models.User.verify_reset_password_token(token)
    if not user:
        return flask.redirect(flask.url_for('index'))
    
    form = app_forms.ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flask.flash('Password successfully reset.')
        return flask.redirect(flask.url_for('login'))
    
    return flask.render_template('reset_password.html', form=form)
