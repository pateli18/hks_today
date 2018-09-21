from bs4 import BeautifulSoup
import requests
import datetime
import mysql.connector


class Scraper(object):
    """
    Class for general purpose scraper that can be applied beyond HKS
    """

    def __init__(self, config):
        """
        Initialize scraper class

        Arguments:
            config (dict): dict of config variables for database
        """
        self.config = config
        self.events_to_add = []
        self.pulled_events = set()

    def reset(self):
        """
        Reset scraper
        """
        self.events_to_add = []
        self.pulled_events = set()

    def get_pulled_events(self):
        """
        Get events that have already been scraped so that the scraper doesn't add to the database again
        """
        # create cursor
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        # set filter date to previous date
        filter_date = datetime.datetime.today() - datetime.timedelta(days=1)

        # execute query and get ids of events already scraped with a start time after yesterday
        cursor.execute("select source_id from events where start_time >= %s", (filter_date, ))
        self.pulled_events = set(event[0] for event in cursor)
        cursor.close()
        conn.close()

    def add_events_to_db(self):
        """
        Add new event or update existing event in db

        Returns:
            events_log (str): describes number of events added to the db on a specific day
        """

        # initialize connector
        conn = mysql.connector.connect(**self.config)
        cursor = conn.cursor()

        # sql template to add event
        add_event = ('insert into events (source, source_id, title, short_description, speaker, sponsor, co_sponsor,'
                     'additional_sponsor, start_time, end_time, event_type, location, description, intranet_homepage,'
                     'public_site, hks_today_email, ticketed_event, ticketed_event_instructions, ad_day_one, ad_day_two,'
                     'contact_name, contact_email, phone_number, rsvp_required, rsvp_date, rsvp_email_url, existing_website,'
                     'policy_topics, academic_areas, geographic_regions, degrees_programs, centers_initiatives, key_terms, date_added)'
                     'VALUES ("hks", %(source_id)s, %(title)s, %(short_description)s, %(speaker)s, %(sponsor)s, %(cosponsors)s,'
                     '%(additional_sponsors)s, %(start_time)s, %(end_time)s, %(event_type)s, %(location)s, %(description)s, %(intranet_home_page)s,'
                     '%(public_site)s, %(hks_today_email)s, %(ticketed_event)s, %(ticketed_event_instructions)s, %(advertisement_day_1)s, %(advertisement_day_2)s,'
                     '%(contact_name)s, %(contact_email_address)s, %(phone_number)s, %(rsvp_required)s, %(rsvp_date)s, %(rsvp_email_or_url)s, %(link_to_an_existing_website)s,'
                     '%(policy_topics)s, %(academic_areas)s, %(geographic_regions)s, %(degrees_&_programs)s, %(centers_&_initiatives)s, %(key_terms)s, %(date_added)s)')

        # sql template to update event
        update_event = ('update events set title=%(title)s, short_description=%(short_description)s, speaker=%(speaker)s, sponsor=%(sponsor)s, co_sponsor=%(cosponsors)s,'
                        'additional_sponsor=%(additional_sponsors)s, start_time=%(start_time)s, end_time=%(end_time)s, event_type=%(event_type)s, location=%(location)s, description=%(description)s, intranet_homepage=%(intranet_home_page)s,'
                        'public_site=%(public_site)s, hks_today_email=%(hks_today_email)s, ticketed_event=%(ticketed_event)s, ticketed_event_instructions=%(ticketed_event_instructions)s, ad_day_one=%(advertisement_day_1)s, ad_day_two=%(advertisement_day_2)s,'
                        'contact_name=%(contact_name)s, contact_email=%(contact_email_address)s, phone_number=%(phone_number)s, rsvp_required=%(rsvp_required)s, rsvp_date=%(rsvp_date)s, rsvp_email_url=%(rsvp_email_or_url)s, existing_website=%(link_to_an_existing_website)s,'
                        'policy_topics=%(policy_topics)s, academic_areas=%(academic_areas)s, geographic_regions=%(geographic_regions)s, degrees_programs=%(degrees_&_programs)s, centers_initiatives=%(centers_&_initiatives)s, key_terms=%(key_terms)s'
                        ' where source_id=%(source_id)s')

        new_additions_counter = 0
        for event in self.events_to_add:

            # update existing event
            if event['source_id'] in self.pulled_events:
                cursor.execute(update_event, event)
            # add new event
            else:
                print(event)
                event["date_added"] = str(datetime.datetime.today()).split('.')[0]
                cursor.execute(add_event, event)
                new_additions_counter += 1
        conn.commit()
        cursor.close()
        conn.close()

        events_log = '{0}: {1} Events Added to DB'.format(datetime.datetime.today(), new_additions_counter)
        return events_log

    def get_new_events(self):
        """
        Main function to call on scraper class

        Returns:
            events_log (str): describes number of events added to the db on a specific day
        """
        self.get_pulled_events()
        self.scrape_new_events()
        events_log = self.add_events_to_db()
        self.reset()
        return events_log


