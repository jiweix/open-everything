import app
from app import models, server
from app.models import db, User, Reservation, Resource, Tag
import unittest


class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = app.get_app("TEST")


    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_a_user(self):
        users = [user for user in User.query.all()]
        self.assertEqual(users, [])



if __name__ == '__main__':
    unittest.main()
