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

import json
import webapp2
import logging

from appengine_config import runtime_config

from google.appengine.api import mail
from google.appengine.api import taskqueue


def log(url, msg, error=None, headers={}):
    headers = dict([(k, v) for k, v in headers.iteritems()])
    params = dict(url=url, msg=msg, headers=json.dumps(headers))
    params['error'] = error
    taskqueue.add(url='/monitor', params=params, queue_name="log")


class Monitor(webapp2.RequestHandler):
    def post(self):
        params = ['url', 'msg', 'error', 'headers']
        url, msg, error, headers = map(self.request.get, params)
        headers = json.loads(headers)
        loc = headers.get('X-Appengine-Citylatlong', '0,0')
        vals = dict(
            url=url,
            msg=msg.replace("'", ''),
            country=headers.get('X-Appengine-Country'),
            region=headers.get('X-Appengine-Region'),
            city=headers.get('X-Appengine-City'),
            loc=loc,
            headers=headers)
        vals = json.dumps(vals, sort_keys=True, indent=4,
                          separators=(',', ': '))
        if error:
            logging.error('MONITOR: %s' % error)
            mail.send_mail(
                sender='noreply@gfw-apis.appspotmail.com',
                to='eightysteele+gfw-api-errors@gmail.com',
                subject='[GFW API ERROR] %s' % msg,
                body='Error: %s\n\n%s' % (error, vals))
        else:
            logging.info('MONITOR: %s' % vals)


routes = [webapp2.Route(r'/monitor', handler=Monitor, methods=['POST'])]
handlers = webapp2.WSGIApplication(routes, debug=runtime_config.get('IS_DEV'))
