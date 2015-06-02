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

"""This module supports acessing TERRAI data."""
import math
import arrow

from gfw.forestchange.common import CartoDbExecutor
from gfw.forestchange.common import Sql

class TerraiSql(Sql):

    WORLD = """
        SELECT 
            COUNT(f.*) AS value,
            DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) as date
            {additional_select}
        FROM terra_i_decrease f
        WHERE DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) >= '{begin}'::date
              AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) <= '{end}'::date
              AND ST_INTERSECTS(
                ST_SetSRID(
                  ST_GeomFromGeoJSON('{geojson}'), 4326), f.the_geom)
        GROUP BY f.grid_code"""

    ISO = """
        SELECT 
            COUNT(f.*) AS value,
            DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) as date
            {additional_select}
        FROM terra_i_decrease f
        WHERE iso = UPPER('{iso}')
            AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) >= '{begin}'::date
            AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) <= '{end}'::date
        GROUP BY f.grid_code"""

    ID1 = """
        SELECT 
            COUNT(f.*) AS value,
            DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) as date
            {additional_select}
        FROM terra_i_decrease f,
            (SELECT * FROM gadm2_provinces_simple
             WHERE iso = UPPER('{iso}') AND id_1 = {id1}) as p
        WHERE ST_Intersects(f.the_geom, p.the_geom)
            AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) >= '{begin}'::date
            AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) <= '{end}'::date
        GROUP BY f.grid_code"""

    WDPA = """
        SELECT 
            COUNT(f.*) AS value,
            DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) as date
        FROM terra_i_decrease f, (SELECT * FROM wdpa_all WHERE wdpaid={wdpaid}) AS p
        WHERE ST_Intersects(f.the_geom, p.the_geom)
              AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) >= '{begin}'::date
              AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) <= '{end}'::date
        GROUP BY f.grid_code"""

    USE = """
        SELECT 
            COUNT(f.*) AS value,
            DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) as date
        FROM {use_table} u, terra_i_decrease f
        WHERE u.cartodb_id = {pid}
              AND ST_Intersects(f.the_geom, u.the_geom)
              AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) >= '{begin}'::date
              AND DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 ) <= '{end}'::date
        GROUP BY f.grid_code"""

    LATEST = """
        SELECT DISTINCT
            grid_code,
            (DATE ((2004+FLOOR((grid_code-1)/23))::text || '-01-01') +  (MOD(grid_code,23)*16 )) as date
        FROM terra_i_decrease 
        WHERE grid_code IS NOT NULL
        GROUP BY grid_code
        ORDER BY grid_code DESC
        LIMIT {limit}"""

    @classmethod
    def download(cls, sql):
        return ' '.join(
            sql.replace("SELECT COUNT(f.*) AS value", "SELECT f.*").split())


def _processResults(action, data):
    if 'rows' in data:
        results = data.pop('rows')
        result = results[0]
        if not result.get('value'):
            data['results'] = results
    else:
        result = dict(value=None)
    data['value'] = result.get('value')
    data['min_date'] = _gridCodeToDate(result.get('min_grid_code'))
    data['max_date'] = _gridCodeToDate(result.get('max_grid_code'))
    return action, data

def _gridCodeToDate(grid_code):
    if grid_code:
        year = 2004 + math.floor((grid_code-1)/23)
        first_of_year = arrow.get(('%s-01-01' % year))
        periods = math.fmod(grid_code,23) * 16
        date = first_of_year.replace(days=+periods)
        return date.format('YYYY-MM-DD')
    else:
        return None

def _maxMinSelector(args):
    if args.get('alert_query'):
        return 'f.created_at'
    else: 
        return "DATE ((2004+FLOOR((f.grid_code-1)/23))::text || '-01-01') +  (MOD(f.grid_code,23)*16 )"

def execute(args):
    args['version'] = 'v2'
    args['max_min_selector'] = _maxMinSelector(args)
    action, data = CartoDbExecutor.execute(args, TerraiSql)
    if action == 'redirect' or action == 'error':
        return action, data
    return _processResults(action, data)
