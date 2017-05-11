import os
import pymysql
import logging
from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

app = Flask(__name__)
login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)

import server
import models
from models import db

# Get app from this function, easy for testing
def get_app(option):
    app.config['LOGGING_LEVEL'] = logging.INFO
    if option == "TEST":
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/test.db'
    else:
    # app configuration
        if 'CLEARDB_DATABASE_URL' in os.environ:
            # setup database for heroku
            app.config['SQLALCHEMY_DATABASE_URI'] = "mysql+pymysql" + os.environ['CLEARDB_DATABASE_URL'].split("?")[0][5:]
        elif 'HEROKU_POSTGRESQL_CYAN_URL' in os.environ:
            # Support of postgresql was added to test a bug in a middleware.
            app.config['SQLALCHEMY_DATABASE_URI'] = "postgres+psycopg2" + os.environ['HEROKU_POSTGRESQL_CYAN_URL'][8:]
        else:
            # use local db if develop locally
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/development.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'please, tell nobody... Shhhh'
    db.init_app(app)
    app.app_context().push()
    with app.app_context():
        db.create_all()
    return app