class HKSScraper(Scraper):
    """
    Scraper specifically for HKS events
    """

    def __init__(self, username, password, config):
        """
        Initialize hks scraper

        Arguments:
            username (str): KNET (HKS Intranet) username
            password (pword): KNET (HKS Intranet) password
            config (dict): dict of config variables for database
        """
        super().__init__(config)
        self.base_url = 'https://knet.hks.harvard.edu/CookieAuth.dll?Logon'
        self.events_url = "https://knet.hks.harvard.edu/Pages/AllEvents.aspx"

        # payload to login to KNET
        self.payload = {
            'username': username,
            'password': password,
            'curl': 'Z2FPagesZ2Fdefault.aspx',
            'flags': '0',
            'forcedownlevel': '0',
            'formdir': '3',
            'rdoPblc': '0',
            'rdoPrvt': '4',
            'SubmitCreds': 'Log On',
        }

    def parse_event_data(self, event_soup):
        """
        Parse the html of an individual event on KNET

        Arguments:
            event_soup (BeautifulSoup): soup of event page

        Returns:
            event_info (dict): dict with event labels and corresponding values
        """
        required_fields = ['source_id',
                           'title',
                           'short_description',
                           'speaker',
                           'sponsor',
                           'cosponsors',
                           'additional_sponsors',
                           'start_time',
                           'end_time',
                           'event_type',
                           'location',
                           'description',
                           'intranet_home_page',
                           'public_site',
                           'hks_today_email',
                           'ticketed_event',
                           'ticketed_event_instructions',
                           'advertisement_day_1',
                           'advertisement_day_2',
                           'contact_name',
                           'contact_email_address',
                           'phone_number',
                           'rsvp_required',
                           'rsvp_date',
                           'rsvp_email_or_url',
                           'link_to_an_existing_website',
                           'policy_topics',
                           'academic_areas',
                           'geographic_regions',
                           'degrees_&_programs',
                           'centers_&_initiatives',
                           'key_terms']
        # get the field labels
        field_headers = [field.text for field in event_soup.findAll('h3', {'class': 'ms-standardheader'})]

        # get the field values
        fields_clean = [field.text.replace('\t', '').replace('\n', '').replace('\r', '').replace('\xa0', '')
                        for field in event_soup.findAll('td', {'class': 'ms-formbody'})]

        # loop through headers and fields, adding to dict and setting value to None if blank
        event_info = {}
        for header, field in zip(field_headers, fields_clean):
            header = header.replace(' ', '_').lower().replace('_(if_any)', '').replace('-', '')
            if field == '':
                field = None
            event_info[header] = field
        field_labels = set(event_info.keys())

        # if field not present on page, set equal to None
        for field in required_fields:
            if field not in field_labels:
                event_info[field] = None

        # convert columns to True / False
        boolean_columns = ['intranet_home_page',
                           'public_site',
                           'hks_today_email',
                           'ticketed_event',
                           'rsvp_required']
        for column in boolean_columns:
            event_info[column] = (event_info[column] == 'Yes')

        # convert columns to date
        date_columns = ['advertisement_day_1',
                        'advertisement_day_2',
                        'rsvp_date']
        for column in date_columns:
            if event_info[column] is not None:
                event_info[column] = datetime.datetime.strptime(event_info[column], '%m/%d/%Y').strftime('%Y-%m-%d')

        # convert columns to time
        date_time_columns = ['start_time',
                             'end_time']
        for column in date_time_columns:
            if event_info[column] is not None:
                event_info[column] = datetime.datetime.strptime(event_info[column],
                                                                '%m/%d/%Y %I:%M %p').strftime('%Y-%m-%d %H:%M:00')
        return event_info

    def create_event_source_id(self, event_url):
        """
        Create the unique id for the event

        Arguments:
            event_url (str): url of event page

        Returns:
            formatted_id (str): unique id of event
        """
        split_url = event_url.split('/')
        org_header = split_url[3] + '-' + split_url[4]
        id_number = split_url[-1].split('=')[1]
        formatted_id = org_header + '-' + id_number
        return formatted_id

    def scrape_new_events(self):
        """
        Scrapes all events from HKS main events page
        """
        with requests.Session() as session:
            # get soup of page
            session.post(self.base_url, self.payload)
            main_events_page = session.get(self.events_url)
            main_event_soup = BeautifulSoup(main_events_page.text, 'html.parser')

            # extract table with all events
            main_events_table = main_event_soup.find("div", {"id": "WebPartWPQ7"})

            # get links to all events
            raw_links = [a['href'] for a in main_events_table.findAll("a")]
            links = {self.create_event_source_id(link): link for link in raw_links}

            # get data for each event in the link
            for link_id in links:
                event_page = session.get(links[link_id])
                event_soup = BeautifulSoup(event_page.text, 'html.parser')
                event_info = self.parse_event_data(event_soup)
                event_info['source_id'] = link_id
                self.events_to_add.append(event_info)
