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
import flask, re
from flask import redirect, jsonify, request, json, url_for, make_response, \
    render_template
from flask_login import login_required, login_user, current_user, logout_user
from werkzeug.contrib.atom import AtomFeed
from werkzeug.exceptions import NotFound
from datetime import datetime, timedelta
from models import db, Resource, User, Reservation, Tag
from . import app, login_manager

# --------------------- App configuration ---------------------------
@app.teardown_appcontext
def shutdown_session(exception=None):
    db.session.remove()

@app.before_request
def make_session_permanent():
    flask.session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=10)

@app.teardown_request
def session_clear(exception=None):
    db.session.remove()
    if exception:
        db.session.rollback()

@login_manager.user_loader
def load_user(user_id):
    return db.session.query(User).filter(User.id == int(user_id)).first()

@login_manager.unauthorized_handler
def unauthorized():
    return render_template('unauthorized.html', index_page=True)

@app.errorhandler(404)
def page_not_found(e):
    return render_template(
        '404.html',
        code=404,
        index_page=not current_user.is_authenticated), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template(
        '404.html',
        code=500,
        index_page=not current_user.is_authenticated), 500
# --------------------- End of App configuration ---------------------

# --------------------- User management ------------------------------
######################################################################
# Register a user
######################################################################
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        #print "register template"
        return render_template(
            'login.html',
            message="Please Register",
            button="Register",
            index_page=True)
    data = request.form.to_dict(flat=True)
    user = db.session.query(User).filter_by(email=data['email']).first()
    if user is not None:
        return render_template(
            'login.html',
            message="Please Register, Email already taken",
            button="Register")
    user = User(data['email'] , data['password'])
    db.session.add(user)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    #print 'User successfully registered'
    return redirect(url_for('login'))

######################################################################
# Login a user
######################################################################
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('.list'))
        return render_template(
            'login.html',
            message="Please Login",
            button="Login",
            index_page=True)
    data = request.form.to_dict(flat=True)
    user = db.session.query(User).filter_by(email=data['email']).first()
    if user is None or not user.is_correct_pw(data['password']):
        #print 'Username or Password is invalid'
        return render_template(
            'login.html',
            message="User name or password invalid, Please try again",
            button="Login",
            index_page=True)
    user.authenticated = True
    db.session.add(user)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    login_user(user)
    #print 'Logged in successfully'
    return redirect(url_for('.list'))

######################################################################
# Log out a user
######################################################################
@app.route('/logout', methods=['GET'])
@login_required
def logout():
    user = current_user
    user.authenticated = False
    db.session.add(user)
    try:
        db.session.commit()
    except:
        db.session.rollback()
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
    return render_template('index.html', index_page=True)

######################################################################
# Landing page
######################################################################
@app.route('/home', methods=['GET'])
@login_required
def list():
    '''
    the landing page,
    viewers will see three sections:
    (1) reservations made for resources by that user,
        sorted by reservation time;
    (2) all resources in the system,
        shown in reverse time order based on last made reservation;
    (3) resources that the user owns, each linked to its URL
    (4) a link to create a new resource
    '''
    resources = [res for res in db.session.query(Resource).all()]
    resources.sort(key=lambda x: x.last_reserve_time, reverse=True)
    user = current_user
    my_reservation = \
        [res for res in user.reservations if res.end_time > datetime.now()]
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
        return render_template(
            "form.html",
            action="Add",
            resource={},
            tag="",
            message="")
    data = request.form.to_dict(flat=True)
    data['owner_id'] = current_user.id
    #print data
    if not re.match(r'\d{2}:\d{2}', data['available_start']) \
        or not re.match(r'\d{2}:\d{2}', data['available_end']) \
        or len(data['name']) == 0:
        return render_template(
            "form.html",
            action="Add",
            resource={},
            tag="",
            message="Input Invalid")
    resource = Resource()
    resource.deserialize(data)
    tag_list = data['tag'].split()
    for tag_name in tag_list:
        tag = db.session.query(Tag).filter_by(value=tag_name.lower()).first()
        if not tag:
            tag = Tag(tag_name.lower())
            db.session.add(tag)
        resource.tags.append(tag)
    db.session.add(resource)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('.get_resources', id=resource.id))

######################################################################
# Retrieve a resource
######################################################################
@app.route('/resources/<int:id>', methods=['GET'])
@login_required
def get_resources(id):
    resource = db.session.query(Resource).get(id)
    if not resource:
        raise NotFound("resource with id '{}' was not found.".format(id))
    owner = current_user.id == resource.owner_id
    reservations = \
        [res for res in resource.reservations if res.end_time <= datetime.now()]
    num_past_reservations = len(reservations)
    return render_template(
        "view.html",
        resource=resource,
        owner=owner,
        num_past=num_past_reservations)

