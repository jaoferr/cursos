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
        return flask.redirect(flask.url_for('index'))

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
        next_url = flask.url_for('user', username=user.username,page=paginated_posts.next_num)
    else:
        next_url = None
        
    if paginated_posts.has_prev:
        prev_url = flask.url_for('user', username=user.username, page=paginated_posts.prev_num)
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
        return flask.redirect(flask.url_for('edit_profile'))
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
            return flask.redirect(flask.url_for('index'))
        if user == flask_login.current_user:
            flask.flash(_('You can\'t follow yourself.'))
            return flask.redirect(flask.url_for('user', username=username))

        flask_login.current_user.follow(user)
        db.session.commit()
        flask.flash(_('Followed %(username)s', username=username))
        return flask.redirect(flask.url_for('user', username=username))
    else:
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    form = main_forms.EmptyForm()
    if form.validate_on_submit():
        user = models.User.query.filter_by(username=username).first()
        if user is None:
            flask.flash(_('User %(username)s not found.', username=username))
            return flask.redirect(flask.url_for('index'))
        if user == flask_login.current_user:
            flask.flask(_('You can\'t unfollow youself.'))
            return flask.redirect(flask.url_for('user', username=username))
        
        flask_login.current_user.unfollow(user)
        db.session.commit()
        flask.flash(_('Unfollowed %(username)s.', username=username))
        return flask.redirect(flask.url_for('user', username=username))
    else:
        return flask.redirect(flask.url_for('index'))

@blueprint.route('/translate', methods=['POST'])
@login_required
def translate_text():
    j = flask.jsonify(
        {'text': translate.translate(
            # flask.request.form['text'],
            'test?',
            flask.request.form['source_language'],
            flask.request.form['dest_language']
        )}
    )
    return j

@blueprint.route('/search')
@login_required
def search():
    if not flask.g.search_form.validate():
        return flask.redirect(flask.url_for('main.explore'))
    page = flask.request.args.get('page', 1, type=int)
    posts, total = models.Post.search(flask.g.search_form.q.data, page, current_app.config['POSTS_PER_PAGE'])

    if total > page * current_app.config['POSTS_PER_PAGE']:
        next_url = flask.url_for('main.search', q=flask.g.search_form.q.data, page=page + 1)
    else:
        next_url = None
        
    if page > 1:
        prev_url = flask.url_for('user', username=flask.g.search_form.q.data, page=page - 1)
    else:
        prev_url = None
    
    template = flask.render_template(
        'search.html', title=_('Search'), 
        posts=posts, next_url=next_url, prev_url=prev_url
    )
    return template