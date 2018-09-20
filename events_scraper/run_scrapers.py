import os
from scrapers import HKSScraper


def scrape_data(hks_config, dbconfig):
    """
    Runs HKS Scraper

    Arguments:
        hks_config (dict): dict of configuration for hks scraper
        dbconfig (dict): dict of configuration for database

    Returns:
        events_log (str): describes number of events added to the db on a specific day
    """
    hks_scraper = HKSScraper(hks_config['username'],
                             hks_config['password'],
                             dbconfig)
    print('Running Program')
    events_log = hks_scraper.get_new_events()
    print(events_log)
    return events_log


def handler(event, context):
    """
    Handler function used by aws lambda. Load configuration variables and run scraper

    Arugments:
        event (): required by lambda function
        context (): required by lambda function

    Returns:
        events_log (str): describes number of events added to the db on a specific day
    """
    dbconfig = {
        'host': os.environ['MYSQL_HOST'],
        'database': os.environ['MYSQL_DB'],
        'user': os.environ['MYSQL_USERNAME'],
        'password': os.environ['MYSQL_PASSWORD'],
    }
    hks_config = {
        'username': os.environ['KNET_USERNAME'],
        'password': os.environ['KNET_PASSWORD'],
    }
    events_log = scrape_data(hks_config, dbconfig)
    return events_log


if __name__ == '__main__':
    handler(None, None)
