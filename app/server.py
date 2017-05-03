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
from models import db, Resource, User, Reservation, Tag
from . import app, login_manager, bcrypt
from flask import Response, redirect, jsonify, request, json, url_for, make_response, render_template
from flask_login import login_required, login_user, current_user, logout_user

# User management
@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        print "register template"
        return render_template('register.html')
    data = request.form.to_dict(flat=True)
    user = User(data['email'] , bcrypt.generate_password_hash(data['password']))
    db.session.add(user)
    db.session.commit()
    print 'User successfully registered'
    return redirect(url_for('login'))

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    data = request.form.to_dict(flat=True)
    user = User.query.filter_by(email=data['email']).first()
    if user is None or not bcrypt.check_password_hash(user.passhash, data['password']):
        flash('Username or Password is invalid' , 'error')
        return redirect(url_for('login'))
    login_user(user)
    print 'Logged in successfully'
    return redirect(url_for('.list'))

@app.route('/logout',methods=['GET'])
def logout():
    logout_user()
    return redirect(url_for('.login'))
# End of User management

# Resource management, need to be updated
@app.route('/resources', methods=['GET'])
def list():
    resources = [res for res in Resource.query.all()]
    return render_template(
        "list.html",
        resources=resources)

@app.route('/resources/add', methods=['GET'])
def add():
    return render_template("form.html", action="Add", resource={})

@app.route('/resources/add', methods=['POST'])
def add_resource():
    data = request.form.to_dict(flat=True)
    print data
    resource = Resource()
    resource.deserialize(data)
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for('.get_resources', id=resource.id))

@app.route('/resources/<int:id>', methods=['GET'])
def get_resources(id):
    resource = Resource.query.get(id)
    if not resource:
        raise NotFound("resource with id '{}' was not found.".format(id))
    return render_template("view.html", resource=resource)

@app.route('/resources/<int:id>/edit', methods=['GET'])
def edit_resources(id):
    resource = Resource.query.get_or_404(id)
    return render_template("form.html", action="Edit", resource=resource)

@app.route('/resources/<int:id>/edit', methods=['POST'])
def update_resources(id):
    resource = Resource.query.get_or_404(id)
    data = request.form.to_dict(flat=True)
    resource.deserialize(data)
    db.session.commit()
    return redirect(url_for('.get_resources', id=resource.id))

@app.route('/resources/<int:id>/delete', methods=['get'])
def delete_resources(id):
    resource = Resource.query.get(id)
    if resource:
        db.session.delete(resource)
        db.session.commit()
    return redirect(url_for('.list'))
