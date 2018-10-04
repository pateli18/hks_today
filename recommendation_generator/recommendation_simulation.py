import datetime
import json

import pandas as pd
import multiprocessing

from utils import recommendation_helpers


def get_all_user_adds(user_recommendations,
                      max_date=pd.Timestamp.today()):
    """
    Gets dict of sets of all events a user has added for calculation of model stats

    Arguments:
        user_recommendations (dict of sets): dict of user ids with sets of all events recommended to the user

    Returns:
        event_adds (dict of sets): dict of user ids with sets of all events added by the user to calendar
    """
    df = recommendation_helpers.get_canonical_event_adds(max_date=max_date,
                                                         verbose=True)
    event_adds = {}
    for user, row in df.groupby('user_id'):
        if user in user_recommendations:
            event_adds[user] = set(row['event_id'].tolist())
    return event_adds


def get_weekly_date_list(start_date, end_date):
    """
    Gets list of dates in weekly intervals between start and end date (includes start and end date)

    Arguments:
        start_date (datetime)
        end_date (datetime)

    Returns:
        date_list (list of datetime)
    """
    num_days = (end_date - start_date).days + 1
    date_list = [start_date + datetime.timedelta(days=i) for i in range(7, num_days, 7)]
    return date_list


def get_total_result_count(user_results,
                           param_name):
    """
    Calculates the total count of a specific param ('correct', 'missed', 'unchosen') over all users

    Arguments:
        user_results (dict of dicts): {user_id:{'correct': {'count': ..., 'events': ...}, ...}, ...}
        param_name (str): name of parameter

    Returns:
        total_result_count (int): total count of param in dataset
    """
    total_result_count = sum([user_results[user][param_name]['count'] for user in user_results])
    return total_result_count


def get_timestamp():
    """
    Gets timestamp at which the report was run and formats it

    Returns:
        timestamp (str): YYYY-MM-DDvHH-MM
    """
    full_date = str(pd.Timestamp.today())
    timestamp = full_date.split(' ')[0] + 'v' + full_date.split(' ')[1][:5].replace(':', '-')
    return timestamp


def get_results_metrics(user_choices,
                        user_recommendations,
                        function,
                        function_parameters,
                        model_version,
                        start_date_str,
                        end_date_str,
                        output_path='./simulation_reports/',
                        include_user_results=False):
    """
    Calculates metrics at the user and total level for a simulation run, saving a json of the results

    Arguments:
        user_choices (dict of sets): {user_id: {event1, event2, ...}, ...}
        user_recommendations (dict of sets): {user_id: {event1, event2, ...}, ...}
        function (function): function on which simulation was run on
        function_parameters (dict): parameters of model function for simulation
        model_version (str): model version on which simulation was run on
        start_date_str (str):start date of simulation
        end_date_str (str): end date of siimulation
    """
    recommender_results = {}

    # create dict which separates event recommendations into correct (recommended and added by user),
    # missed (not recommended and added by user), and unchosen (recommended and not added by user)
    user_results = {}
    for user in user_choices:
        user_results[user] = {}
        choices = user_choices[user]
        recommendations = user_recommendations[user]

        # separate evenets into three categories
        correct_events = set.intersection(choices, recommendations)
        missed_events = choices - correct_events
        unchosen_events = recommendations - correct_events

        user_results[user]['correct'] = {'count': len(correct_events), 'events': list(correct_events)}
        user_results[user]['missed'] = {'count': len(missed_events), 'events': list(missed_events)}
        user_results[user]['unchosen'] = {'count': len(unchosen_events), 'events': list(unchosen_events)}

    if include_user_results:
        recommender_results['user_results'] = user_results

    # get total metrics
    total_correct = get_total_result_count(user_results=user_results,
                                           param_name='correct')

    total_missed = get_total_result_count(user_results=user_results,
                                          param_name='missed')

    total_unchosen = get_total_result_count(user_results=user_results,
                                            param_name='unchosen')

    total_records = total_correct + total_unchosen

    recommender_results['correct'] = {'count': total_correct, 'pct': '{0:.2%}'.format(total_correct / total_records)}
    recommender_results['missed'] = {'count': total_missed, 'pct': '{0:.2%}'.format(total_missed / total_records)}
    recommender_results['unchosen'] = {'count': total_unchosen, 'pct': '{0:.2%}'.format(total_unchosen / total_records)}
    recommender_results['total'] = total_records
    recommender_results['recs_per_user'] = '{0:.2f}'.format(total_records / len(user_choices.keys()))

    # add model / function metadata
    recommender_results['timestamp'] = get_timestamp()
    recommender_results['function_name'] = function.__name__

    recommender_results['function_params'] = function_parameters
    recommender_results['model_version'] = model_version

    # save report to jsons
    filename = '{0}{1}_{2}.json'.format(output_path, model_version, recommender_results['timestamp'])
    with open(filename, 'w') as outfile:
        json.dump(recommender_results, outfile)
    print('File saved to {0}'.format(filename))


def simulate_date(function,
                  function_parameters,
                  date):
    """
    Simulate an individual date, used by multiprocessing step

    Arguments:
        function (function): function on which simulation was run on
        function_parameters (dict): parameters of model function for simulation
        date (datetime): date to run function for

    Returns:
        date_recs (dict of sets): {user_id:{event_id, ...}, ...}
    """
    function_parameters['date_filter'] = date
    date_recs = function(**function_parameters)
    print('{} complete...'.format(date))
    return date_recs


def run_simulation(model_version,
                   function,
                   function_parameters,
                   start_date_str,
                   end_date_str,
                   pool_processes=4,
                   output_path='./simulation_reports/',
                   include_user_results=False):
    """
    Runs a simulation of the chosen model/function over a specified time period before passing results to
    get results metrics

    Arguments:
        model_version (str): model version on which simulation was run on
        function (function): function on which simulation was run on
        function_parameters (dict): parameters of model function for simulation
        start_date_str (str):start date of simulation
        end_date_str (str): end date of siimulation
    """

    # get date range
    start_date = pd.to_datetime(start_date_str)
    end_date = pd.to_datetime(end_date_str)
    date_list = get_weekly_date_list(start_date, end_date)

    # create worker data for multiprocessing
    worker_data = [(function, function_parameters, date)
                   for date in date_list]

    # run multiprocessing
    pool = multiprocessing.Pool(pool_processes)
    all_date_recs = pool.starmap(simulate_date, worker_data)

    # aggregate individual date results
    recommended_event_adds = {}
    for date_recs in all_date_recs:
        for user in date_recs:
            previous_events = recommended_event_adds.get(user, set())
            all_events = previous_events | date_recs[user]
            recommended_event_adds[user] = all_events

    actual_event_adds = get_all_user_adds(user_recommendations=recommended_event_adds,
                                          max_date=end_date)

    get_results_metrics(user_choices=actual_event_adds,
                        user_recommendations=recommended_event_adds,
                        function=function,
                        function_parameters=function_parameters,
                        model_version=model_version,
                        start_date_str=start_date_str,
                        end_date_str=end_date_str,
                        output_path=output_path,
                        include_user_results=include_user_results)
