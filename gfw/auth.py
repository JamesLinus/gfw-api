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

"""This module contains request handlers for user authentication."""

import webapp2
import monitor
from gfw import common
from gfw.common import CORSRequestHandler
from engineauth import models
from engineauth.models import User
from engineauth.models import UserProfile

config = {
    'webapp2_extras.sessions': {
        'secret_key': 'wIDjEesObzp5nonpRHDzSp40aba7STuqC6ZRY'
    }
}


class UserApi(CORSRequestHandler):
    """Handler for user info."""

    def get(self):
        try:
            # TODO: get cookie out, look up session
            value = self.request.cookies.get('_eauth')
            if value:
                session = models.Session.get_by_value(value)

            self.user = User.get_by_id(int(session.user_id))
            self.profile = UserProfile.get_by_id(self.user.auth_ids[-1])
            name = self.profile.user_info['info']['displayName']
            username = self.profile.user_info['info']['nickname']

            self.complete('respond', {'name': name, 'email': self.user.email, 'username': username})

        except Exception, e:
            name = e.__class__.__name__
            msg = 'Error: Users API (%s)' % name
            monitor.log(self.request.url, msg, error=e,
                        headers=self.request.headers)

routes = [webapp2.Route(r'/user/session', handler=UserApi,
          handler_method='get',
          methods=['GET'])]


handlers = webapp2.WSGIApplication(routes, debug=common.IS_DEV)
