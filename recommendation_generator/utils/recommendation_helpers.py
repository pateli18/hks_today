import os

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


def get_canonical_event_adds(max_date=pd.Timestamp.today(),
                             verbose=True):
    """
    Get dataframe of user additions to calendar no duplicates before a certain date

    Returns:
        df_event_adds (pandas DataFrame)
    """
    df_selected_events = get_table_data(table_name='selected_events',
                                        non_dup_columns=['id'],
                                        verbose=False)

    df_event_adds_full = (df_selected_events[df_selected_events.selection_type == 'calendar']
                          .drop_duplicates(['user_id', 'event_id']))

    df_event_adds = df_event_adds_full[df_event_adds_full['date_selected'] <= max_date]

    if verbose:
        print("Shape: {}".format(df_event_adds.shape))
        print("Columns: {}".format(', '.join(df_event_adds.columns)))
    return df_event_adds
