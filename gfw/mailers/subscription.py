# Global Forest Watch API
# Copyright (C) 2015 World Resource Institute
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

import copy
import json
import datetime
import logging

from appengine_config import runtime_config

from gfw.common import gfw_url
from gfw.models.topic import Topic

from sparkpost import SparkPost
sparkpost = SparkPost(runtime_config.get('sparkpost_api_key'))

def summary_for_topic(topic):
    meta = topic.metadata
    lower_first = func = lambda s: s[:1].lower() + s[1:] if s else ''
    return meta['description'] + " at a " + meta['resolution'] + " resolution."  \
            " Coverage of " + meta['coverage'] + \
            ". Source is " + meta['source'] + \
            ". Available data from " + meta['timescale'] + ", updated " + \
            lower_first(meta['updates'])

class SubscriptionMailer:
    def __init__(self, subscription):
        self.subscription = subscription
        self.topic = Topic.get_by_id(subscription.topic)

    def send_for_event(self, event):
        topic_result = self.subscription.run_analysis(event.begin, event.end)

        if topic_result.is_zero() == False:
            topic = Topic.get_by_id(event.topic)

            subscriptions_url = gfw_url('my_gfw/subscriptions', {})
            unsubscribe_url = '%s/v2/subscriptions/%s/unsubscribe' % \
                (runtime_config['APP_BASE_URL'], str(self.subscription.key.id()))
            begin = event.begin.strftime('%d %b %Y')
            end = event.end.strftime('%d %b %Y')

            email = self.subscription.email
            user_profile = self.subscription.user_id.get().get_profile()
            name = getattr(user_profile, 'name', email)

            response = sparkpost.transmissions.send(
                recipients=[{'address': { 'email': email, 'name': name }}],
                template='forest-change-notification',
                substitution_data={
                    'selected_area': topic_result.area_name(),
                    'alert_count': topic_result.formatted_value(),
                    'alert_type': topic.description,
                    'alert_date': begin + " to " + end,
                    'alert_summary': summary_for_topic(topic),
                    'alert_name': self.subscription.formatted_name(),
                    'alert_link': self.subscription.url,
                    'unsubscribe_url': unsubscribe_url,
                    'subscriptions_url': subscriptions_url
                }
            )

            logging.info("Send Subscription Email Result: %s" % response)
