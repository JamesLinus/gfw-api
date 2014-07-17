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

from google.appengine.ext import testbed

from gfw.forestchange import fires
from gfw.forestchange import common


class BaseTest(unittest.TestCase):

    def setUp(self):
        self.testbed = testbed.Testbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_urlfetch_stub()
        self.mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)

    def tearDown(self):
        self.testbed.deactivate()


class FiresTest(BaseTest):

    def testNationalSql(self):
        sql = fires.FiresSql.process(
            {'iso': 'idn', 'begin': '2001', 'end': '2002'})
        self.assertTrue("iso = UPPER('idn')" in sql)
        self.assertTrue("acq_date::date >= '2001'::date" in sql)
        self.assertTrue("acq_date::date <= '2002'::date" in sql)

    def testSubnationalSql(self):
        config = {'iso': 'bra', 'id1': '1', 'begin': '2001', 'end': '2002'}
        sql = fires.FiresSql.process(config)
        print sql
        self.assertTrue("iso = UPPER('bra')" in sql)
        self.assertTrue("id_1 = 1" in sql)
        self.assertTrue("acq_date::date >= '2001'::date" in sql)
        self.assertTrue("acq_date::date <= '2002'::date" in sql)

    def testExecuteNational(self):
        # valid iso
        config = {'iso': 'idn', 'begin': '2001-01-01', 'end': '2015-01-01'}
        sql = fires.FiresSql.process(config)
        print sql
        action, data = fires.execute(config)
        self.assertEqual(action, 'respond')
        self.assertIn('value', data)
        print data

        # invalid iso
        action, data = fires.execute(
            {'iso': 'FOO', 'begin': '2001-01-01', 'end': '2014-01-01'})
        self.assertEqual(action, 'respond')
        self.assertIn('value', data)
        self.assertEqual(data['value'], None)

        # no iso
        self.assertRaises(Exception, fires.execute, {})

    def testExecuteSubNational(self):
        # valid iso
        config = {'iso': 'idn', 'id1': 1, 'begin': '2001-01-01',
                  'end': '2015-01-01'}
        sql = fires.FiresSql.process(config)
        print sql
        action, data = fires.execute(config)
        self.assertEqual(action, 'respond')
        self.assertIn('value', data)
        print data

        # invalid iso
        action, data = fires.execute(
            {'iso': 'FOO', 'begin': '2001-01-01', 'end': '2014-01-01'})
        self.assertEqual(action, 'respond')
        self.assertIn('value', data)
        self.assertEqual(data['value'], None)

        # no iso
        self.assertRaises(Exception, fires.execute, {})

if __name__ == '__main__':
    reload(common)
    reload(fires)
    unittest.main(verbosity=2, exit=False)
