import mysql.connector


def format_timing_location(start_time, end_time, location):
    """
    Formats time and location into string consumable by email

    Arguments:
        start_time (datetime): start time of event
        end_time (datetime): end time of event
        location (str): location of event

    Returns:
        time_location_fmt (str): formatted message with time and location
    """
    start_time_fmt = start_time.strftime('%I:%M %p')
    end_time_fmt = end_time.strftime('%I:%M %p')
    mins = int((end_time - start_time).seconds / 60)

    time_location_fmt = '{0} - {1} ({2} mins) at {3}'.format(start_time_fmt,
                                                             end_time_fmt,
                                                             mins,
                                                             location)

    return time_location_fmt


def get_users_from_query(config, query):
    """
    Gets list of users from provided sql query

    Arguments:
        config (dict): db parameters
        query (str): sql query

    Returns:
        users (list of str): list of user ids
    """
    # execute query
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(query)

    users = [{"id": _id, "email": email} for _id, email in cursor]

    cursor.close()
    conn.close()

    return users


def get_events_from_query(config, query):
    """
    Gets list of events for populating email from a given query

    Arguments:
        config (dict): dict of config variables for database
        query (str): sql query

    Returns
        events (list of dicts): list ordered by date and list of events per element
    """

    # execute query
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(query)

    # put inidividual event info in list and separate out date for aggregation down below
    events = [{'id': _id,
               'title': title,
               'timing_location': format_timing_location(start_time, end_time, location),
               'description': description}
              for _id, title, start_time, end_time, location, description in cursor]
    cursor.close()
    conn.close()

    return events
