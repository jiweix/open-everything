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
import flask
from flask import Response, redirect, jsonify, request, json, url_for, make_response, render_template, g
from flask_login import login_required, login_user, current_user, logout_user
from werkzeug.contrib.atom import AtomFeed
from datetime import datetime, timedelta
from models import db, Resource, User, Reservation, Tag
from . import app, login_manager, bcrypt

# --------------------- User management ------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter(User.id == int(user_id)).first()

@app.before_request
def make_session_permanent():
    flask.session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

######################################################################
# Register a user
######################################################################
@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'GET':
        print "register template"
        return render_template('login.html', message="Please Register", button="Register")
    data = request.form.to_dict(flat=True)
    user = User(data['email'] , bcrypt.generate_password_hash(data['password']))
    db.session.add(user)
    db.session.commit()
    print 'User successfully registered'
    return redirect(url_for('login'))

######################################################################
# Login a user
######################################################################
@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('.list'))
        return render_template('login.html', message="Please Login", button="Login")
    data = request.form.to_dict(flat=True)
    user = User.query.filter_by(email=data['email']).first()
    if user is None or not bcrypt.check_password_hash(user.passhash, data['password']):
        print 'Username or Password is invalid'
        return redirect(url_for('login'))
    user.authenticated = True
    db.session.add(user)
    db.session.commit()
    login_user(user)
    print 'Logged in successfully'
    return redirect(url_for('.list'))

######################################################################
# Log out a user
######################################################################
@app.route('/logout',methods=['GET'])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    db.session.commit()
    logout_user()
    return redirect(url_for('.login'))
# --------------------- End of User management -----------------------

######################################################################
# Index page, should show register and log in option if not logged in
######################################################################
@app.route('/', methods=['GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('.list'))
    return render_template('index.html')

######################################################################
# Landing page
######################################################################
@app.route('/home', methods=['GET'])
@login_required
def list():
    '''
    the landing page,
    viewers will see three sections:
    (1) reservations made for resources by that user, sorted by reservation time;
    (2) all resources in the system, shown in reverse time order based on last made reservation;
    (3) resources that the user owns, each linked to its URL
    (4) a link to create a new resource
    '''
    resources = [res for res in Resource.query.all()]
    resources.sort(key=lambda x: x.last_reserve_time, reverse=True)
    user = current_user
    my_reservation = [res for res in user.reservations if res.end_time > datetime.now()]
    my_reservation.sort(key=lambda x: x.start_time)
    return render_template(
        "list.html",
        my_reservation=my_reservation,
        my_resources=user.resources,
        resources=resources)

######################################################################
# Add a resource (GET and POST)
######################################################################
@app.route('/resources/add', methods=['GET','POST'])
@login_required
def add_resource():
    if request.method == 'GET':
        return render_template("form.html", action="Add", resource={}, tag="")
    data = request.form.to_dict(flat=True)
    data['owner_id'] = current_user.id
    print data
    resource = Resource()
    resource.deserialize(data)
    tag_list = data['tag'].split()
    for tag_name in tag_list:
        tag = Tag.query.filter_by(value=tag_name.lower()).first()
        if not tag:
            tag = Tag(tag_name.lower())
        resource.tags.append(tag)
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for('.get_resources', id=resource.id))

######################################################################
# Retrieve a resource
######################################################################
@app.route('/resources/<int:id>', methods=['GET'])
@login_required
def get_resources(id):
    resource = Resource.query.get(id)
    if not resource:
        raise NotFound("resource with id '{}' was not found.".format(id))
    owner = current_user.id == resource.owner_id
    return render_template("view.html", resource=resource, owner=owner)

######################################################################
# Edit a resource (GET the edit page)
######################################################################
@app.route('/resources/<int:id>/edit', methods=['GET'])
@login_required
def edit_resources(id):
    resource = Resource.query.get_or_404(id)
    tag_str = ''
    for tag in resource.tags:
        tag_str += tag.value + " "
    return render_template("form.html", action="Edit", resource=resource, tag=tag_str[:-1])

######################################################################
# Edit a resource (POST)
######################################################################
@app.route('/resources/<int:id>/edit', methods=['POST'])
@login_required
def update_resources(id):
    resource = Resource.query.get_or_404(id)
    data = request.form.to_dict(flat=True)
    data['owner_id'] = current_user.id
    print data
    if resource is None or data['owner_id'] != resource.owner_id:
        return redirect(url_for('.list'))
    # edit name is not allowed.
    data['name'] = resource.name
    resource.deserialize(data)
    # update tags
    tag_list = data['tag'].split()
    for tag_name in tag_list:
        tag = Tag.query.filter_by(value=tag_name.lower()).first()
        if not tag:
            tag = Tag(tag_name.lower())
            db.session.add(tag)
        if tag not in resource.tags:
            resource.tags.append(tag)
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for('.get_resources', id=resource.id))

