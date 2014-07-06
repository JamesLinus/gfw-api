# Global Forest Watch API
# Copyright (C) 2014 World Resource Institute
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

"""Unit test coverage for the gfw.forestchange.forma module."""

import unittest

from test.forestchange.common import BaseTest

from gfw.forestchange import forma
from gfw.forestchange.forma import FormaSql
from gfw.forestchange.forma import execute
from gfw.forestchange import common


class FormaSqlTest(BaseTest):

    """Test FORMA SQL for national, subnational, concessions, and protected
    areas by executing queries for all combinations of args via direct
    requests to CartoDB.
    """

    def testNational(self):
        print 'hi'
        args = [
            ('begin', '2010-01-01'),
            ('end', '2014-01-01')]
        for args in self.combos(args):
            args = dict(args)
            args['iso'] = 'idn'
            sql = FormaSql.process(args)
            url = self.getCdbUrl(sql)
            print sql
            response = self.fetch(url)
            self.assertEqual(200, response.status_code)
            self.assertIsNot(None, response.json()['rows'])
            self.assertIsNot(None, 'value' in response.json()['rows'][0])


# class FormaExecuteTest(BaseTest):

#     def testExecuteNational(self):
#         # valid iso
#         action, data = execute(
#             {'iso': 'bra', 'begin': '2001-01-01', 'end': '2014-01-01'})
#         self.assertEqual(action, 'respond')
#         self.assertIn('value', data)
#         self.assertIsNot(data['value'], None)

#         # invalid iso
#         action, data = execute(
#             {'iso': 'FOO', 'begin': '2001-01-01', 'end': '2014-01-01'})
#         self.assertEqual(action, 'respond')
#         self.assertIn('value', data)
#         self.assertEqual(data['value'], None)

#         # no iso
#         self.assertRaises(Exception, execute, {})

if __name__ == '__main__':
    reload(common)
    reload(forma)
    unittest.main(verbosity=2, exit=False)
