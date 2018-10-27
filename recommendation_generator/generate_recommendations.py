import os
import datetime

import pandas as pd
import numpy as np
from scipy.sparse.linalg import svds

from utils import recommendation_helpers

MODEL_VERSION = '0.0.0'


def get_user_event_df(min_actions,
                      max_recent_action_days=14,
                      max_date=pd.Timestamp.today(),
                      verbose=False):
    """
    Gets dataframe with user ids as index and event ids as columns,
    with a flag as the value if the user has added the event

    Arguments:
        min_actions (int): minimum number of actions a user must have undertaken to be included in matrix

    Returns:
        user_event_df (Pandas DataFrame): dataframe with users as index and events as columns
    """
    df = recommendation_helpers.get_canonical_event_adds(max_date=max_date,
                                                         verbose=verbose)

    # get indices of users who have undertaken minimum number of actions
    user_adds = df.groupby('user_id').size()
    users_w_min_adds = list(user_adds[user_adds >= min_actions].index)

    # get indices of users who have added an event recently
    recent_action_date = max_date - datetime.timedelta(days=max_recent_action_days)
    most_recent_user_add = df.groupby('user_id')['date_selected'].max()
    users_w_recent_add = list(most_recent_user_add[most_recent_user_add >= recent_action_date].index)

    # filter dataframe and create flag for pivot
    df_clean = df[(df['user_id'].isin(users_w_min_adds)) & (df['user_id'].isin(users_w_recent_add))]
    df_clean['flag'] = df_clean.shape[0] * [1]

    user_event_df = df_clean.pivot(index='user_id', columns='event_id', values='flag')
    user_event_df.fillna(0, inplace=True)

    if verbose:
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
    # k cannot be larger than minimum dimension on df
    min_dim = min(user_event_df.shape)
    if k > min_dim:
        k = min_dim - 1

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

    events = recommendation_helpers.get_table_data(table_name='events',
                                                   non_dup_columns=['id', 'date_added'],
                                                   verbose=False)

    date = pd.to_datetime(date_filter)
    upcoming_events = events[events['start_time'] > date]['id'].tolist()

    return upcoming_events


def get_recommendations(predictions_df,
                        user_event_df,
                        threshold,
                        date_filter=pd.Timestamp.today()):
    """
    Gets recommendations for each user

    Arguments:
        predictions_df (Pandas DataFrame): dataframe with users as index and events as columns
        user_event_df (Pandas DataFrame): dataframe with users as index and events as columns
        threshold (float): threshold at which an event is recommended

    Returns:
        user_recommendations (dict): dict with user ids and list of events per user
    """

    all_upcoming_events = get_upcoming_events(date_filter)

    # only keep those events which at least one other user has added
    relevant_upcoming_events = [event for event in all_upcoming_events if event in user_event_df.columns]

    # filter out recommendations for events the user has already added
    predictions_upcoming_events_df = (predictions_df[relevant_upcoming_events] *
                                      ((user_event_df[relevant_upcoming_events] - 1) * -1))

    # creates dict with user id as key and list of recommended events
    user_recommendations = {}
    for index, row in predictions_upcoming_events_df.iterrows():
        user_recommendations[index] = list({event for event in relevant_upcoming_events if row[event] > threshold})

    return user_recommendations


def add_recs_to_db(user_recommendations):
    # initialize connector
    conn = recommendation_helpers.get_db_connection()
    cursor = conn.cursor()

    date_added = str(pd.Timestamp.today()).split('.')[0]
    add_rec = ('insert into recommendations (user_id, event_id, date_added, model_version)'
               'VALUES (%(user_id)s, %(event_id)s, %(date_added)s, %(model_version)s)')

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
                        "model_version": MODEL_VERSION,
                        "date_added": datetime.datetime.today()}
            cursor.execute(add_rec, user_rec)
            total_recs += 1

    conn.commit()
    cursor.close()
    conn.close()

    return users_w_recs, total_recs


def generate_recommendations(recs_config,
                             add_to_db=True,
                             date_filter=pd.Timestamp.today(),
                             verbose=False):
    """
    Runs each of the steps in the pipeline for generating recommendations

    Arguments:
        recs_config (dict): dictionary of config variable for generating recommendations

    Returns:
        user_recommendations (dict): dict with user ids and list of events per user
    """
    if verbose:
        print("Getting User Event Matrix")
    user_event_df = get_user_event_df(min_actions=recs_config["min_user_actions"],
                                      max_recent_action_days=recs_config["max_recent_action_days"],
                                      max_date=date_filter,
                                      verbose=verbose)

    # if no event matrix, don't return anything
    if min(user_event_df.shape) > 1:

        if verbose:
            print("Calculating Predictions")
        predictions_df = get_predictions_df(user_event_df=user_event_df,
                                            k=recs_config["vector_size"])
        if verbose:
            print("Extracting Predictions")
        user_recommendations = get_recommendations(predictions_df=predictions_df,
                                                   user_event_df=user_event_df,
                                                   threshold=recs_config["threshold"],
                                                   date_filter=date_filter)

        if add_to_db:
            if verbose:
                print("Saving Predictions")
            users_w_recs, total_recs = add_recs_to_db(user_recommendations)

            if verbose:
                print("Generated {0} recommendations for {1} users".format(total_recs, users_w_recs))

    else:

        user_recommendations = {}

    return user_recommendations


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
        'threshold': float(os.environ["THRESHOLD"]),
        'max_recent_action_days': float(os.environ["MAX_RECENT_ACTION_DAYS"])
    }

    user_recommendations = generate_recommendations(recs_config=recs_config,
                                                    add_to_db=True)

    return user_recommendations


if __name__ == '__main__':
    # run simulation if running the function locally
    from recommendation_simulation import run_simulation
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--min_user_actions',
                        '-m',
                        required=True,
                        type=int,
                        help='Mininum number of events user must have added to generate recommendations for them')

    parser.add_argument('--vector_size',
                        '-v',
                        required=True,
                        type=int,
                        help='Size of svd vector')

    parser.add_argument('--threshold',
                        '-t',
                        required=True,
                        type=float,
                        help='Threshold over which to include recommendation for user')

    parser.add_argument('--max_recent_action_days',
                        '-r',
                        required=True,
                        type=int,
                        help='Max days since user has taken an action in order to be included in recommendation set')

    parser.add_argument('--start_date',
                        '-s',
                        required=True,
                        type=str,
                        help='Date at which to start simulation')

    parser.add_argument('--end_date',
                        '-e',
                        required=True,
                        type=str,
                        help='Date at which to end simulation')

    parser.add_argument('--output_path',
                        '-o',
                        default='./simulation_reports/',
                        type=str,
                        help='Folder in which to save report')

    parser.add_argument('--include_user_results',
                        '-i',
                        default=False,
                        type=bool,
                        help='Include individual user data in results report')

    parser.add_argument('--processes',
                        '-p',
                        default=4,
                        type=int,
                        help='Number of processes to run in simulation')

    args = parser.parse_args()

    function_parameters = {'recs_config': {'min_user_actions': args.min_user_actions,
                                           'vector_size': args.vector_size,
                                           'threshold': args.threshold,
                                           'max_recent_action_days': args.max_recent_action_days},
                           'add_to_db': False}

    run_simulation(model_version=MODEL_VERSION,
                   function=generate_recommendations,
                   function_parameters=function_parameters,
                   start_date_str=args.start_date,
                   end_date_str=args.end_date,
                   output_path=args.output_path,
                   include_user_results=args.include_user_results,
                   pool_processes=args.processes)
