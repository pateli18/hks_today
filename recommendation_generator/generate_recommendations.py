import os

import mysql.connector
import pandas as pd
import numpy as np
from scipy.sparse.linalg import svds

MODEL_VERSION = '0.0.0'


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


def get_canonical_event_adds(verbose=True):
    """
    Get dataframe of user additions to calendar no duplicates

    Returns:
        df_event_adds (pandas DataFrame)
    """
    df_selected_events = get_table_data(table_name='selected_events',
                                        non_dup_columns=['id'],
                                        verbose=False)

    df_event_adds = (df_selected_events[df_selected_events.selection_type == 'calendar']
                     .drop_duplicates(['user_id', 'event_id']))

    if verbose:
        print("Shape: {}".format(df_event_adds.shape))
        print("Columns: {}".format(', '.join(df_event_adds.columns)))
    return df_event_adds


def get_user_event_df(min_actions):
    """
    Gets dataframe with user ids as index and event ids as columns,
    with a flag as the value if the user has added the event

    Arguments:
        min_actions (int): minimum number of actions a user must have undertaken to be included in matrix

    Returns:
        user_event_df (Pandas DataFrame): dataframe with users as index and events as columns
    """
    df = get_canonical_event_adds(verbose=False)

    # get indices of users who have undertaken minimum number of actions
    user_adds = df.groupby('user_id').size()
    selected_users = list(user_adds[user_adds >= min_actions].index)

    # filter dataframe and create flag for pivot
    df_clean = df[df['user_id'].isin(selected_users)]
    df_clean['flag'] = 1

    user_event_df = df_clean.pivot(index='user_id', columns='event_id', values='flag')
    user_event_df.fillna(0, inplace=True)

    print("Matrix Shape: ", user_event_df.shape)
    return user_event_df


def get_predictions_df(user_event_df,
                       k):
    """
    Gets scores for each user event pair

    Arguments:
        user_event_df (Pandas DataFrame): dataframe with users as index and events as columns
        k (int): vector size

    Returns:
        predictions_df (Pandas DataFrame): dataframe with users as index and events as columns
    """

    # Calculate svd score
    U, sigma, Vt = svds(user_event_df, k=k)
    sigma = np.diag(sigma)
    predictions_matrix = np.dot(np.dot(U, sigma), Vt)

    # rescale matrix between 1 and 0
    predictions_matrix = ((predictions_matrix - predictions_matrix.min()) /
                          (predictions_matrix.max() - predictions_matrix.min()))

    # input matrix scores into df
    predictions_df = pd.DataFrame(predictions_matrix, columns=user_event_df.columns)
    predictions_df.index = user_event_df.index

    return predictions_df


def get_upcoming_events(date_filter=pd.Timestamp.today()):
    """
    Gets events that have not occurred yet

    Keyword Arguments:
        date_filter (datetime): date to filter upcoming events for

    Returns:
        upcoming_events (list): list of event ids which have not occured yet
    """

    events = get_table_data(table_name='events',
                            non_dup_columns=['id', 'date_added'],
                            verbose=False)

    date = pd.to_datetime(date_filter)
    upcoming_events = events[events['start_time'] > date]['id'].tolist()

    return upcoming_events


def get_recommendations(predictions_df,
                        user_event_df,
                        threshold):
    """
    Gets recommendations for each user

    Arguments:
        predictions_df (Pandas DataFrame): dataframe with users as index and events as columns
        user_event_df (Pandas DataFrame): dataframe with users as index and events as columns
        threshold (float): threshold at which an event is recommended

    Returns:
        user_recommendations (dict): dict with user ids and list of events per user
    """

    all_upcoming_events = get_upcoming_events()

    # only keep those events which at least one other user has added
    relevant_upcoming_events = [event for event in all_upcoming_events if event in user_event_df.columns]

    # filter out recommendations for events the user has already added
    predictions_upcoming_events_df = (predictions_df[relevant_upcoming_events] *
                                      ((user_event_df[relevant_upcoming_events] - 1) * -1))

    # creates dict with user id as key and list of recommended events
    user_recommendations = {}
    for index, row in predictions_upcoming_events_df.iterrows():
        user_recommendations[index] = [event for event in relevant_upcoming_events if row[event] > threshold]

    return user_recommendations


def add_recs_to_db(user_recommendations):
    # initialize connector
    conn = get_db_connection()
    cursor = conn.cursor()

    date_added = str(pd.Timestamp.today()).split('.')[0]
    add_rec = ('insert into recommendations (user_id, event_id, date_added)'
               'VALUES (%(user_id)s, %(event_id)s, %(date_added)s)')

    users_w_recs = 0
    total_recs = 0

    # loop through each user in dict, adding event rec to database
    for user in user_recommendations:
        user_recs = user_recommendations[user]
        if len(user_recs) > 0:
            users_w_recs += 1
        for user_rec in user_recs:
            user_rec = {"user_id": user,
                        "event_id": user_rec,
                        "date_added": date_added,
                        "model_version": MODEL_VERSION}
            cursor.execute(add_rec, user_rec)
            total_recs += 1

    conn.commit()
    cursor.close()
    conn.close()

    return users_w_recs, total_recs


def generate_recommendations(recs_config):
    """
    Runs each of the steps in the pipeline for generating recommendations

    Arguments:
        recs_config (dict): dictionary of config variable for generating recommendations
    """
    print("Getting User Event Matrix")
    user_event_df = get_user_event_df(recs_config["min_user_actions"])

    print("Calculating Predictions")
    predictions_df = get_predictions_df(user_event_df, recs_config["vector_size"])

    print("Extracting Predictions")
    user_recommendations = get_recommendations(predictions_df, user_event_df, recs_config["threshold"])

    print("Saving Predictions")
    users_w_recs, total_recs = add_recs_to_db(user_recommendations)

    print("Generated {0} recommendations for {1} users".format(total_recs, users_w_recs))


def generate_recommendation_handler(event, context):
    """
    Handler function used by aws lambda. generate recommendations and send to database

    Arguments:
        event (): required by lambda function
        context (): required by lambda function
    """
    recs_config = {
        'min_user_actions': int(os.environ["MIN_USER_ACTIONS"]),
        'vector_size': int(os.environ["VECTOR_SIZE"]),
        'threshold': float(os.environ["THRESHOLD"])
    }

    generate_recommendations(recs_config)


if __name__ == '__main__':
    generate_recommendation_handler(None, None)
