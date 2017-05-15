######################################################################
# Copyright 2017 Jiwei Xu. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
######################################################################
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import bcrypt

db = SQLAlchemy()

class Tag_Resource(db.Model):
    '''
    Tag Resource relationship. Used to link resource to tag
    '''
    __tablename__ = "tag_resource"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))

    resource = db.relationship("Resource",
            backref=db.backref("tag_resource", cascade="all, delete-orphan"))
    tag = db.relationship("Tag",
            backref=db.backref("tag_resource", cascade="all, delete-orphan"))

    def __init__(self, resource_id, tag_id):
        self.resource_id = resource_id
        self.tag_id = tag_id


class Resource(db.Model):
    '''
    A shared resource that can be reserved by any register user.
    resource and reservation have 1 to many relationship.
    resource and owner have 1 to 1 relationship.
    '''
    __tablename__ = "resource"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # time should be hh:mm in 24 hour format
    available_start = db.Column(db.String(5))
    available_end = db.Column(db.String(5))
    last_reserve_time = db.Column(db.DateTime)
    tags = db.relationship('Tag', secondary="tag_resource", lazy='dynamic')
    reservations = db.relationship('Reservation', backref='resource',
                                lazy='dynamic')

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.owner_id = int(data['owner_id'])
            self.available_start = data['available_start']
            self.available_end = data['available_end']
            self.last_reserve_time = datetime.now()
        except KeyError as e:
            raise KeyError('Invalid resource: missing ' + e.args[0])
        except ValueError as e:
            raise ValueError('Invalid resource: body of request contained bad or no data')
        return self


class Reservation(db.Model):
    '''
    A reservation defines a user's intension to use one resource at certain time.
    reservation and resource have 1 to 1 relationship.
    reservation and user have 1 to 1 relationship.
    '''
    __tablename__ = "reservation"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    resource_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # duration should be calculate from these column
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    create_time = db.Column(db.DateTime)
    duration = db.Column(db.String(5))

    def deserialize(self, data):
        try:
            self.resource_id = int(data['resource_id'])
            self.resource_name = data['resource_name']
            self.user_id = int(data['user_id'])
            self.start_time = data['start_time']
            self.end_time = data['end_time']
            self.duration = data['duration']
            self.create_time = datetime.now()
        except KeyError as e:
            raise KeyError('Invalid reservation: missing ' + e.args[0])
        except ValueError as e:
            raise ValueError('Invalid reservation: body of request contained bad or no data')
        return self


class Tag(db.Model):
    '''
    Tag of resources, could be 'room', 'car', 'satellite' etc.
    tag and resources have many to many relationship.
    '''
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    # lower case letters
    value = db.Column(db.String(20))

    resources = db.relationship('Resource', secondary="tag_resource",
                                lazy='dynamic')

    def __init__(self, value):
        self.value = value


class User(db.Model):
    '''
    A regitered user. Can share resrouces and have reservations.
    user and resource have 1 to many relationship.
    user and reservation have 1 to many relationship.
    '''
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    passhash = db.Column(db.String(150))
    authenticated = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='user',
                                lazy='dynamic')
    resources = db.relationship('Resource', backref='user',
                                lazy='dynamic')

    def __init__(self, email, password):
        self.email = email
        self.passhash = bcrypt.generate_password_hash(password)

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated

    def is_correct_pw(self, password):
        return bcrypt.check_password_hash(self.passhash, password)
