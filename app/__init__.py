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
    if option == "TEST":
        print "Using Test DB"
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/test.db'
    else:
    # app configuration
        if 'POSTGRESQL' in os.environ:
            print "Using postgresql"
            app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['POSTGRESQL']
        elif 'DATABASE_URL' in os.environ:
            # setup database for heroku
            print "Using Production DB"
            app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
        else:
            # use local db if develop locally
            print "Using Local DB"
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/development.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = 'please, tell nobody... Shhhh'
    app.config['LOGGING_LEVEL'] = logging.INFO
    db.init_app(app)
    app.app_context().push()
    with app.app_context():
        db.create_all()
    return app
