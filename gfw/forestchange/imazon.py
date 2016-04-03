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

"""This module supports acessing IMAZON data."""

from gfw.forestchange.common import CartoDbExecutor
from gfw.forestchange.common import Sql


class ImazonSql(Sql):

    WORLD = """
        WITH poly AS (SELECT * FROM ST_SetSRID(ST_GeomFromGeoJSON('{geojson}'), 4326) geojson)
        SELECT data_type,
            SUM(ST_Area(ST_Intersection(ST_Transform(poly.geojson, 3857), i.the_geom_webmercator))/(100*100)) AS value
            {additional_select}
        FROM imazon_sad i, poly
        WHERE i.date >= '{begin}'::date
            AND i.date <= '{end}'::date
        GROUP BY data_type"""

    # ISO same as WORLD since imazon only in Brazil

    ISO = """
        SELECT data_type,
            sum(ST_Area(i.the_geom_webmercator)/(100*100)) AS value
            {additional_select}
        FROM imazon_sad i
        WHERE i.date >= '{begin}'::date
            AND i.date <= '{end}'::date
        GROUP BY data_type"""

    ID1 = """
        SELECT data_type,
            SUM(ST_Area(ST_Intersection(
                i.the_geom_webmercator,
                p.the_geom_webmercator))/(100*100)) AS value
            {additional_select}
        FROM imazon_sad i,
            (SELECT *
                FROM gadm2_provinces_simple
                WHERE iso = UPPER('{iso}') AND id_1 = {id1}) as p
        WHERE i.date >= '{begin}'::date
            AND i.date <= '{end}'::date
        GROUP BY data_type"""

    WDPA = """
        SELECT data_type,
            SUM(ST_Area(ST_Intersection(
                i.the_geom_webmercator,
                p.the_geom_webmercator))/(100*100)) AS value
            {additional_select}
        FROM (SELECT CASE when marine::numeric = 2 then null
        when ST_NPoints(the_geom_webmercator)<=18000 THEN the_geom_webmercator
       WHEN ST_NPoints(the_geom_webmercator) BETWEEN 18000 AND 50000 THEN ST_RemoveRepeatedPoints(the_geom_webmercator, 100)
      ELSE ST_RemoveRepeatedPoints(the_geom_webmercator, 1000)
       END as the_geom_webmercator FROM wdpa_protected_areas where wdpaid={wdpaid}) p,
            imazon_sad i
        WHERE i.date >= '{begin}'::date
            AND i.date <= '{end}'::date
        GROUP BY data_type"""

    USE = """
        SELECT data_type,
            SUM(ST_Area(ST_Intersection(
                i.the_geom_webmercator,
                p.the_geom_webmercator))/(100*100)) AS value
            {additional_select}
        FROM {use_table} p, imazon_sad i
        WHERE p.cartodb_id = {pid}
            AND i.date >= '{begin}'::date
            AND i.date <= '{end}'::date
        GROUP BY data_type"""


    LATEST = """
        SELECT DISTINCT date
        FROM imazon_sad
        WHERE date IS NOT NULL
        ORDER BY date DESC
        LIMIT {limit}"""

    @classmethod
    def download(cls, sql):
        download_sql = sql.replace(ImazonSql.MIN_MAX_DATE_SQL, "")
        download_sql = sql.replace('SELECT data_type,', 'SELECT i.data_type, i.the_geom,')
        download_sql = download_sql.replace('GROUP BY data_type', 'GROUP BY i.data_type, i.the_geom')
        query = ' '.join(download_sql.split())
        return query


NO_DATA = [dict(disturbance='defor', value=None),
           dict(disturbance='degrad', value=None)]


def _processResults(action, data, args):

    # Only have data for Brazil
    if 'iso' in args and args['iso'].lower() != 'bra':
        result = NO_DATA
    elif 'rows' in data:
        result = data.pop('rows')
    else:
        result = NO_DATA

    data['value'] = result

    return action, data


def execute(args):
    if 'begin' in args:
        args['begin'] = args['begin'].strftime('%Y-%m-%d')
    if 'end' in args:
        args['end'] = args['end'].strftime('%Y-%m-%d')

    action, data = CartoDbExecutor.execute(args, ImazonSql)
    if action == 'redirect' or action == 'error':
        return action, data
    return _processResults(action, data, args)
