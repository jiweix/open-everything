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

db = SQLAlchemy()

class Tag_Resource(db.Model):
    __tablename__ = "tag_resource"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))

    resource = db.relationship("Resource", backref=db.backref("tag_resource", cascade="all, delete-orphan"))
    tag = db.relationship("Tag", backref=db.backref("tag_resource", cascade="all, delete-orphan"))

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

    def serialize(self):
        return { "id": self.id,
                 "name": self.name,
                 "owner_id": self.owner_id,
                 "available_start": self.available_start,
                 "available_end": self.available_end,
                 "last_reserve_time": self.last_reserve_time
                }

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.owner_id = int(data['owner_id'])
            self.available_start = data['available_start']
            self.available_end = data['available_end']
            self.last_reserve_time = datetime.now()
        except KeyError as e:
            raise KeyError('Invalid resource: missing ' + e.args[0])
        except TypeError as e:
            raise TypeError('Invalid resource: body of request contained bad or no data')
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
    duration = db.Column(db.Integer)

    def serialize(self):
        return { "id": self.id,
                 "resource_id": self.resource_id,
                 "resource_name": self.resource_name,
                 "user_id": self.user_id,
                 "start_time": self.start_time,
                 "end_time": self.end_time,
                 "duration": self.duration
                }

    def deserialize(self, data):
        try:
            self.resource_id = int(data['resource_id'])
            self.resource_name = data['resource_name']
            self.user_id = int(data['user_id'])
            self.start_time = data['start_time']
            self.end_time = data['end_time']
            self.duration = self.get_duration(data['start_time'], data['end_time'])
        except KeyError as e:
            raise KeyError('Invalid reservation: missing ' + e.args[0])
        except TypeError as e:
            raise TypeError('Invalid reservation: body of request contained bad or no data')
        return self

    def get_duration(self, start, end):
        return int((end - start).total_seconds() / 60.0)

class Tag(db.Model):
    '''
    Tag of resources, could be 'room', 'car', 'satellite' etc.
    tag and resources have many to many relationship.
    '''
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    # lower case letters
    value = db.Column(db.String(20))

    resources = db.relationship('Resource', secondary="tag_resource", lazy='dynamic')

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

    def __init__(self, email, passhash):
        self.email = email
        self.passhash = passhash

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated
