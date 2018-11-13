import datetime
import json

import pandas as pd

from utils import recommendation_helpers


def get_recommendations(model_version):
    """
    Gets a Pandas Dataframe of recommendations for a specific model version

    Arguments:
        model_version (str): model being evaluated

    Returns:
        recommendations (Pandas DataFrame): dataframe with user id and event id
    """
    sql_query = """
    SELECT user_id, event_id
    FROM recommendations
    WHERE model_version = '{}'
    """.format(model_version)
    recommendations = pd.read_sql(sql_query, recommendation_helpers.get_db_connection())
    return recommendations


def get_ab_tests(model_version):
    """
    Get a Pandas DataFrame of users in the ab_test for a specific model veresion along with
    their recommendation subscription status

    Arguments:
        model_version (str): model being evaluated

    Returns:
        ab_tests (Pandas DataFrame): dataframe with user id, ab test flag, and recommendation email flag
    """

    sql_query = """
    SELECT ab_tests.user_id, ab_tests.test_flag, users.recommendation_subscribed
    FROM ab_tests
    JOIN users ON ab_tests.user_id = users.id
    WHERE ab_tests.model_version = '{}'
    """.format(model_version)
    ab_tests = pd.read_sql(sql_query, recommendation_helpers.get_db_connection())

    return ab_tests


def get_selected_events(start_date):
    """
    Gets user actions that have been added to calendar after a chosen start date,
    deleting duplicates (same user adding the same event)

    Arguments:
        start_data (str): minimum date from which to pull user actions

    Returns:
        selected_events (Pandas Dataframe): dataframe with user id, event id, selection source and start time
    """
    sql_query = """
    SELECT selected_events.user_id, selected_events.event_id, selected_events.selection_source, events.start_time
    FROM selected_events
    JOIN events ON selected_events.event_id = events.id
    WHERE selected_events.selection_type = 'calendar'
    AND events.start_time >= STR_TO_DATE('{}', '%Y-%m-%d')
    """.format(start_date)
    selected_events = pd.read_sql(sql_query, recommendation_helpers.get_db_connection())
    selected_events.drop_duplicates(['event_id', 'user_id'], inplace=True)
    return selected_events


def get_week_event_adds(current_week, selected_events):
    """
    Retrieves user adds for a given week

    Arguments:
        current_week (datetime): start date for a given week (Sunday)
        selected_events (Pandas DataFrame): dataframe produced by `get_selected_events`

    Returns:
        user_adds (Pandas DataFrame): dataframe with number of events added by a user for
            a given week
    """
    next_week = current_week + datetime.timedelta(days=7)
    user_adds = (selected_events[(selected_events.start_time >= current_week) &
                 (selected_events.start_time <= next_week)]
                 .groupby('user_id')['event_id']
                 .size()
                 .reset_index())
    user_adds['week'] = current_week
    return user_adds


def get_weekly_user_add_count(min_date, max_date, selected_events):
    """
    Gets a dataframe of the number of events the user added for all weeks between 2 dates

    Arguments:
        min_date (datetime date): earliest date to calculate events adds on
        max_date (datetime date): maximum date to calculate event adds on
        selected_events (Pandas DataFrame): dataframe produced by `get_selected_events`

    Returns:
        weekly_user_adds (Pandas Dataframe): dataframe with user id, user adds, and the week
    """
    weeks = (max_date - min_date).days // 7
    weekly_user_adds = pd.DataFrame()

    # loop through each week and append to dataframe
    for week in range(weeks + 1):
        current_week = min_date + datetime.timedelta(days=week * 7)
        user_adds = get_week_event_adds(current_week=current_week, selected_events=selected_events)
        weekly_user_adds = pd.concat([weekly_user_adds, user_adds], axis=0)

    weekly_user_adds.columns = ['user_id', 'user_adds', 'week']
    return weekly_user_adds


def create_before_after_sets(weekly_user_adds, ab_tests, ab_test_flag, recommendation_date):
    """
    Filters data from `get_weekly_user_add_count` for users on one side of test and split it before and
    after a specified recommendation date, returning the number of adds

    Arguments:
        weekly_user_adds (Pandas DataFrame): dataframe returned by `get_weekly_user_add_count`
        ab_tests (Pandas DataFrame): dataframe returned by `get_ab_tests`
        ab_test_flag (bool): indicate whether or not user is participating in the ab test
        recommendation_date (datetime date): date at which model recommendations are deployed

    Returns:
        weekly_adds_before (Pandas Series): user event adds before the recommendation date
        weekly_adds_after (Pandas Series): user event adds after the recommendation date
    """

    # filter for one set of users in the ab test
    user_ids = ab_tests[ab_tests.test_flag == ab_test_flag].user_id.tolist()
    weekly_adds_filtered = weekly_user_adds[weekly_user_adds.user_id.isin(user_ids)]

    # split data into before and after
    weekly_adds_before = weekly_adds_filtered[weekly_adds_filtered.week <= recommendation_date]['user_adds']
    weekly_adds_after = weekly_adds_filtered[weekly_adds_filtered.week > recommendation_date]['user_adds']

    return weekly_adds_before, weekly_adds_after


def get_aggregate_metrics(weekly_user_adds, ab_tests, recommendation_date):
    """
    Gets comparison statistics between user sets in a and b test before and after a recommendation model
    was deployed

    Arguments:
        weekly_user_adds (Pandas DataFrame): dataframe returned by `get_weekly_user_add_count`
        ab_tests (Pandas DataFrame): dataframe returned by `get_ab_tests`
        recommendation_date (datetime date): date at which model recommendations are deployed

    Returns:
        metrics (list of dicts): list with items for each metric (sum, mean, median) comparison for each set
    """
    weekly_adds_before_recs, weekly_adds_after_recs = create_before_after_sets(
        weekly_user_adds=weekly_user_adds,
        ab_tests=ab_tests,
        ab_test_flag=1,
        recommendation_date=recommendation_date)

    weekly_adds_before_no_recs, weekly_adds_after_no_recs = create_before_after_sets(
        weekly_user_adds=weekly_user_adds,
        ab_tests=ab_tests,
        ab_test_flag=0,
        recommendation_date=recommendation_date)

    metrics = [
        {'metric': 'sum',
         'recs': True, 'before': int(weekly_adds_before_recs.sum()),
         'after': int(weekly_adds_after_recs.sum())},
        {'metric': 'sum',
         'recs': False,
         'before': int(weekly_adds_before_no_recs.sum()),
         'after': int(weekly_adds_after_no_recs.sum())},
        {'metric': 'mean',
         'recs': True, 'before': weekly_adds_before_recs.mean(),
         'after': weekly_adds_after_recs.mean()},
        {'metric': 'mean',
         'recs': False,
         'before': weekly_adds_before_no_recs.mean(),
         'after': weekly_adds_after_no_recs.mean()},
        {'metric': 'median',
         'recs': True, 'before': weekly_adds_before_recs.median(),
         'after': weekly_adds_after_recs.median()},
        {'metric': 'median',
         'recs': False,
         'before': weekly_adds_before_no_recs.median(),
         'after': weekly_adds_after_no_recs.median()},
    ]

    return metrics


def create_production_performance_report(min_date,
                                         max_date,
                                         model_version,
                                         recommendation_date):
    """
    Creates a json report of various metrics that can be used to evaluate a recommendation model's performance in
    production

    Arguments:
        min_date (datetime date): earliest date to calculate events adds on
        max_date (datetime date): maximum date to calculate event adds on
        model_version (str): version of model that is being evaluated
        recommendation_date (datetime date): date at which model recommendations are deployed

    Returns:
        report (json): json of various metrics
    """

    # initialize report json
    report = {}

    # pull selected events and ab tests from db
    selected_events = get_selected_events(start_date=min_date)
    ab_tests = get_ab_tests(model_version=model_version)

    # add aggregate metrics to report
    weekly_user_adds = get_weekly_user_add_count(min_date=min_date, max_date=max_date, selected_events=selected_events)
    report['metrics'] = get_aggregate_metrics(weekly_user_adds=weekly_user_adds,
                                              ab_tests=ab_tests,
                                              recommendation_date=recommendation_date)

    # add selection sources
    report['selection_sources'] = (selected_events[selected_events.start_time > recommendation_date]
                                   .selection_source
                                   .value_counts()
                                   .to_dict())

    # add proportion of people still subscribed to recommendations
    user_recs = ab_tests[ab_tests.test_flag == 1].user_id.tolist()
    report['recs_subscribed_proportion'] = (ab_tests[ab_tests.user_id.isin(user_recs)]['recommendation_subscribed']
                                            .sum() / len(user_recs) * 100)

    # add proportion of recommendations that were actually selected
    recommendations = get_recommendations(model_version=model_version)
    report['recs_selected_proportion'] = (recommendations.merge(selected_events, on=['user_id', 'event_id']).shape[0] /
                                          recommendations.shape[0] * 100)

    return report


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--min_date',
                        '-min',
                        default='20180909',
                        type=str,
                        help='Earliest date to calculate events adds on, format should be YYYYMMDD')

    parser.add_argument('--max_date',
                        '-max',
                        required=True,
                        type=str,
                        help='Latest date to calculate events adds on, format should be YYYYMMDD')

    parser.add_argument('--model_version',
                        '-model',
                        required=True,
                        type=str,
                        help='Version number of model being evaluated')

    parser.add_argument('--recommendation_date',
                        '-rec',
                        required=True,
                        type=str,
                        help='Date at which model recommendations are deployed, format should be YYYYMMDD')

    parser.add_argument('--report_save_folder',
                        '-report',
                        default='production_reports/',
                        type=str,
                        help='Folder to save report in')

    args = parser.parse_args()

    report = create_production_performance_report(
        min_date=datetime.datetime.strptime(args.min_date, '%Y%m%d').date(),
        max_date=datetime.datetime.strptime(args.max_date, '%Y%m%d').date(),
        model_version=args.model_version,
        recommendation_date=datetime.datetime.strptime(args.recommendation_date, '%Y%m%d').date()
    )

    # save report to json
    with open('{}{}-{}.json'.format(args.report_save_folder, args.model_version, args.max_date), 'w') as f:
        json.dump(report, f)
