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

db = SQLAlchemy()

association_table = db.Table('association', db.Model.metadata,
    db.Column('resource_id', db.Integer, db.ForeignKey('resource.id')),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'))
)

class Resource(db.Model):
    __tablename__ = "resource"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # Integer value from 0 to 1440 in minutes for start_time and end_time
    available_start = db.Column(db.Integer)
    available_end = db.Column(db.Integer)
    tags = db.relationship('Tags', secondary=association_table, backref='resource')
    reservations = db.relationship('Reservation', backref='resource',
                                lazy='dynamic')

    def serialize(self):
        return { "id": self.id,
                 "name": self.name,
                 "owner_id": self.owner_id,
                 "available_start": self.available_start,
                 "available_end": self.available_end
                }

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.owner_id = int(data['owner_id'])
            self.available_start = int(data['available_start'])
            self.available_end = int(data['available_end'])
        except KeyError as e:
            raise KeyError('Invalid resource: missing ' + e.args[0])
        except TypeError as e:
            raise TypeError('Invalid resource: body of request contained bad or no data')
        return self


class Reservation(db.Model):
    __tablename__ = "reservation"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resource.id'))
    resource_name = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    # time should be integer as minutes
    start_time = db.Column(db.Integer)
    duration = db.Column(db.Integer)

    def serialize(self):
        return { "id": self.id,
                 "resource_id": self.resource_id,
                 "resource_name": self.resource_name,
                 "user_id": self.user_id,
                 "start_time": self.start_time,
                 "duration": self.duration
                }

    def deserialize(self, data):
        try:
            self.resource_id = int(data['resource_id'])
            self.resource_name = data['resource_name']
            self.user_id = int(data['user_id'])
            self.start_time = int(data['start_time'])
            self.duration = int(data['duration'])
        except KeyError as e:
            raise KeyError('Invalid reservation: missing ' + e.args[0])
        except TypeError as e:
            raise TypeError('Invalid reservation: body of request contained bad or no data')
        return self

class Tag(db.Model):
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    # lower case letters less than or equals to 20 chars
    value = db.Column(db.String(20))

    def __init__(value):
        self.value = value


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100))
    passhash = db.Column(db.String)
    authenticated = db.Column(db.Boolean, default=False)
    reservations = db.relationship('Reservation', backref='user',
                                lazy='dynamic')
    resources = db.relationship('Resource', backref='user',
                                lazy='dynamic')

    def __init__(email, passhash):
        self.email = email
        self.passhash = passhash

    def is_active(self):
        return True

    def get_id(self):
        return self.id

    def is_authenticated(self):
        return self.authenticated
