import datetime

import httplib2
from flask import render_template, request, url_for, redirect, make_response, flash
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from oauth2client.client import OAuth2WebServerFlow, AccessTokenCredentials, AccessTokenCredentialsError
from apiclient import discovery

from HarvardEvents.models import Event, EventSelection, Search, User
from HarvardEvents import app, db

from HarvardEvents.utils import query_helpers
from HarvardEvents.utils import event_creation_helpers

"""
Global Variables
"""

# initialize login manager
login_manager = LoginManager(app)

# initialize Oauth2 flow
flow = OAuth2WebServerFlow(client_id=app.config['CLIENT_ID'],
                           client_secret=app.config['CLIENT_SECRET'],
                           scope=['https://www.googleapis.com/auth/calendar', 'email'],
                           redirect_uri=app.config['REDIRECT_URI'])

# initialize credentials
credentials = None

"""
User login handlers
"""


@login_manager.user_loader
def load_user(user_id):
    """
    Call back for flask_login, used to reload user session

    Arguments:
        user_id (str): id string of user

    Returns:
        user (HarvardEvents.models.User): user object
    """
    user = db.session.query(User).filter_by(id=user_id).first()
    return user


@app.route('/login')
def login():
    """
    Logs user in via Google

    Returns:
        redirect to either Google authorization url or main mage
    """
    if current_user.is_authenticated:
        return redirect(url_for('all_events_viewer'))
    auth_url = flow.step1_get_authorize_url()
    return redirect(auth_url)


@app.route('/logout')
def logout():
    """
    Logs user out, returns to main page
    """
    if current_user.is_authenticated:
        logout_user()
    return redirect(url_for('all_events_viewer'))


"""
HKS Today Functions
"""


@app.route('/')
def all_events_viewer():
    """
    Creates view for main page

    Returns:
        resp (Flask Response): Main page of the site
    """
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'

    # search handler
    if 'search' in request.args:
        search_term = request.args.get('search')

        # add search term to db
        search_item = Search(user_id=user_id, search=search_term)
        db.session.add(search_item)
        db.session.commit()
    else:
        search_term = None

    event_query = query_helpers.get_events_query(user_id, search_term)
    num_events = len(event_query)
    # loop through every event in events query and create a dict with date and events keys, with events as
    # an item with a single list
    template_data = {"search_term": search_term, "num_search_events": num_events}
    template_data["all_events"] = []
    for event_object, flag in event_query:
        event = event_object.get_tile_data

        # flag event if user has selected it before
        event['user_flag'] = (flag is not None) if user_id != 'anonymous' else False
        template_data["all_events"].append(event)

    # if there are not events and the user has conducted a search return no search results found
    if len(template_data["all_events"]) == 0 and 'search' in request.args:
        flash('No Search Results found for {0}'.format(search_term), 'danger')
        return redirect(url_for('all_events_viewer'))

    # get user scroll position
    scroll_position = request.cookies.get('scroll_position')
    resp = make_response(render_template('index.html',
                                         data=template_data,
                                         scroll=scroll_position))

    # delete scroll position cookie
    resp.set_cookie('scroll_position', expires=0)
    return resp


@app.route('/<event_id>/<selection_source>')
def individual_event_viewer(event_id, selection_source):
    """
    Creates individual event viewer page

    Arguments:
        event_id (str): id of the event being selected
        selection_source (str): location of link

    Returns:
        resp (Flask Response): Page for an individual event
    """
    # TODO: make this do it doesn't have to be called every page
    user_id = current_user.id if current_user.is_authenticated else 'anonymous'

    # add the user click to the db
    selected_event = EventSelection(user_id=user_id,
                                    event_id=event_id,
                                    selection_type='link',
                                    selection_source=selection_source)
    db.session.add(selected_event)
    db.session.commit()

    # create response
    event = db.session.query(Event).filter_by(id=event_id).one().get_tile_data
    resp = make_response(render_template('individual_event.html',
                                         data=event))
    resp.set_cookie('scroll_position', 'event_{}'.format(event_id))
    return resp


