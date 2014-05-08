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

"""This module provides functions for dealing with FORMA data."""

import json

from gfw import cdb
from gfw import sql


META = {
    "description": "Alerts where forest disturbances have likely occurred.",
    "resolution": "500 x 500 meters",
    "coverage": "Humid tropical forest biome",
    "timescale": "January 2006 to present",
    "updates": "16 day",
    "source": "MODIS",
    "units": "Alerts",
    "name": "FORMA"
}


def _query_args(params):
    """Return prepared query args from supplied API params."""
    args = {}
    filters = []
    if 'geojson' in params:
        filters.append("""ST_INTERSECTS(ST_SetSRID(
            ST_GeomFromGeoJSON('%s'),4326),the_geom)""" % params['geojson'])
    if 'iso' in params:
        filters.append("iso = upper('%s')" % params['iso'])
    if 'id1' in params:
        filters.append("id_1 = '%s'" % params['id1'])
    if 'begin' in params:
        filters.append("date >= '%s'" % params['begin'])
    if 'end' in params:
        filters.append("date <= '%s'" % params['end'])
    args['where'] = ' AND '.join(filters)
    if args['where']:
        args['where'] = ' WHERE ' + args['where']
    return args


def _query_response(response, params):
    """Return world response."""
    if response.status_code == 200:
        result = json.loads(response.content)['rows'][0]
        result.update(META)
        result.update(params)
        if 'geojson' in params:
            result['geojson'] = json.loads(params['geojson'])
        return result
    else:
        raise Exception(response.content)


def _download_args(params):
    args = _query_args(params)
    fmt = params.get('format')
    if fmt != 'csv':
        args['select'] = ', the_geom'
    else:
        args['select'] = ''
    args['format'] = fmt
    return args


def query(**params):
    """Query FORMA with supplied params and return result."""
    args = _query_args(params)
    query = sql.FORMA_ANALYSIS.format(**args)
    response = cdb.execute(query)
    return _query_response(response, params)


def download(**params):
    """Return CartoDB download URL for supplied params."""
    args = _download_args(params)
    query = sql.FORMA_DOWNLOAD.format(**args)
    download_args = dict(format=params['format'])
    if 'filename' in params:
        download_args['filename'] = params['filename']
    return cdb.get_url(query, download_args)
