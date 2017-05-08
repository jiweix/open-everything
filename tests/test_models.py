import unittest
from datetime import datetime, timedelta
import app
from app import models, server
from app.models import db, User, Reservation, Resource, Tag

class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = app.get_app("TEST")

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_create_a_user(self):
        users = [user for user in User.query.all()]
        self.assertEqual(users, [])
        self.add_one_user()
        users = [user for user in User.query.all()]
        self.assertEqual(len(users), 1)
        user = User.query.filter_by(email="a@a.com").first()
        self.assertTrue(user.is_correct_pw("hard_to_guess_pw"))

    def test_update_a_user(self):
        self.add_one_user()
        user = User.query.filter_by(email="a@a.com").first()
        self.assertFalse(user.is_authenticated())
        user.authenticated = True
        db.session.add(user)
        db.session.commit()
        user_copy = User.query.filter_by(email="a@a.com").first()
        self.assertTrue(user.is_authenticated())

    def test_create_a_resource(self):
        self.add_one_user()
        self.add_one_resource()
        user = User.query.filter_by(email="a@a.com").first()
        resources = [res for res in user.resources]
        self.assertEqual(len(resources), 1)
        resource = resources[0]
        self.assertEqual(resource.name, "test_res")
        self.assertEqual(resource.owner_id, user.id)
        self.assertEqual(resource.available_start, "5:00")
        self.assertEqual(resource.available_end, "17:00")

    def test_create_a_resource_missing_key(self):
        resource = Resource()
        error = False
        try:
            resource.deserialize({
                    'name' : "test_res",
                    'available_start': "5:00",
                    'available_end' : "17:00"
                    })
        except KeyError as e:
            self.assertTrue("Invalid resource: missing" in e.message)
            error = True
        self.assertTrue(error)

    def test_create_a_resource_wrong_value(self):
        resource = Resource()
        error = False
        try:
            resource.deserialize({
                    'name' : "test_res",
                    'owner_id' : 'not_integer',
                    'available_start': "5:00",
                    'available_end' : "17:00"
                    })
        except ValueError as e:
            self.assertTrue("body of request contained bad or no data" in e.message)
            error = True
        self.assertTrue(error)

    def test_create_a_reservation(self):
        user, resource, tag, tag_2 = self.setup_dummy_data()
        reservation = Reservation()
        # business logic in enforced in server level.
        reservation.deserialize({
                'resource_id' : resource.id,
                'resource_name' : resource.name,
                'user_id' : user.id,
                'start_time' : datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=30),
                'duration': '00:30'
                })
        db.session.add(reservation)
        db.session.commit()
        user = User.query.filter_by(email="a@a.com").first()
        resource = [res for res in user.resources][0]
        user_res = [res for res in user.reservations][0]
        resource_res = [res for res in resource.reservations][0]
        self.assertEqual(user_res, resource_res)
        self.assertEqual(user_res.resource_id, resource.id)
        self.assertEqual(user_res.user_id, user.id)
        self.assertEqual(user_res.resource_name, resource.name)
        self.assertEqual(user_res.duration, '00:30')

    def test_create_a_reservation_missing_key(self):
        reservation = Reservation()
        error = False
        try:
            reservation.deserialize({
                    'resource_id' : 1,
                    'user_id' : 1,
                    'start_time' : datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=30),
                    'duration': '00:30'
                    })
        except KeyError as e:
            self.assertTrue("Invalid reservation: missing" in e.message)
            error = True
        self.assertTrue(error)

    def test_create_a_reservation_wrong_value(self):
        reservation = Reservation()
        error = False
        try:
            reservation.deserialize({
                    'resource_id' : 1,
                    'resource_name' : "test_res",
                    'user_id' : "not_integer",
                    'start_time' : datetime.now(),
                    'end_time': datetime.now() + timedelta(minutes=30),
                    'duration': '00:30'
                    })
        except ValueError as e:
            self.assertTrue("body of request contained bad or no data" in e.message)
            error = True
        self.assertTrue(error)

    def test_retrive_resource_by_tag(self):
        user, resource, tag, tag_2 = self.setup_dummy_data()
        resource_copy = [res for res in tag.resources][0]
        self.assertEqual(resource, resource_copy)

    def test_retrive_tags_through_resource(self):
        user, resource, tag, tag_2 = self.setup_dummy_data()
        tags = [t for t in resource.tags]
        self.assertTrue(tag in tags)
        self.assertTrue(tag_2 in tags)
        self.assertEqual(len(tags), 2)

    def setup_dummy_data(self):
        self.add_one_user()
        self.add_one_resource()
        user = User.query.filter_by(email="a@a.com").first()
        resource = [res for res in user.resources][0]
        tag = Tag("tag_1")
        tag_2 = Tag("tag_2")
        resource.tags.append(tag)
        resource.tags.append(tag_2)
        db.session.add(tag)
        db.session.add(tag_2)
        db.session.add(resource)
        db.session.commit()
        return user, resource, tag, tag_2

    def add_one_user(self):
        user = User("a@a.com", "hard_to_guess_pw")
        db.session.add(user)
        db.session.commit()

    # must call add_one_user before using this method, should not called twice in one test
    def add_one_resource(self):
        user = User.query.filter_by(email="a@a.com").first()
        resource = Resource()
        resource.deserialize({
                'name' : "test_res",
                'owner_id' : user.id,
                'available_start': "5:00",
                'available_end' : "17:00"
                })
        db.session.add(resource)
        db.session.commit()

if __name__ == '__main__':
    unittest.main()
