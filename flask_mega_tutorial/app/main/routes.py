import flask
import flask_login
import langdetect
import werkzeug.urls
import app.main.forms as main_forms
from flask import current_app
from app.main import blueprint
from app.translate import translate
from app import models, db
from flask_babel import _, get_locale
from flask_login.utils import login_required


from datetime import datetime


@blueprint.before_request
def before_request():
    if flask_login.current_user.is_authenticated:
        flask_login.current_user.last_seen = datetime.utcnow()
        db.session.commit()
        flask.g.search_form = main_forms.SearchForm()
    flask.g.locale = str(get_locale())

@blueprint.route('/', methods=['GET', 'POST'])
@blueprint.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    form = main_forms.PostForm()
    if form.validate_on_submit():
        try:
            language = langdetect.detect(form.post.data)
        except langdetect.LangDetectException:
            language = ''
        post = models.Post(
            body=form.post.data, 
            author=flask_login.current_user,
            language=language
        )
        db.session.add(post)
        db.session.commit()
        flask.flash(_('Posted!'))
        return flask.redirect(flask.url_for('main.index'))

    page = flask.request.args.get('page', 1, type=int)
    posts = flask_login.current_user.followed_posts()
    paginated_posts = posts.paginate(page, current_app.config['POSTS_PER_PAGE'], False)
    
    if paginated_posts.has_next:
        next_url = flask.url_for('main.index', page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('main.index', page=paginated_posts.prev_num)
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

@blueprint.route('/explore')
@login_required
def explore():
    page = flask.request.args.get('page', 1, type=int)
    posts = models.Post.query.order_by(models.Post.timestamp.desc())
    paginated_posts = posts.paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    if paginated_posts.has_next:
        next_url = flask.url_for('main.explore', page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('main.explore', page=paginated_posts.prev_num)
    else:
        prev_url = None

    explore = flask.render_template(
        'index.html', title=_('Explore'),
        posts=paginated_posts.items,
        next_url=next_url,
        prev_url=prev_url
    )
    return explore

@blueprint.route('/restricted')
@login_required
def restricted():
    return '<b>' + _('A restricted page') + '</b>'

@blueprint.route('/user/<username>')
@login_required
def user(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    page = flask.request.args.get('page', type=int)
    posts = user.posts.order_by(models.Post.timestamp.desc())
    paginated_posts = posts.paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    if paginated_posts.has_next:
        next_url = flask.url_for('main.user', username=user.username,page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('main.user', username=user.username, page=paginated_posts.prev_num)
    else:
        prev_url = None

    form = main_forms.EmptyForm()

    user_page = flask.render_template(
        'user.html', user=user, posts=paginated_posts.items, form=form,
        next_url=next_url, prev_url=prev_url
    )

    return user_page

@blueprint.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = main_forms.EditProfileForm(flask_login.current_user.username)
    if form.validate_on_submit():
        flask_login.current_user.username = form.username.data
        flask_login.current_user.about_me = form.about_me.data
        db.session.commit()
        flask.flash(_('Changes saved.'))
        return flask.redirect(flask.url_for('main.edit_profile'))
    elif flask.request.method == 'GET':
        form.username.data = flask_login.current_user.username
        form.about_me.data = flask_login.current_user.about_me
    
    return flask.render_template('edit_profile.html', title=_('Edit profile'), form=form)

@blueprint.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = main_forms.EmptyForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            flask.flash(_('User %(username)s not found.', username=username))
            return flask.redirect(flask.url_for('main.index'))
        if user == flask_login.current_user:
            flask.flash(_('You can\'t follow yourself.'))
            return flask.redirect(flask.url_for('main.user', username=username))

        flask_login.current_user.follow(user)
        db.session.commit()
        flask.flash(_('Followed %(username)s', username=username))
        return flask.redirect(flask.url_for('main.user', username=username))
    else:
        return flask.redirect(flask.url_for('main.index'))

@blueprint.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = main_forms.EmptyForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            flask.flash(_('User %(username)s not found.', username=username))
            return flask.redirect(flask.url_for('main.index'))
        if user == flask_login.current_user:
            flask.flask(_('You can\'t unfollow youself.'))
            return flask.redirect(flask.url_for('main.user', username=username))
        
        flask_login.current_user.unfollow(user)
        db.session.commit()
        flask.flash(_('Unfollowed %(username)s.', username=username))
        return flask.redirect(flask.url_for('main.user', username=username))
    else:
        return flask.redirect(flask.url_for('main.index'))

@blueprint.route('/translate', methods=['POST'])
@login_required
def translate_text():
    j = flask.jsonify(
        {'text': translate(
            flask.request.form['text'],
            flask.request.form['source_language'],
            flask.request.form['dest_language']
        )}
    )
    return j

@blueprint.route('/search')
@login_required
def search():
    if not flask.g.search_form.validate():
        print('\n')
        print(flask.g.search_form.validate())
        print(flask.g.search_form.data)
        print('\n')
        return flask.redirect(flask.url_for('main.explore'))
    page = flask.request.args.get('page', 1, type=int)
    posts, total = models.Post.search(flask.g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])

    if total > page * current_app.config['POSTS_PER_PAGE']:
        next_url = flask.url_for('main.search', q=flask.g.search_form.q.data, page=page + 1)
    else:
        next_url = None
        
    if page > 1:
        prev_url = flask.url_for('main.user', username=flask.g.search_form.q.data, page=page - 1)
    else:
        prev_url = None
    
    template = flask.render_template(
        'search.html', title=_('Results'), 
        posts=posts, next_url=next_url, prev_url=prev_url
    )
    return template

@blueprint.route('/user/<username>/popup')
@login_required
def user_popup(username):
    user = models.User.query.filter_by(username=username).first_or_404()
    form = main_forms.EmptyForm()

    template = flask.render_template('user_popup.html', user=user, form=form)
    return template

@blueprint.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    user = models.User.query.filter_by(username=recipient).first_or_404()
    form = main_forms.MessageForm()
    if form.validate_on_submit():
        msg = models.Message(
            author=flask_login.current_user, 
            recipient=user,
            body=form.message.data
        )
        db.session.add(msg)
        user.add_notification('unread_message_count', user.new_messages())
        db.session.commit()
        flask.flash(_('Your message has been sent.'))
        return flask.redirect(flask.url_for('main.user', username=recipient))
    
    template = flask.render_template(
        'send_message.html', title=_('Send a message'),
        form=form, recipient=recipient 
    )
    return template

@blueprint.route('/messages')
@login_required
def messages():
    flask_login.current_user.last_message_read_time = datetime.utcnow()
    flask_login.current_user.add_notification('unread_message_count', 0)
    db.session.commit()
    page = flask.request.args.get('page', 1, type=int)
    messages = flask_login.current_user.messages_received.order_by(models.Message.timestamp.desc())
    paginated_messages = messages.paginate(page, current_app.config['POSTS_PER_PAGE'], False)

    if paginated_messages.has_next:
        next_url = flask.url_for(
            'main.messages', page=paginated_messages.next_num
        )
    else:
        next_url = None
        
    if paginated_messages.has_prev:
        prev_url = flask.url_for(
            'main.messages', page=paginated_messages.prev_num
        )
    else:
        prev_url = None
    
    template = flask.render_template(
        'messages.html', messages=paginated_messages.items,
        next_url=next_url, prev_url=prev_url
    )
    return template

@blueprint.route('/notifications')
@login_required
def notifications():
    since = flask.request.args.get('since', 0.0, type=float)
    notifications = flask_login.current_user.notifications.filter(
        models.Notification.timestamp > since)
    notifications = notifications.order_by(models.Notification.timestamp.asc())

    j = [{
        'name': n.name,
        'data': n.get_data(),
        'timestamp': n.timestamp
    } for n in notifications]
    json_notifications = flask.jsonify(j)

    return json_notifications    

@blueprint.route('/export_posts')
@login_required
def export_posts():
    if flask_login.current_user.get_task_in_progress('export_posts'):
        flask.flash(_('An export task is already in progress.'))
    else:
        flask_login.current_user.launch_task('export_posts', _('Exporting posts...'))
        db.session.commit()
    
    return flask.redirect(flask.url_for('main.user', username=flask_login.current_user.username))
