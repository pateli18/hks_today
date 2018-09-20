

def create_event_db_object(form, current_user_id):
    """
    Format object from `create_event_object` for use in db

    Arguments:
        form (dict): dict of post request data
        current_user_id (str): id of user creating event

    Returns:
        event (dict): dict of event info formatted for db consumption
    """
    event = {'title': form['title'],
             'start_time': form['date'] + 'T' + form['start_time'],
             'end_time': form['date'] + 'T' + form['end_time'],
             'location': form['location'],
             'description': form['description'],
             'rsvp_date': form['rsvp_deadline'],
             'rsvp_email_url': form['rsvp_email_url'],
             'rsvp_required': (form['rsvp_email_url'] != ''),
             'ticketed_event': (form['ticketed_event_instructions'] != ''),
             'ticketed_event_instructions': form['ticketed_event_instructions'],
             'contact_name': form['contact_name'],
             'contact_email': form['contact_email'],
             'source': 'user',
             'source_id': current_user_id}
    for field in event:
        event[field] = None if event[field] == '' else event[field]
    return event