######################################################################
# Delete a resource
######################################################################
@app.route('/resources/<int:id>/delete', methods=['GET'])
@login_required
def delete_resources(id):
    resource = Resource.query.get(id)
    if resource is not None and resource.owner_id == current_user.id:
        for res in resource.reservations:
            db.session.delete(res)
        db.session.delete(resource)
        db.session.commit()
    return redirect(url_for('.list'))

######################################################################
# Get a reservation
######################################################################
@app.route('/reservations/<int:id>', methods=['GET'])
@login_required
def get_res(id):
    reservation = Reservation.query.get(id)
    if not reservation or reservation.end_time < datetime.now():
        raise NotFound("reservation with id '{}' was not found.".format(id))
    return render_template("view_res.html", reservation=reservation)

######################################################################
# Add a reservation
######################################################################
@app.route('/resources/<int:id>/add_reservation', methods=['GET', 'POST'])
@login_required
def add_res(id):
    if request.method == 'GET':
        return render_template('form_res.html', action="Add", message="")
    data = request.form.to_dict(flat=True)
    try:
        date = [int(x) for x in data['date'].split('-')]
        start = [int(x) for x in data['start'].split(':')]
        duration = [int(x) for x in data['duration'].split(':')]
        end = [start[0]+duration[0], start[1]+duration[1]]
        data['start_time'] = datetime(date[0], date[1], date[2], start[0], start[1])
        data['end_time'] = datetime(date[0], date[1], date[2], end[0], end[1])
    except:
        return render_template('form_res.html', action="Add", message="Time Input Invalid")
    # TODO more check about reservation could be made in that period of time should be performed
    resource = Resource.query.get(id)
    message = valid_res(data['start_time'], data['end_time'], resource)
    if message != "":
        return render_template('form_res.html', action="Add", message=message)
    data['user_id'] = current_user.id
    data['resource_id'] = id
    if resource is None:
        raise NotFound("resource with id '{}' was not found.".format(id))
    data['resource_name'] = resource.name
    resource.last_reserve_time = datetime.now()
    reservation = Reservation()
    reservation.deserialize(data)
    db.session.add(reservation)
    db.session.add(resource)
    db.session.commit()
    return redirect(url_for('.list'))

######################################################################
# Get reservations for one resource
######################################################################
@app.route('/resources/<int:id>/get_reservations', methods=['GET'])
@login_required
def get_res_for_resource(id):
    resource = Resource.query.get(id)
    if resource is None:
        raise NotFound("resource with id '{}' was not found.".format(id))
    reservations = [res for res in resource.reservations if res.end_time > datetime.now()]
    return render_template("list_res.html", reservations=reservations, resource=resource)

######################################################################
# Delete a reservation
######################################################################
@app.route('/reservations/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_res(id):
    reservation = Reservation.query.get(id)
    if reservation:
        db.session.delete(reservation)
        db.session.commit()
    return redirect(url_for('.list'))

######################################################################
# Get resources with 'tag'
######################################################################
@app.route('/tags/<int:id>', methods=['GET'])
@login_required
def get_resources_with_tag(id):
    tag = Tag.query.get(id)
    if not tag:
        raise NotFound("tag with id '{}' was not found.".format(id))
    resources = tag.resources
    return render_template("list_tag_resource.html", resources=resources, tag=tag)

######################################################################
# Get a user's info (reservation, resources)
######################################################################
@app.route('/users/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    user = User.query.get(id)
    if not user:
        raise NotFound("user with id '{}' was not found.".format(id))
    resources = [res for res in user.resources]
    resources.sort(key=lambda x: x.last_reserve_time, reverse=True)
    reservations = [res for res in user.reservations if res.end_time > datetime.now()]
    reservations.sort(key=lambda x: x.start_time)
    return render_template("list_user_info.html", resources=resources, reservations=reservations)

######################################################################
# Generate RSS for a resource
######################################################################
@app.route('/resources/<int:id>/rss', methods=['GET'])
@login_required
def generate_rss(id):
    resource = Resource.query.get(id)
    reservations = [res for res in resource.reservations if res.end_time > datetime.now()]
    reservations.sort(key=lambda x: x.start_time)
    name = "All reservations for {}".format(resource.name)
    feed = AtomFeed(name, feed_url=request.url,
                    url=request.host_url, author="JX")
    for res in reservations:
        url = request.host_url + "reservations/" + str(res.id)
        feed.add("Reservation id, " + str(res.id),
                 content_type='html',
                 updated=datetime.now(),
                 id=res.id,
                 url=url
                 )
    return feed.get_response()

######################################################################
#  H E L P E R  F U N C T I O N S
######################################################################
def valid_res(start, end, resource):
    if start > end:
        return "End must later than Start"
    res_start = [int(x) for x in resource.available_start.split(':')]
    res_end = [int(x) for x in resource.available_end.split(':')]
    if start.hour < res_start[0] or (start.hour == res_start[0] and start.minute < res_start[1]):
        return "Start time is before the resource available start"
    if end.hour > res_end[0] or (end.hour == res_end[0] and end.minute > res_end[1]):
        return "End time is after the resource available end"
    for reservation in resource.reservations:
        if reservation.end_time > start and reservation.start_time < end:
            return "Reservation in that period"
    return ""
