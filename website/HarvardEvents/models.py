from flask_login import UserMixin
import datetime
from HarvardEvents import db


class Event(db.Model):
    __tablename__ = 'events'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    title = db.Column(db.String(256), nullable=False)
    short_description = db.Column(db.Text)
    speaker = db.Column(db.String(256))
    sponsor = db.Column(db.String(256))
    co_sponsor = db.Column(db.String(256))
    additional_sponsor = db.Column(db.String(256))
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    event_type = db.Column(db.String(256))
    location = db.Column(db.String(256))
    description = db.Column(db.Text)
    intranet_homepage = db.Column(db.Boolean)
    public_site = db.Column(db.Boolean)
    hks_today_email = db.Column(db.Boolean)
    ticketed_event = db.Column(db.Boolean)
    ticketed_event_instructions = db.Column(db.String(256))
    ad_day_one = db.Column(db.Date)
    ad_day_two = db.Column(db.Date)
    contact_name = db.Column(db.String(256))
    contact_email = db.Column(db.String(256))
    phone_number = db.Column(db.String(15))
    rsvp_required = db.Column(db.Boolean)
    rsvp_date = db.Column(db.Date)
    rsvp_email_url = db.Column(db.String(256))
    existing_website = db.Column(db.String(256))
    policy_topics = db.Column(db.String(256))
    academic_areas = db.Column(db.String(256))
    geographic_regions = db.Column(db.String(256))
    degrees_programs = db.Column(db.String(256))
    centers_initiatives = db.Column(db.String(256))
    key_terms = db.Column(db.String(256))
    source = db.Column(db.Enum('hks', 'user'), nullable=False)
    source_id = db.Column(db.String(256), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.datetime.today())

    @property
    def get_tile_data(self):
        return {
            'event_id': self.id,
            'title': self.title,
            'timing': '{0} - {1} ({2} mins)'.format(self.start_time.strftime('%I: %M %p'),
                                                    self.end_time.strftime('%I: %M %p'),
                                                    int((self.end_time - self.start_time).seconds / 60)),
            'location': self.location,
            'rsvp_required': ((self.rsvp_email_url.replace(' ', '') if self.rsvp_email_url else 'Yes')
                              if self.rsvp_required else 'No'),
            'description': self.description,
            'contact_name': self.contact_name,
            'contact_email': self.contact_email,
            'ticketed_event_instructions': self.ticketed_event_instructions,
            'rsvp_date': (self.rsvp_date.strftime('%a %b %d') if self.rsvp_date else None),
            'date': self.start_time.strftime('%a %b %d'),
        }

    @property
    def google_calendar_event(self):
        return {
            'summary': self.title,
            'location': self.location,
            'description': self.description,
            'start': {
                'dateTime': self.start_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/New_York',
            },
            'end': {
                'dateTime': self.end_time.strftime('%Y-%m-%dT%H:%M:%S'),
                'timeZone': 'America/New_York',
            },
        }

    @property
    def add_event_object(self):
        return {'type': 'edit',
                'info': {
                    'id': self.id,
                    'title': self.title,
                    'date': self.start_time.strftime('%Y-%m-%d'),
                    'start_time': self.start_time.strftime('%H:%M:%S'),
                    'end_time': self.end_time.strftime('%H:%M:%S'),
                    'location': self.location,
                    'description': self.description,
                    'rsvp_date': self.rsvp_date,
                    'rsvp_email_url': self.rsvp_email_url,
                    'ticketed_event_instructions': self.ticketed_event_instructions,
                    'contact_name': self.contact_name,
                    'contact_email': self.contact_email,
                    'source_id': self.source_id,
                }
                }

    @property
    def to_csv(self):
        title = self.title.replace('"', "'") if self.title is not None else None
        short_description = self.short_description.replace('"', "'") if self.short_description is not None else None
        speaker = self.speaker.replace('"', "'") if self.speaker is not None else None
        description = self.description.replace('"', "'") if self.description is not None else None
        ticketed_event_instructions = (self.ticketed_event_instructions.replace('"', "'")
                                       if self.ticketed_event_instructions is not None else None)
        return '{0.id},"{1}","{2}","{3}","{0.sponsor}","{0.co_sponsor}","{0.additional_sponsor}",'\
               '{0.start_time},{0.end_time},{0.event_type},"{0.location}","{4}",{0.intranet_homepage},{0.public_site},{0.hks_today_email},'\
               '{0.ticketed_event},"{5}",{0.ad_day_one},{0.ad_day_two},"{0.contact_name}",{0.contact_email},{0.phone_number},'\
               '{0.rsvp_required},{0.rsvp_date},{0.rsvp_email_url},"{0.existing_website}","{0.policy_topics}","{0.academic_areas}","{0.geographic_regions}",'\
               '"{0.degrees_programs}","{0.centers_initiatives}","{0.key_terms}",{0.source},{0.source_id},{0.date_added}\n'.format(self, title, short_description, speaker, description, ticketed_event_instructions)


class EventSelection(db.Model):
    __tablename__ = 'selected_events'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    date_selected = db.Column(db.DateTime, default=datetime.datetime.today())
    selection_type = db.Column(db.Enum('calendar', 'link'), nullable=False)
    selection_source = db.Column(db.Enum('site', 'recommended', 'popular', 'weekly_email', 'newevent_email'),
                                 nullable=False)

    @property
    def to_csv(self):
        return '{0.id},{0.user_id},{0.event_id},{0.date_selected},{0.selection_type},{0.selection_source}\n'.format(self)


class Search(db.Model):
    __tablename__ = 'searches'

    id = db.Column(db.Integer, primary_key=True, nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id'), nullable=False)
    date_searched = db.Column(db.DateTime, default=datetime.datetime.today())
    search = db.Column(db.Text)


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.String(50), primary_key=True, nullable=False)
    email = db.Column(db.String(256), unique=True, nullable=False)
    daily_subscribed = db.Column(db.Boolean, default=True)
    recommendation_subscribed = db.Column(db.Boolean, default=True)
    newevents_subscribed = db.Column(db.Boolean, default=True)
    token = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.today())
    user_type = db.Column(db.Enum('user', 'admin'), default='user')

    @property
    def to_csv(self):
        return '{0.id},{0.created_at}\n'.format(self)
