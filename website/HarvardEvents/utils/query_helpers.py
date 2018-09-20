import HarvardEvents


def user_selected_events_subquery(user_id):
    """
    Creates subquery to determine which events user has already added to calendar

    Arguments:
        user_id (str): id of user

    Returns:
        subquery (SQLAlchemy Subquery): query that determines which event a user has added to their calendar
    """
    subquery = (HarvardEvents.db.session.query(HarvardEvents.models.EventSelection.event_id)
                                        .filter(HarvardEvents.models.EventSelection.user_id == user_id)
                                        .filter(HarvardEvents.models.EventSelection.selection_type == 'calendar')
                                        .subquery())
    return subquery
