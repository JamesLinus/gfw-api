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

"""This module supports acessing FORMA data."""

from gfw.forestchange.common import CartoDbExecutor
from gfw.forestchange.common import Sql


class FormaSql(Sql):

    ISO = """
        SELECT t.iso, count(t.*) AS value
        FROM forma_api t
        WHERE date >= '{begin}'::date
              AND date <= '{end}'::date
              AND iso = UPPER('{iso}')
        GROUP BY t.iso"""

    ID1 = """
        SELECT g.id_1 AS id1, count(*) AS value
        FROM forma_api t
        INNER JOIN (
            SELECT *
            FROM gadm2
            WHERE id_1 = {id1}
                  AND iso = UPPER('{iso}')) g
            ON t.gadm2::int = g.objectid
        WHERE t.date >= '{begin}'::date
              AND t.date <= '{end}'::date
        GROUP BY id1
        ORDER BY id1"""

    @classmethod
    def iso(cls, params, args):
        params['iso'] = args['iso']
        query_type, params = cls.get_query_type(params, args)
        if query_type == 'download':
            return cls.ISO.format(**params)
        else:
            return cls.ISO.format(**params)

    @classmethod
    def id1(cls, params, args):
        params['iso'] = args['iso']
        params['id1'] = args['id1']
        query_type, params = cls.get_query_type(params, args)
        if query_type == 'download':
            return cls.ID1.format(**params)
        else:
            return cls.ID1.format(**params)


def _processResults(action, data):
    if data['rows']:
        result = data['rows'][0]
        data.pop('rows')
    else:
        result = dict(value=0)

    data['value'] = result['value']

    return action, data


def execute(args):
    action, data = CartoDbExecutor.execute(args, FormaSql)
    return _processResults(action, data)
