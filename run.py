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
import os
import logging
from app.models import db
from app import app, server
import pymysql

debug = (os.getenv('DEBUG', 'False') == 'True')
port = os.getenv('PORT', '8080')

# app configuration
if 'DATABASE_URL' in os.environ:
    # setup database for heroku
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
else:
    # use local db if develop locally
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/development.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'please, tell nobody... Shhhh'
app.config['LOGGING_LEVEL'] = logging.INFO

debug = (os.getenv('DEBUG', 'False') == 'True')
port = os.getenv('PORT', '8080')

db.init_app(app)
with app.app_context():
    db.create_all()
app.run(host='0.0.0.0', port=int(port), debug=debug)
