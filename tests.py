from datetime import datetime, timedelta
from os import unlink
import unittest

from flask_sqlalchemy import model
from app import app, db
from app import models

class UserModelCase(unittest.TestCase):

    def setUp(self) -> None:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self) -> None:
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = models.User(username='j')
        u.set_password('h1h2')
        self.assertFalse(u.check_password('i3i4'))
        self.assertTrue(u.check_password('h1h2'))

    def test_avatar(self):
        u = models.User(username='j', email='j@e.com')
        self.assertEqual(u.avatar(128), ('https://www.gravatar.com/avatar/b2034081b6f96db7c9764a5b71b2a134?d=identicon&s=128'))
    
    def test_follow(self):
        u1 = models.User(username='j', email='j@e.com')
        u2 = models.User(username='f', email='f@e.com')

        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'f')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'j')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        u1 = models.User(username='j', email='j@e.com')
        u2 = models.User(username='f', email='f@e.com')
        u3 = models.User(username='c', email='c@e.com')
        u4 = models.User(username='s', email='s@e.com')
        db.session.add_all([u1, u2, u3, u4])

        now = datetime.utcnow()
        p1 = models.Post(body='post from j', author=u1, timestamp=now + timedelta(seconds=1))
        p2 = models.Post(body='post from f', author=u2, timestamp=now + timedelta(seconds=4))
        p3 = models.Post(body='post from c', author=u3, timestamp=now + timedelta(seconds=3))
        p4 = models.Post(body='post from s', author=u4, timestamp=now + timedelta(seconds=2))
        db.session.add_all([p1, p2, p3, p4])
        db.session.commit()

        u1.follow(u2)
        u1.follow(u4)
        u2.follow(u3)
        u3.follow(u4)
        db.session.commit()

        f1 = u1.followed_posts().all()
        f2 = u2.followed_posts().all()
        f3 = u3.followed_posts().all()
        f4 = u4.followed_posts().all()
        self.assertEqual(f1, [p2, p4, p1])
        self.assertEqual(f2, [p2, p3])
        self.assertEqual(f3, [p3, p4])
        self.assertEqual(f4, [p4])

if __name__ == '__main__':
    unittest.main(verbosity=2)
