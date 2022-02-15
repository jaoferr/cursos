import time
import rq
import sys
import json
import app.models as models
import app.email as email
from app import create_app
from app import db
from flask import render_template
from flask_babel import _, force_locale


app = create_app()
app.app_context().push()

def example(seconds):
    job = rq.get_current_job()
    print('Starting task')
    for i in range(seconds):
        job.meta['progress'] = 100.0 * i / seconds
        job.save_meta()
        print(i)
        time.sleep(1)
    job.meta['progress'] = 100
    job.save_meta()
    print('Task complete')

def _set_task_progress(progress):
    job = rq.get_current_job()
    if job:
        job.meta['progress'] = progress
        job.save_meta()
        
        task = models.Task.query.get(job.get_id())
        task.user.add_notification('task_progress', {'task_id': job.get_id(),
                                                     'progress': progress})
        if progress >= 100:
            task.complete = True
        db.session.commit()

def export_posts(user_id, **kwargs):
    try:
        user = models.User.query.get(user_id)
        _set_task_progress(0)
        data = []
        total_posts = user.posts.count()
        posts = user.posts.order_by(models.Post.timestamp.asc())
        for i, post in enumerate(posts):
            data.append({'timestamp': post.timestamp.isoformat() + 'Z',
                         'body': post.body})
            time.sleep(3)
            _set_task_progress(100 * i // total_posts)
        with force_locale(kwargs['locale']):
            email.send_email(
                f'[Flask Mega Tutorial]{_("Your posts")}',
                sender=app.config['ADMINS'][0], recipients=[user.email],
                text_body=render_template('email/export_posts.txt', user=user),
                html_body=render_template('email/export_posts.html', user=user),
                attachments=[('posts.json', 'application/json', json.dumps({'posts': data}, indent=4))],
                sync=True
            )
    except:
        app.logger.error('Unhandled exception', exc_info=sys.exc_info())
    finally:
        _set_task_progress(100)
