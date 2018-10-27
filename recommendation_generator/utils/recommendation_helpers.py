import os
import datetime
import random

import pandas as pd
import mysql.connector


def get_db_connection():
    """
    Generate connection to database for querying or putting data

    Returns:
        conn (mysql connection): connection to database
    """

    dbconfig = {
        'host': os.environ['MYSQL_HOST'],
        'database': os.environ['MYSQL_DB'],
        'user': os.environ['MYSQL_USERNAME'],
        'password': os.environ['MYSQL_PASSWORD'],
    }
    conn = mysql.connector.connect(**dbconfig)
    return conn


def get_table_data(table_name,
                   non_dup_columns=None,
                   verbose=True):
    """
    Gets dataframe of table

    Arguments:
        table_name (str): name of table (options are `events`, `searches`, `selected_events`, and `users`)

    Keyword Arguments:
        non_dup_columns (list): columns to exclude from drop duplicates
        verbose (bool): print logging statements

    Returns:
        df (pandas DataFrame): dataframe of table data
    """
    conn = get_db_connection()
    df = pd.read_sql("select * from {}".format(table_name), conn)

    if non_dup_columns:
        if verbose:
            print("Dropping duplicates...")
        dup_columns = [column for column in df.columns if column not in non_dup_columns]
        df.drop_duplicates(dup_columns, inplace=True)

    if verbose:
        print("Shape: {}".format(df.shape))
        print("Columns: {}".format(', '.join(df.columns)))
    return df


def get_canonical_event_adds(min_actions,
                             max_recent_action_days,
                             max_date=pd.Timestamp.today(),
                             verbose=True):
    """
    Get dataframe of user additions to calendar no duplicates before a certain date and which conform
    to active user requirements

    Arguments:
        min_actions (int): min_actions (int): minimum number of actions a user must have undertaken
            to be included in matrix
        max_recent_action_days (int): maximum number of days since a user has undertaken an action

    Returns:
        df_canonical (pandas DataFrame)
    """
    df_selected_events = get_table_data(table_name='selected_events',
                                        non_dup_columns=['id'],
                                        verbose=False)

    df_event_adds_full = (df_selected_events[df_selected_events.selection_type == 'calendar']
                          .drop_duplicates(['user_id', 'event_id']))

    df_event_adds = df_event_adds_full[df_event_adds_full['date_selected'] <= max_date]

    # get indices of users who have undertaken minimum number of actions
    user_adds = df_event_adds.groupby('user_id').size()
    users_w_min_adds = list(user_adds[user_adds >= min_actions].index)

    # get indices of users who have added an event recently
    recent_action_date = max_date - datetime.timedelta(days=max_recent_action_days)
    most_recent_user_add = df_event_adds.groupby('user_id')['date_selected'].max()
    users_w_recent_add = list(most_recent_user_add[most_recent_user_add >= recent_action_date].index)

    # filter dataframe and create flag for pivot
    df_canonical = df_event_adds[(df_event_adds['user_id'].isin(users_w_min_adds)) &
                                 (df_event_adds['user_id'].isin(users_w_recent_add))]

    if verbose:
        print("Shape: {}".format(df_canonical.shape))
        print("Columns: {}".format(', '.join(df_canonical.columns)))
    return df_canonical


def create_ab_set(user_list,
                  model_version):
    """
    Splits users into a and b sets and saves to database

    Arguments:
        user_list (list of str): list of user ids
        model_version (str): model identifier
    """
    test_users = set(random.sample(user_list, len(user_list) // 2))

    conn = get_db_connection()
    cursor = conn.cursor()

    date_added = str(pd.Timestamp.today()).split('.')[0]
    add_rec = ('insert into ab_tests (user_id, test_flag, date_added, model_version)'
               'VALUES (%(user_id)s, %(test_flag)s, %(date_added)s, %(model_version)s)')

    # loop through each user in list adding to ab test
    for user in user_list:
        test_flag = user in test_users
        user_rec = {"user_id": user,
                    "test_flag": test_flag,
                    "model_version": model_version,
                    "date_added": date_added}
        cursor.execute(add_rec, user_rec)

    conn.commit()
    cursor.close()
    conn.close()
