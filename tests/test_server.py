import unittest
from datetime import datetime, timedelta
import app
from app import models, server
from app.models import db, User, Reservation, Resource, Tag
from flask import url_for

class TestModels(unittest.TestCase):

    def setUp(self):
        self.app = app.get_app("TEST")
        self.app.config.update(SERVER_NAME='localhost')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.setup_dummy_data()
        self.client = self.app.test_client(use_cookies=True)
        self.user_data = {  'email': "a@a.com",
                            'password': "hard_to_guess_pw"}

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # ---------------------- User tests ----------------------------------------
    def test_can_access_login_page(self):
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Please Login" in response.data)

    def test_can_access_register_page(self):
        response = self.client.get('/register')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Please Register" in response.data)

    def test_user_can_login(self):
        response = self.client.post('/login',
                                    data=self.user_data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, url_for('list'))

    def test_invalid_user_can_not_login(self):
        response = self.client.post('/login',
                                    data={ 'email': "a@a.com",
                                           'password': "wrong_password"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("User name or password invalid, Please try again" in response.data)

    def test_register_and_login_a_user(self):
        response = self.client.post('/register',
                                    data={ 'email': "b@b.com",
                                           'password': "hard_to_guess_pw"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, url_for('login'))
        response = self.client.post('/login',
                                    data={ 'email': "b@b.com",
                                           'password': "hard_to_guess_pw"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, url_for('list'))

    def test_register_with_duplicate_email(self):
        response = self.client.post('/register',
                                    data=self.user_data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Email already taken" in response.data)
    # ----------------------End User tests -------------------------------------

    # ----------------------Home page tests ------------------------------------
    def test_login_user_can_access_home_page(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.get('/home')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("test_res" in response.data)

    def test_anonymous_user_can_not_access_home_page(self):
        response = self.client.get('/home')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("You need to log in" in response.data)
    # ----------------------End Home page tests --------------------------------

    # ----------------------Resource tests -------------------------------------
    def test_access_add_resource_page(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.get('/resources/add')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Add resource" in response.data)

    def test_add_new_resource(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.post('/resources/add',
                                    data={ 'name': 'resource_2',
                                           'owner_id': self.test_user_id,
                                           'available_start': '01:00',
                                           'available_end': '23:00',
                                           'tag': ''},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("resource_2" in response.data)

    def test_add_invalid_resource(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.post('/resources/add',
                                    data={ 'name': 'resource_2',
                                           'owner_id': self.test_user_id,
                                           'available_start': 'wrong_time',
                                           'available_end': '23:00',
                                           'tag': ''})
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Input Invalid" in response.data)

    def test_retrive_resource_by_id(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.get('/resources/'+str(self.test_resource_id))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("test_res" in response.data)

    def test_access_edit_resource_page(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.get('/resources/'+str(self.test_resource_id)+'/edit')
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Edit resource" in response.data)

    def test_edit_resource(self):
        self.client.post('/login',
                         data=self.user_data)
        response = self.client.post('/resources/'+str(self.test_resource_id)+'/edit',
                                    data={ 'name': 'resource_2',
                                           'available_start': '01:00',
                                           'available_end': '23:00',
                                           'tag': 'test_tag' },
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("test_tag" in response.data)

    def test_edit_resource_invalid_user(self):
        self.client.post('/register',
                         data={ 'email': "b@b.com",
                                'password': "hard_to_guess_pw"})
        self.client.post('/login',
                         data={ 'email': "b@b.com",
                                'password': "hard_to_guess_pw"})
        response = self.client.post('/resources/'+str(self.test_resource_id)+'/edit',
                                    data={ 'name': 'resource_2',
                                           'available_start': '01:00',
                                           'available_end': '23:00',
                                           'tag': 'test_tag' })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.location, url_for('list'))
    # ----------------------End Resource tests ---------------------------------


    # ---------------------- SET UP --------------------------------------------
    def setup_dummy_data(self):
        self.test_user_id = self.add_one_user()
        self.test_resource = self.add_one_resource()
        self.test_resource_id, self.test_resource_name = self.test_resource.id, self.test_resource.name
        self.test_reservation_id = self.add_one_reservation(
                                        self.test_resource_id,
                                        self.test_resource_name,
                                        self.test_user_id)
        self.tag = Tag("tag_1")
        self.tag_2 = Tag("tag_2")
        self.test_resource.tags.append(self.tag)
        self.test_resource.tags.append(self.tag_2)
        db.session.add(self.tag)
        db.session.add(self.tag_2)
        db.session.add(self.test_resource)
        db.session.commit()

    def add_one_user(self):
        user = User("a@a.com", "hard_to_guess_pw")
        db.session.add(user)
        db.session.commit()
        return user.id

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
        return resource

    def add_one_reservation(self, resource_id, resource_name, user_id):
        reservation = Reservation()
        reservation.deserialize({
                'resource_id' : resource_id,
                'resource_name' : resource_name,
                'user_id' : user_id,
                'start_time' : datetime.now(),
                'end_time': datetime.now() + timedelta(minutes=30),
                'duration': '00:30'
                })
        db.session.add(reservation)
        db.session.commit()
        return reservation.id

if __name__ == '__main__':
    unittest.main()
