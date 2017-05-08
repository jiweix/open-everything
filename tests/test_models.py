import app
from app import models, server
from app.models import db

import unittest


class TestPets(unittest.TestCase):

    def setUp(self):
        app.get_app("TEST")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_a_user():
        
