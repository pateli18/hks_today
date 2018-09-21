import sendgrid
import os
from sendgrid.helpers.mail import *
import datetime
import mysql.connector

import send_daily_helpers


def get_newly_added_events(config):
    """
    Gets list of events newly added to db

    Arguments:
        config (dict): dict of config variables for database

    Returns
        events (list of dicts): list ordered by date and list of events per element
    """
    filter_date = datetime.datetime.today() - datetime.timedelta(days=1)

    sql_query = """
    select id, title, start_time, end_time, location, description
    from events where date_added >= '{0}'
    order by start_time
    """.format(str(filter_date).split(' ')[0])

    events = send_daily_helpers.get_events_from_query(config, sql_query)

    return events


def get_weekly_events(config):
    """
    Gets events for the next week

    Arguments:
        config (dict): dict of config variables for database

    Returns
        events (list of dicts): list ordered by date and list of events per element
    """

    start_date = datetime.datetime.today()
    end_date = start_date + datetime.timedelta(days=6)

    sql_query = """
    select id, title, start_time, end_time, location, description
    from events where start_time >= '{0}' and start_time < '{1}' order by start_time
    """.format(str(start_date).split(' ')[0], str(end_date).split(' ')[0])

    events = send_daily_helpers.get_events_from_query(config, sql_query)

    return events


def generate_email_html(events, subject, link_ref):
    """
    Creates html for the email

    Arguments:
        events (list of dicts): list ordered by date and list of events per element
        subject (str): subject of email
        link_ref (str): reference tag for storing info on source of user click

    Returns:
        html (str): html of email body
    """

    # initialize html and creates header
    html = '<html><body><div style="width:100%;padding-top:.75em;padding-bottom:.75em;padding-left:.25em;background-color:#f7f7f7;"><a href="www.hks.today" style="font-size:1.6em;color:#A51C30;text-decoration: none;"><strong>HKS</strong>Today {0}</a></div>'.format(subject)

    # loops through each date in events list
    for date in events:

        # create date header
        html += '<div style="color: #1E1E1E;font-size: 1.2em;margin-top:10px;font-weight: bold;">{0}</div>'.format(date['date'])

        # adds event info
        for event in date['events']:
            html += '<a href="www.hks.today/{0}/{1}"><div style="color:#A51C30;font-size:1em;font-weight:bold;margin-top:10px;text-decoration:none;">{2}</div></a>'.format(event['id'], link_ref, event['title'])
            html += '<p style="color: #8996A0;font-size:.8em;font-style: italic;margin-top:0px;margin-bottom:0px;">{0}</p>'.format(event['timing_location'])
            html += '<p style="font-size:.8em;margin-top:0px;margin-bottom:0px;">{0}</p>'.format(event['description'])
            html += '<a style="font-size:.8em;" href="www.hks.today/add_to_google_cal/{0}/{1}">(Add to Calendar)</a><br>'.format(event['id'], "weekly_email")

    # create unsubscribe link and close body
    html += '<br><br><a href="www.hks.today/preferences" style="font-size:.6em;">Unsubscribe</a></body></html>'
    return html


def get_users_to_email(config, param):
    """
    Get users subscribed to specific email

    Arguments:
        config (dict): dict of config variables for database
        param (str): name of specific email list

    Returns:
        users (list of str): list of user emails
    """
    sql_statement = 'select email from users where {0} = 1'.format(param)
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    cursor.execute(sql_statement)
    users = [user[0] for user in cursor]
    cursor.close()
    conn.close()

    # test the function by only emailing the test email
    testing = bool(int(os.environ["TESTING"]))
    if testing:
        print(len(users))
        users = [os.environ["TEST_EMAIL"]]
    return users


def generate_email(events, sg, param, subject_text, link_ref, dbconfig):
    """
    Generates and sends email to user

    Arguments:
        events (list of dicts): list ordered by date and list of events per element
        sg (SendGridAPIClient): sendgrid client for sending an email
        param (str): name of specific email list
        subject_text (str): subject of email
        link_ref (str): reference tag for storing info on source of user click
        dbconfig (dict): dict of config variables for database
    """
    users = get_users_to_email(dbconfig, param)

    # only send an email if there are relevant events
    if len(events) > 0:

        from_email = Email("dailyupdate@hks.today", "HKS Today")
        subject = "HKS {0} - {1}".format(subject_text, datetime.datetime.today().strftime('%a, %b %d'))
        html_body = generate_email_html(events, subject_text, link_ref)
        content = Content('text/html', html_body)
        print("content", content)
        mail = Mail(from_email, subject, from_email, content)

        # add users to email in bcc
        for user in users:
            mail.personalizations[0].add_bcc(Email(user))

        # send email and print results
        response = sg.client.mail.send.post(request_body=mail.get())
        print(response.status_code)
        print(response.body)
        print(response.headers)

    else:
        print("No Events")


def send_daily_events_email(dbconfig, sendgridconfig):
    """
    Creates and sends both the weekly events and newly added events email

    Arguments:
        dbconfig (dict): dict of config variables for database
        sendgridconfig (dict): dict of config variables for sendgrid client
    """
    weekly_events = get_weekly_events(dbconfig)
    new_events = get_newly_added_events(dbconfig)

    sg = sendgrid.SendGridAPIClient(**sendgridconfig)

    generate_email(weekly_events, sg, "daily_subscribed", "This Week", "weekly_email", dbconfig)
    generate_email(new_events, sg, "newevents_subscribed", "New Events", "newevent_email", dbconfig)


def daily_handler(event, context):
    """
    Handler function used by aws lambda. Load configuration variables and send emails

    Arugments:
        event (): required by lambda function
        context (): required by lambda function
    """
    dbconfig = {
        'host': os.environ['MYSQL_HOST'],
        'database': os.environ['MYSQL_DB'],
        'user': os.environ['MYSQL_USERNAME'],
        'password': os.environ['MYSQL_PASSWORD'],
    }
    sendgridconfig = {
        'api_key': os.environ['SENDGRID_API_KEY']
    }
    send_daily_events_email(dbconfig, sendgridconfig)


if __name__ == '__main__':
    daily_handler(None, None)