@app.route('/preferences')
@login_required
def view_preferences():
    """
    Display user preferences page

    Returns:
        resp (Flask Response): User preferences page
    """
    # get events submitted by individual user
    submitted_events = [{'id': id, 'title': title, 'upcoming_flag': (start_time > datetime.datetime.today())}
                        for id, title, start_time in
                        (db.session.query(Event.id, Event.title, Event.start_time)
                                   .filter(Event.source_id == current_user.id)
                                   .order_by(Event.start_time)
                                   .all())]

    # get events user has added to calendar
    today = datetime.datetime.today()
    event_user_subquery = query_helpers.user_selected_events_subquery(current_user.id)
    previous_events = [{'id': id, 'title': title}
                       for id, title in (db.session.query(Event.id, Event.title)
                       .filter(Event.id.in_(event_user_subquery))
                       .filter(Event.start_time <= today)
                       .all())]

    upcoming_events = [{'id': id, 'title': title}
                       for id, title in (db.session.query(Event.id, Event.title)
                       .filter(Event.id.in_(event_user_subquery))
                       .filter(Event.start_time > today)
                       .all())]

    data = {"email": current_user.email,
            "daily_subscribed": current_user.daily_subscribed,
            "newevents_subscribed": current_user.newevents_subscribed,
            "recommendation_subscribed": current_user.recommendation_subscribed,
            "submitted_events": submitted_events,
            "previous_events": previous_events,
            "upcoming_events": upcoming_events}

    resp = make_response(render_template('user_preferences.html',
                                         data=data))

    return resp


@app.route('/change_preferences', methods=['POST'])
@login_required
def change_preferences():
    """
    Change user preferences, can only change one at a time

    Returns:
        preference_redirect (Flask Redirect): Redirect for preferences page
    """
    # change user's email
    if 'email' in request.form:
        email = request.form['email']
        current_user.update({"email": email})
        db.session.add(current_user)
        db.session.commit()
        flash('Email Changed To: {0}'.format(email), 'success')

    # change whether user receives daily subscription emails
    elif 'daily_subscription' in request.args:
        # TODO: add change preference function
        preference = False if request.args.get('daily_subscription') == 'true' else True
        current_user.daily_subscribed = preference
        db.session.add(current_user)
        db.session.commit()
        flash('Subscription Preferences Changed', 'success')

    # change whether user receives new events subscription emails
    elif 'newevents_subscription' in request.args:
        preference = False if request.args.get('newevents_subscription') == 'true' else True
        current_user.newevents_subscribed = preference
        db.session.add(current_user)
        db.session.commit()
        flash('Subscription Preferences Changed', 'success')

    # change whether user receives recommendation subscription emails
    elif 'recommendation_subscription' in request.args:
        preference = False if request.args.get('recommendation_subscription') == 'true' else True
        current_user.recommendation_subscribed = preference
        db.session.add(current_user)
        db.session.commit()
        flash('Subscription Preferences Changed', 'success')
    else:
        flash('No Preferences Changed', 'warning')

    preference_redirect = redirect(url_for('view_preferences'))
    return preference_redirect


