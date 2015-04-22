
import copy
import json

from gfw import cdb

def date_column(args):
    if args.get('alert_query'):
        return 'created_at'
    else:
        return 'date'

def classify_query(args):
    if 'iso' in args and not 'id1' in args:
        return 'iso'
    elif 'iso' in args and 'id1' in args:
        return 'id1'
    elif 'ifl' in args:
        return 'ifl'
    elif 'ifl_id1' in args:
        return 'ifl_id1'
    elif 'use' in args:
        return 'use'
    elif 'pa' in args:
        return 'pa'
    elif 'wdpaid' in args:
        return 'wdpa'
    else:
        return 'world'


class SqlError(ValueError):
    def __init__(self, msg):
        super(SqlError, self).__init__(msg)


class Sql(object):

    @classmethod
    def get_query_type(cls, params, args, the_geom_table=''):
        """Return query type (download or analysis) with updated params."""
        query_type = 'analysis'
        if 'format' in args:
            query_type = 'download'
            if args['format'] != 'csv':
                the_geom = ', the_geom' \
                    if not the_geom_table \
                    else ', %s.the_geom' % the_geom_table
                params['the_geom'] = the_geom
        return query_type, params

    @classmethod
    def clean(cls, sql):
        """Return sql with extra whitespace removed."""
        return ' '.join(sql.split())

    @classmethod
    def process(cls, args):
        begin = args['begin'] if 'begin' in args else '2014-01-01'
        end = args['end'] if 'end' in args else '2015-01-01'
        params = dict(begin=begin, end=end, geojson='', the_geom='')
        classification = classify_query(args)
        if hasattr(cls, classification):
            return map(cls.clean, getattr(cls, classification)(params, args))

    @classmethod
    def world(cls, params, args):
        params['date_column'] = date_column(args)
        params['geojson'] = args['geojson']
        query_type, params = cls.get_query_type(params, args)
        query = cls.WORLD.format(**params)        
        download_query = cls.download(cls.WORLD.format(**params))
        return query, download_query

    @classmethod
    def iso(cls, params, args):
        params['date_column'] = date_column(args)        
        params['iso'] = args['iso']
        query_type, params = cls.get_query_type(params, args)
        query = cls.ISO.format(**params)
        download_query = cls.download(cls.ISO.format(**params))
        return query, download_query

    @classmethod
    def id1(cls, params, args):        
        params['iso'] = args['iso']
        params['id1'] = args['id1']
        query_type, params = cls.get_query_type(params, args)
        query = cls.ID1.format(**params)
        download_query = cls.download(cls.ID1.format(**params))
        return query, download_query

    @classmethod
    def wdpa(cls, params, args):
        params['wdpaid'] = args['wdpaid']
        query_type, params = cls.get_query_type(params, args)
        query = cls.WDPA.format(**params)
        download_query = cls.download(cls.WDPA.format(**params))
        return query, download_query

    @classmethod
    def use(cls, params, args):
        concessions = {
            'mining': 'gfw_mining',
            'oilpalm': 'gfw_oil_palm',
            'fiber': 'gfw_wood_fiber',
            'logging': 'gfw_logging'
        }
        params['use_table'] = concessions.get(args['use']) or args['use']
        params['pid'] = args['useid']
        query_type, params = cls.get_query_type(params, args)
        query = cls.USE.format(**params)
        download_query = cls.download(cls.USE.format(**params))
        return query, download_query


def get_download_urls(query, params):
    urls = {}
    args = copy.copy(params)
    for fmt in ['csv', 'geojson', 'svg', 'kml', 'shp']:
        args['format'] = fmt
        urls[fmt] = cdb.get_url(query, args)
    return urls


class CartoDbExecutor():

    @classmethod
    def _query_response(cls, response, params, query):
        """Return world response."""
        result = {}

        if response.status_code == 200:
            rows = json.loads(response.content)['rows']
            if rows:
                result['rows'] = rows
        else:
            result['error'] = 'CartoDB Error: %s' % response.content

        result['params'] = params
        if 'geojson' in params:
            result['params']['geojson'] = json.loads(params['geojson'])
        if 'dev' in params:
            result['dev'] = {'sql': query}

        return result

    @classmethod
    def execute(cls, args, sql):
        try:
            query, download_query = sql.process(args)
            download_url = cdb.get_url(download_query, args)
            if 'format' in args:
                return 'redirect', download_url
            else:
                action, response = 'respond', cdb.execute(query)
                response = cls._query_response(response, args, query)
                response['download_urls'] = get_download_urls(
                    download_query, args)
                if 'error' in response:
                    action = 'error'
                return action, response
        except Exception, e:
            return 'execute() error', e
