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

import json
import webapp2
import monitor
import datetime

from appengine_config import runtime_config
from google.appengine.ext import ndb
from google.appengine.api import mail
from google.appengine.api import taskqueue
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
import logging
import re
from google.appengine.api import users

#
# Model
#
class Notification(ndb.Model):
    """Key = subscription+event"""
    topic = ndb.StringProperty()
    params = ndb.JsonProperty()  # subscription+event JSON
    sent = ndb.BooleanProperty(default=False)
    created = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def get(cls, event, subscription):
        return cls.get_by_id('%s+%s' % (event.key.id(), subscription.key.id()))

    @classmethod
    def create(cls, event, subscription):
        id = '%s+%s' % (event.key.id(), subscription.key.id())
        return cls(
            id=id,
            topic=event.topic,
            params=dict(event=event.params, subscription=subscription.params))