######################################################################
# Edit a resource (GET the edit page)
######################################################################
@app.route('/resources/<int:id>/edit', methods=['GET'])
@login_required
def edit_resources(id):
    resource = db.session.query(Resource).get_or_404(id)
    tag_str = ''
    for tag in resource.tags:
        tag_str += tag.value + " "
    return render_template(
        "form.html",
        action="Edit",
        resource=resource,
        tag=tag_str[:-1])

######################################################################
# Edit a resource (POST)
######################################################################
@app.route('/resources/<int:id>/edit', methods=['POST'])
@login_required
def update_resources(id):
    resource = db.session.query(Resource).get_or_404(id)
    data = request.form.to_dict(flat=True)
    data['owner_id'] = current_user.id
    #print data
    if resource is None or data['owner_id'] != resource.owner_id:
        return redirect(url_for('.list'))
    # edit name is not allowed.
    data['name'] = resource.name
    resource.deserialize(data)
    # update tags
    tag_list = data['tag'].split()
    for tag_name in tag_list:
        tag = db.session.query(Tag).filter_by(value=tag_name.lower()).first()
        if not tag:
            tag = Tag(tag_name.lower())
            db.session.add(tag)
        if tag not in resource.tags:
            resource.tags.append(tag)
    db.session.add(resource)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('.get_resources', id=resource.id))

######################################################################
# Delete a resource
######################################################################
@app.route('/resources/<int:id>/delete', methods=['GET'])
@login_required
def delete_resources(id):
    resource = db.session.query(Resource).get(id)
    if resource is not None and resource.owner_id == current_user.id:
        for res in resource.reservations:
            db.session.delete(res)
        db.session.delete(resource)
        try:
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('.list'))

######################################################################
# Get a reservation
######################################################################
@app.route('/reservations/<int:id>', methods=['GET'])
@login_required
def get_res(id):
    reservation = db.session.query(Reservation).get(id)
    if not reservation or reservation.end_time < datetime.now():
        raise NotFound("reservation with id '{}' was not found.".format(id))
    return render_template("view_res.html", reservation=reservation)

######################################################################
# Add a reservation
######################################################################
@app.route('/resources/<int:id>/add_reservation', methods=['GET', 'POST'])
@login_required
def add_res(id):
    resource = db.session.query(Resource).get(id)
    if resource is None:
        raise NotFound("resource with id '{}' was not found.".format(id))
    reservations = \
        [res for res in resource.reservations if res.end_time > datetime.now()]
    reservations.sort(key=lambda x: x.start_time)
    if request.method == 'GET':
        return render_template(
            'form_res.html',
            action="Add Reservation",
            button="Save",
            message="",
            results=reservations)
    data = request.form.to_dict(flat=True)
    try:
        data['start_time'], data['end_time'] = \
            convert_str_to_time(data['date'], data['start'], data['duration'])
    except Exception as e:
        #print e.message
        return render_template(
            'form_res.html',
            action="Add Reservation",
            button="Save",
            message="Time Input Invalid",
            results=reservations)
    message = valid_res(data['start_time'], data['end_time'], resource)
    if message == "":
        message = \
            valid_user_time(data['start_time'], data['end_time'], current_user)
    if message != "":
        return render_template(
            'form_res.html',
            action="Add Reservation",
            button="Save",
            message=message,
            results=reservations)
    data['user_id'] = current_user.id
    data['resource_id'] = id
    data['resource_name'] = resource.name
    resource.last_reserve_time = datetime.now()
    reservation = Reservation()
    reservation.deserialize(data)
    db.session.add(reservation)
    db.session.add(resource)
    try:
        db.session.commit()
    except:
        db.session.rollback()
    return redirect(url_for('.list'))

######################################################################
# Get reservations for one resource
######################################################################
@app.route('/resources/<int:id>/get_reservations', methods=['GET'])
@login_required
def get_res_for_resource(id):
    resource = db.session.query(Resource).get(id)
    if resource is None:
        raise NotFound("resource with id '{}' was not found.".format(id))
    reservations = \
        [res for res in resource.reservations if res.end_time > datetime.now()]
    return render_template(
        "list_res.html",
        reservations=reservations,
        resource=resource)

