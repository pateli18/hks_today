import pytz
import datetime

from HarvardEvents import db
from HarvardEvents import models


def user_selected_events_subquery(user_id):
    """
    Creates subquery to determine which events user has already added to calendar

    Arguments:
        user_id (str): id of user

    Returns:
        subquery (SQLAlchemy Subquery): query that determines which event a user has added to their calendar
    """
    subquery = (db.session.query(models.EventSelection.event_id)
                          .filter(models.EventSelection.user_id == user_id)
                          .filter(models.EventSelection.selection_type == 'calendar')
                          .subquery())
    return subquery


def get_events_query(user_id, search_term=None):
    """
    Returns query results getting future events, either all of them or those matching a search term

    Arguments:
        user_id (str): user id of current session
        search_term (str): user search term, if None return all events
    """
    current_datetime = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%Y-%m-%d %H:%M:00')
    event_user_subquery = user_selected_events_subquery(user_id)

    if search_term:
        # query different fields for presence of search term,
        # joined with event ids which user has already added to calendar
        search_term_query = '%{0}%'.format(search_term)
        event_query = (db.session.query(models.Event, event_user_subquery)
                                 .filter(models.Event.end_time >= current_datetime)
                                 .filter((models.Event.description.ilike(search_term_query)) |
                                         (models.Event.title.ilike(search_term_query)) |
                                         (models.Event.policy_topics.ilike(search_term_query)) |
                                         (models.Event.academic_areas.ilike(search_term_query)) |
                                         (models.Event.geographic_regions.ilike(search_term_query)) |
                                         (models.Event.degrees_programs.ilike(search_term_query)) |
                                         (models.Event.centers_initiatives.ilike(search_term_query)))
                                 .order_by(models.Event.start_time)
                                 .outerjoin(event_user_subquery)
                                 .all())

    else:
        # get all future events, joined with event ids which user has already added to calendar
        event_query = (db.session.query(models.Event, event_user_subquery)
                                 .filter(models.Event.end_time >= current_datetime)
                                 .order_by(models.Event.start_time)
                                 .outerjoin(event_user_subquery)
                                 .all())

    return event_query