@app.route('/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    """
    Adds user created event

    Returns:
        if 'GET' and user created event or unsuccessful 'POST':
            resp (Flask Response): Add event page
        else:
            a redirect for all events page
    """
    if request.method == 'POST':

        # either update an existing event or create a new event
        event_object = event_creation_helpers.create_event_db_object(request.form, current_user.id)
        if 'edit' in request.args:
            event = db.session.query(Event).filter(Event.id == request.args.get('edit'))
            event.update(event_object)
        else:
            event = Event(**event_object)
            db.session.add(event)
        db.session.commit()
        flash('Event Successfully Submitted', 'success')
        return redirect(url_for('all_events_viewer'))

    # display event page with event
    if request.method == 'GET':
        if 'edit' in request.args:
            event_object = db.session.query(Event).filter(Event.id == request.args.get('edit')).first()
            event = event_object.add_event_object

            # user has not created event, do not allow them to edit it
            if event['info']['source_id'] != current_user.id:
                flash("You did not create the event so you cannot edit it", 'danger')
                return redirect(url_for('all_events_viewer'))
            for field in event['info']:
                if event['info'][field] is None:
                    event['info'][field] = ''
        else:
            event = {'type': 'new'}

    data = {"event_data": event}
    data["min_date"] = datetime.datetime.today().strftime('%Y-%m-%d')

    resp = render_template('add_event.html',
                           data=data)

    return resp


@app.route('/delete_event/<event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    """
    Deletes user added event

    Arguments:
        event_id (str): id of the event being deleted

    Returns:
        preference_redirect (Flask Redirect): Redirect for preferences page
    """
    event = db.session.query(Event).filter(Event.id == event_id).first()

    # do not let user delete the event if they did not create it or if the event has already passed
    if current_user.id != event.source_id:
        flash('You cannot delete this event because you did not create it', 'danger')
    elif event.start_time < datetime.datetime.today():
        flash('You cannot delete this event because it has already passed', 'danger')
    else:
        # remove the data of the event selections of the event before deleting it
        selectedevents = db.session.query(EventSelection).filter(EventSelection.event_id == event_id).all()
        for selectedevent in selectedevents:
            db.session.delete(selectedevent)
        db.session.commit()
        db.session.delete(event)
        db.session.commit()
        flash('Event Deleted', 'success')

    preference_redirect = redirect(url_for('view_preferences'))
    return preference_redirect


"""
Google OAuth Functions
"""


@app.route('/add_to_google_cal/<event_id>/<selection_source>')
def add_to_google_calendar(event_id, selection_source):
    """
    Adds event to user's google calendar

    Arguments:
        event_id (str): id of the event being selected
        selection_source (str): location of link

    Returns:
        resp (Flask Response): Varies depending on whether user is logged in
    """
    if current_user.is_authenticated:
        try:
            # adds user selection to database
            selected_event = EventSelection(user_id=current_user.id,
                                            event_id=event_id,
                                            selection_type='calendar',
                                            selection_source=selection_source)
            db.session.add(selected_event)
            db.session.commit()

            # gets google calendar event of object
            event = db.session.query(Event).filter_by(id=event_id).one().google_calendar_event

            # add event to google calendar
            credentials = AccessTokenCredentials(current_user.token, None)
            http = credentials.authorize(httplib2.Http())
            service = discovery.build('calendar', 'v3', http=http)
            event = service.events().insert(calendarId='primary', body=event).execute()

            # redirect user to main page
            flash('Event added to Google Calendar', 'success')
            resp = make_response(redirect(url_for('all_events_viewer')))
            resp.set_cookie('add_event', 'false')
            resp.set_cookie('scroll_position', 'event_{}'.format(event_id))
            return resp

        # if user token has expired log the user out and redirect to login page
        except AccessTokenCredentialsError:
            logout_user()

    resp = make_response(redirect(url_for('login')))
    resp.set_cookie('event_id', event_id)
    resp.set_cookie('selection_source', selection_source)
    resp.set_cookie('add_event', 'true')
    return resp


@app.route('/google_callback')
def callback():
    """
    Callback method from Google after user adds event to the calendar

    Returns:
        redirect (Flask Redirect): redirect to appropriate page
    """

    # if oauth request was successful a code will be returned
    if 'code' in request.args:

        # get oauth user profile
        auth_code = request.args.get('code')
        credentials = flow.step2_exchange(auth_code)
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('oauth2', 'v2', http=http)
        user_profile = service.userinfo().get().execute()
        user_id = user_profile['id']

        # create new user if first time or update user access_token in db
        user = db.session.query(User).filter_by(id=user_id).first()
        if user is None:
            user = User(id=user_id, email=user_profile['email'])
        user.token = credentials.access_token
        db.session.add(user)
        db.session.commit()

        login_user(user)

        # if the user tried to add an event and then oauth was called, redirect to the add event call
        if request.cookies.get('add_event') == 'true':
            page_redirect = redirect(url_for('add_to_google_calendar',
                                             event_id=request.cookies.get('event_id'),
                                             selection_source=request.cookies.get('selection_source')))
    # redirect to main page if login was successful or not
        else:
            flash('Login Successful', 'success')
            page_redirect = redirect(url_for('all_events_viewer'))
    else:
        flash('Login failed', 'danger')
        page_redirect = redirect(url_for('all_events_viewer'))

    return page_redirect