######################################################################
# Get json reservations for one resource for calendar
######################################################################
@app.route('/resources/<int:id>/get_reservations_object', methods=['GET'])
@login_required
def get_res_for_resource_json(id):
    resource = db.session.query(Resource).get(id)
    if resource is None:
        raise NotFound("resource with id '{}' was not found.".format(id))
    reservations = \
        [res for res in resource.reservations if res.end_time > datetime.now()]
    reservations.sort(key=lambda x: x.start_time)
    results = []
    for res in reservations:
        results.append({"title" : res.id,
                        "start" : res.start_time.strftime("%Y-%m-%dT%H:%M:%S"),
                        "end" : res.end_time.strftime("%Y-%m-%dT%H:%M:%S")})
    return make_response(jsonify(results), 200)

######################################################################
# Delete a reservation
######################################################################
@app.route('/reservations/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_res(id):
    reservation = db.session.query(Reservation).get(id)
    if reservation and reservation.user_id == current_user.id:
        db.session.delete(reservation)
        try:
            db.session.commit()
        except:
            db.session.rollback()
    return redirect(url_for('.list'))

######################################################################
# Get resources with 'tag'
######################################################################
@app.route('/tags/<int:id>', methods=['GET'])
@login_required
def get_resources_with_tag(id):
    tag = db.session.query(Tag).get(id)
    if not tag:
        raise NotFound("tag with id '{}' was not found.".format(id))
    resources = tag.resources
    return render_template(
        "list_tag_resource.html",
        resources=resources,
        tag=tag)

######################################################################
# Get a user's info (reservation, resources)
######################################################################
@app.route('/users/<int:id>', methods=['GET'])
@login_required
def get_user(id):
    user = db.session.query(User).get(id)
    if not user:
        raise NotFound("user with id '{}' was not found.".format(id))
    resources = [res for res in user.resources]
    resources.sort(key=lambda x: x.last_reserve_time, reverse=True)
    reservations = \
        [res for res in user.reservations if res.end_time > datetime.now()]
    reservations.sort(key=lambda x: x.start_time)
    return render_template(
        "list_user_info.html",
        resources=resources,
        reservations=reservations)

######################################################################
# Generate RSS for a resource
######################################################################
@app.route('/resources/<int:id>/rss', methods=['GET'])
@login_required
def generate_rss(id):
    resource = db.session.query(Resource).get(id)
    reservations = \
        [res for res in resource.reservations if res.end_time > datetime.now()]
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
# Search available resource
######################################################################
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search_resource():
    if request.method == 'GET':
        return render_template(
            "form_res.html",
            action="Search Resource",
            button="Search",
            message="",
            results=[])
    data = request.form.to_dict(flat=True)
    try:
        start, end = \
            convert_str_to_time(data['date'], data['start'], data['duration'])
    except Exception as e:
        print e.message
        return render_template(
            'form_res.html',
            action="Search Resource",
            button="Search",
            message="Time Input Invalid",
            results=[])
    if valid_user_time(start, end, current_user) != "":
        return render_template(
            'form_res.html',
            action="Search Resource",
            button="Search",
            message="You already have a reservation during that time",
            results=[])
    results = []
    for res in db.session.query(Resource).all():
        if valid_res(start, end, res) == "":
            results.append(res)
    return render_template(
        'form_res.html',
        action="Search Resource",
        button="Search",
        message="",
        results=results)



######################################################################
#  H E L P E R  F U N C T I O N S
######################################################################
def valid_res(start, end, resource):
    if start > end:
        return "End must later than Start"
    res_start = [int(x) for x in resource.available_start.split(':')]
    res_end = [int(x) for x in resource.available_end.split(':')]
    if start < datetime.now():
        return "Start time can't be in the past"
    if (start.hour < res_start[0] or \
        (start.hour == res_start[0] and start.minute < res_start[1])):
        return "Start time is before the resource available start"
    if (end.hour > res_end[0] or \
        (end.hour == res_end[0] and end.minute > res_end[1])):
        return "End time is after the resource available end"
    for reservation in resource.reservations:
        if reservation.end_time > start and reservation.start_time < end:
            return "Reservation in that period, check below"
    return ""

def valid_user_time(start, end, user):
    for reservation in user.reservations:
        if reservation.end_time > start and reservation.start_time < end:
            return "You can only make one reservation at a time"
    return ""

def convert_str_to_time(d, s, du):
    date = [int(x) for x in d.split('-')]
    start = [int(x) for x in s.split(':')]
    duration = [int(x) for x in du.split(':')]
    end = [start[0]+duration[0], start[1]+duration[1]]
    if end[1] == 60:
        end[0], end[1] = end[0] + 1, 0
    res_s = datetime(date[0], date[1], date[2], start[0], start[1])
    res_e = datetime(date[0], date[1], date[2], end[0], end[1])
    return res_s, res_e
