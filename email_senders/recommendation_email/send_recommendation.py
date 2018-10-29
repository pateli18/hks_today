import os
from datetime import datetime

import sendgrid

import email_helpers


def get_users_to_email(db_config, ab_test, model_version):
    """
    Gets list of user ids to email with recommendations

    Arguments:
        db_config (dict): db configuration variables
        ab_test (bool): boolean on whether or not to run an ab test
        model_version (str): version of model to send recommendations for

    Returns:
        users (list of str): list of user ids
    """
    if ab_test:
        query = """
        SELECT users.id, users.email
        FROM ab_tests
        JOIN users
        ON ab_tests.user_id = users.id
        WHERE model_version = '{0}' AND test_flag = 1
        """.format(model_version)
        users = email_helpers.get_users_from_query(config=db_config,
                                                   query=query)
    else:
        query = "SELECT id, email FROM users WHERE recommendation_subscribed = 1"
        users = email_helpers.get_users_from_query(config=db_config,
                                                   query=query)
    return users


def get_popular_events(db_config, num_popular_events):
    """
    Queries for most popular events, returning a formatted dict for use in email

    Arguments:
        db_config (dict): db configuration variables
        num_popular_events (int): number of popular events to query

    Returns:
        popular_events (dict): formatted dict for passing through html email generator
    """

    # run query
    popular_events_query = """
    SELECT events.id, events.title, events.start_time, events.end_time, events.location, events.description
    FROM
        (SELECT event_id, count(*) adds
         FROM selected_events
         WHERE selection_type = 'calendar'
         GROUP BY 1
         ORDER BY 2 DESC) as event_counts
    JOIN events
    ON event_counts.event_id = events.id
    WHERE events.start_time > curdate()
    LIMIT {0};
    """.format(num_popular_events)
    popular_events_results = email_helpers.get_events_from_query(db_config, popular_events_query)

    # create formatted dict
    popular_events = {"name": "Popular Events",
                      "events": popular_events_results,
                      "selection_source": "popular"}
    return popular_events


def get_user_recommendations(db_config, user_id, model_version, max_recs):
    """
    Queries event recommendations for a specified user, adding them in a list formatted for email

    Arguments:
        db_config (dict): db configuration variables
        user_id (str): id of user to query recommendations for
        model_version (str): version of model to send recommendations for
        max_recs (int): maximum recommendations a user can receive

    Returns:
        user_recs (dict): formatted dict for passing through html email generator
    """

    # run query
    recommendations_query = """
    SELECT events.id, events.title, events.start_time, events.end_time, events.location, events.description
    FROM recommendations
    JOIN events
    ON recommendations.event_id = events.id
    WHERE recommendations.user_id = '{0}'
    AND recommendations.model_version = '{1}'
    AND date(recommendations.date_added) = curdate()
    ORDER BY events.start_time
    LIMIT {2}
    """.format(user_id, model_version, max_recs)
    recommendations = email_helpers.get_events_from_query(db_config, recommendations_query)

    # create formatted dict
    user_recs = {"name": "Recommended Events",
                 "events": recommendations,
                 "selection_source": "recommended"}
    return user_recs


def add_popular_events(user_rec, popular_events):
    """
    Add popular events to individual user recommendations, avoiding duplicates between
    model recommendations and popular events

    Arguments:
        user_recs (dict): formatted dict for passing through html email generator
        popular_events (dict): formatted dict for passing through html email generator

    Returns:
        full_user_rec (list of dicts): list with both user_recs and de-duped popular events
    """

    # only keep popular events not already recommended to user
    event_rec_ids = {event["id"] for event in user_rec["events"]}
    user_popular_events = popular_events.copy()
    user_popular_events["events"] = [event for event in user_popular_events["events"]
                                     if event["id"] not in event_rec_ids]

    # combine recommendations and popular events in list
    full_user_rec = [user_rec, user_popular_events]
    return full_user_rec


