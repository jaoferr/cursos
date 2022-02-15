import time
import rq
from app import create_app
from app import db
import app.models as models

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
