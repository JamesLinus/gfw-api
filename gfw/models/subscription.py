# Global Forest Watch API
# Copyright (C) 2013 World Resource Institute
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module supports pubsub."""
import logging
import copy
import json

from appengine_config import runtime_config
from google.appengine.ext import ndb
from google.appengine.api import users

from gfw.admin.pubsub.mail_handlers import send_confirmation_email

from gfw.user.gfw_user import GFWUser
from gfw.models.topic import Topic

class Subscription(ndb.Model):
    name      = ndb.StringProperty()
    topic     = ndb.StringProperty()
    email     = ndb.StringProperty()
    url       = ndb.StringProperty()
    user_id   = ndb.KeyProperty()
    pa        = ndb.StringProperty()
    use       = ndb.StringProperty()
    useid     = ndb.IntegerProperty()
    iso       = ndb.StringProperty()
    id1       = ndb.StringProperty()
    ifl       = ndb.StringProperty()
    fl_id1    = ndb.StringProperty()
    wdpaid    = ndb.IntegerProperty()
    has_geom  = ndb.BooleanProperty(default=False)
    confirmed = ndb.BooleanProperty(default=False)
    geom      = ndb.JsonProperty()
    params    = ndb.JsonProperty()
    updates   = ndb.JsonProperty()
    created   = ndb.DateTimeProperty(auto_now_add=True)
    new       = ndb.BooleanProperty(default=True)

    kind = 'Subscription'

    """ Class Methods """

    @classmethod
    def create(cls, params, user=None):
        """Create subscription if email and, iso or geom is present"""

        subscription = Subscription()
        subscription.populate(**params)
        subscription.params = params
        subscription.has_geom = bool(params.get('geom'))

        user_id = user.key if user is not None else ndb.Key('User', None)
        subscription.user_id = user_id

        subscription.put()
        return subscription

    #
    #   Query Helpers
    #

    @classmethod
    def by_topic(cls, topic):
        """Return all confirmed Subscription entities for supplied topic."""
        return cls.query(cls.topic == topic, cls.confirmed == True).iter()

    @classmethod
    def with_token(cls, token):
        """Return subscription for a given token"""
        token_type = type(token)
        if (token_type is str) or (token_type is unicode):
            subscription = ndb.Key(urlsafe=token).get()
            if subscription.key.kind()==cls.kind:
                subscription = subscription
            else:
                subscription = False
        else:
            subscription = token.get()
        return subscription

    @classmethod
    def with_confirmation(cls):
        """Return all confirmed Subscription entities"""
        return cls.query(cls.confirmed == True).iter()

    @classmethod
    def without_confirmation(cls):
        """Return all unconfirmed Subscription entities"""
        return cls.query(cls.confirmed == True).iter()

    @classmethod
    def with_topic(cls, topic):
        """Return all confirmed Subscription entities for supplied topic."""
        return cls.query(cls.topic == topic, cls.confirmed == True).iter()

    @classmethod
    def with_email(cls, email):
        return cls.query(cls.email == email).iter()

    #
    # Subscriptions
    #

    @classmethod
    def subscribe(cls, params, user):
        subscription = Subscription.create(params, user)
        if subscription:
            subscription.send_confirmation_email()
            return subscription
        else:
            return False

    @classmethod
    def unsubscribe_by_token(cls, token):
        subscription = cls.with_token(token)
        if subscription:
            return subscription.unsubscribe()

    @classmethod
    def unsubscribe_all(cls, topic, email):
        subs = cls.query(cls.topic == topic, cls.email == email)
        for sub in subs:
            sub.unsubscribe()

    @classmethod
    def confirm_by_id(cls, id):
        subscription = cls.get_by_id(int(id))
        if subscription:
            return subscription.confirm()
        else:
            return False

    """ Instance Methods """

    def send_confirmation_email(cls):
        user_profile = cls.user_id.get().get_profile()

        name = None
        if hasattr(user_profile, 'name'):
            name = user_profile.name

        send_confirmation_email(cls.email, name, cls.key.urlsafe())

    def to_dict(self):
        result = super(Subscription,self).to_dict()
        result['key'] = self.key.id()
        return result
    #
    # Subscriptions
    #

    def name(self):
        return self.params.get('name') or "Unnamed Subscription"

    def confirm(self):
        self.confirmed = True
        return self.put()

    def unconfirm(self):
        self.confirmed = False
        self.send_confirmation_email()

        return self.put()

    def unsubscribe(self):
        return self.key.delete()

    def run_analysis(self, begin, end):
        params = copy.copy(self.params)
        params['begin'] = begin.strftime('%Y-%m-%d')
        params['end'] = end.strftime('%Y-%m-%d')

        if 'geom' in params:
            geom = params['geom']
            if 'geometry' in geom:
                geom = geom['geometry']
            params['geojson'] = json.dumps(geom)

        topic = Topic.get_by_id(self.topic)
        return topic.execute(params)
