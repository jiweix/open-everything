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

class Resource(db.Model):
    __tablename__ = "resources"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    owner_id = db.Column(db.Integer)
    description = db.Column(db.String(200))

    def serialize(self):
        return { "id": self.id, "name": self.name, "owner_id": self.owner_id, "description": self.description}

    def deserialize(self, data):
        try:
            self.name = data['name']
            self.owner_id = int(data['owner_id'])
            self.description = data['description']
        except KeyError as e:
            raise KeyError('Invalid resource: missing ' + e.args[0])
        except TypeError as e:
            raise KeyError('Invalid resource: body of request contained bad or no data')
        return self

'''
class Reservation(db.Model):
    __tablename__ = "reservation"
    id = db.Column(db.Integer, primary_key=True)
    resource_id = db.Column(db.String(100))
    user_id = db.Column(db.Integer)
    start_time = db.Column(db.String(200))
    end_time =
    '''