def generate_email_html(events):
    """
    Creates html to be used in an email body

    Arguments:
        events (list of dicts): list which has both user recommendations and popular events

    Returns:
        html (str): html for email body
    """
    html = '<html><body><div style="width:100%;padding-top:.75em;padding-bottom:.75em;padding-left:.25em;background-color:#f7f7f7;"><a href="www.hks.today" style="font-size:1.6em;color:#A51C30;text-decoration: none;"><strong>HKS</strong>Today Events for You</a></div>'
    for event_type in events:
        html += '<div style="color: #1E1E1E;font-size: 1.2em;margin-top:10px;font-weight: bold;">{0}</div>'.format(event_type["name"])
        event_list = event_type["events"]
        if len(event_list) > 0:
            for event in event_list:
                html += '<a href="www.hks.today/{0}/{1}"><div style="color:#A51C30;font-size:1em;font-weight:bold;margin-top:10px;text-decoration:none;">{2}</div></a>'.format(event['id'], event_type['selection_source'], event['title'])
                html += '<p style="color: #8996A0;font-size:.8em;font-style: italic;margin-top:0px;margin-bottom:0px;">{0}</p>'.format(event["timing_location"])
                html += '<p style="font-size:.8em;margin-top:0px;margin-bottom:0px;">{0}</p>'.format(event['description'])
                html += '<a style="font-size:.8em;" href="www.hks.today/add_to_google_cal/{0}/{1}">(Add to Calendar)</a><br>'.format(event['id'], event_type['selection_source'])
        else:
            html += '<p style="font-size:.8em;margin-top:0px;margin-bottom:0px;">No {0}</p>'.format(event_type["name"])
    html += '<br><br><a href="www.hks.today/preferences" style="font-size:.6em;">Unsubscribe</a></body></html>'
    return html


def send_recommendation_email(db_config, sendgrid_config, email_config):
    """
    Gets recommendations, creates emails, and sends emails to users

    Arguments:
        db_config (dict): db configuration variables
        sendgrid_config (dict): sendgrid configuration variables
        email_config (dict): configuration variables unique to this function
    """

    users = get_users_to_email(db_config=db_config,
                               ab_test=email_config["ab_test"],
                               model_version=email_config["model_version"])

    popular_events = get_popular_events(db_config=db_config,
                                        num_popular_events=email_config["num_popular_events"])

    # test the function by only emailing the test email
    testing = bool(int(os.environ["TESTING"]))
    if testing:
        print("Running test, excluding emails of {} users".format(len(users)))
        users = [{"id": os.environ["TEST_ID"], "email": os.environ["TEST_EMAIL"]}]

    # only send an email if future events exist
    if len(popular_events["events"]) > 0:

        sg = sendgrid.SendGridAPIClient(**sendgrid_config)

        for user in users:

            # get events specific to user and create html
            user_rec = get_user_recommendations(db_config=db_config,
                                                user_id=user["id"],
                                                model_version=email_config["model_version"],
                                                max_recs=email_config["max_recs"])

            full_user_rec = add_popular_events(user_rec=user_rec,
                                               popular_events=popular_events)

            email_html = generate_email_html(full_user_rec)

            # create email body and send
            email_data = {"personalizations": [{"to": [{"email": user["email"]}]}],
                          "content": [{"type": "text/html", "value": email_html}],
                          "from": {"email": "recommendations@hks.today", "name": "HKSToday"},
                          "subject": "HKS Recommended Events - {0}".format(datetime.today().strftime('%a, %b %d'))}
            response = sg.client.mail.send.post(request_body=email_data)
            print(response.status_code)
            print(response.body)
            print(response.headers)


def recommendation_email_handler(event, context):
    db_config = {
        'host': os.environ['MYSQL_HOST'],
        'database': os.environ['MYSQL_DB'],
        'user': os.environ['MYSQL_USERNAME'],
        'password': os.environ['MYSQL_PASSWORD'],
    }
    sendgrid_config = {
        'api_key': os.environ['SENDGRID_API_KEY']
    }
    email_config = {
        'ab_test': int(os.environ['AB_TEST']),
        'model_version': os.environ['MODEL_VERSION'],
        'num_popular_events': int(os.environ['NUM_POPULAR_EVENTS']),
        'max_recs': int(os.environ['MAX_RECS'])
    }
    send_recommendation_email(db_config, sendgrid_config, email_config)


if __name__ == '__main__':
    recommendation_email_handler(None, None)
