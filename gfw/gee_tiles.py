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

"""This module contains request handlers for serving GEE tiles and was
written by @andrewxhill."""

import os
import ee
import time
import math
import webapp2
import jinja2
import json
from oauth2client.appengine import AppAssertionCredentials
from google.appengine.api import memcache
from google.appengine.api import urlfetch
import config
import logging
from google.appengine.ext import ndb


class TileEntry(ndb.Model):
    value = ndb.BlobProperty()


jinja_environment = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

#Global variables
EE_URL = 'https://earthengine.googleapis.com'

# The OAuth scope URL for the Google Earth Engine API.
GEE_SCOPE = 'https://www.googleapis.com/auth/earthengine.readonly'
SCOPES = (GEE_SCOPE)
credentials = AppAssertionCredentials(scope=SCOPES)


class MainPage(webapp2.RequestHandler):
    def get(self):

      ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
      mapid = ee.Image('srtm90_v4').getMapId({'min':0, 'max':1000})


      template_values = {
          'mapid' : mapid['mapid'],
          'token' : mapid['token']
          }
      template = jinja_environment.get_template('index.html')
      self.response.out.write(template.render(template_values))


class MapInit():
  def __init__(self,reqid, request):

      if reqid == 'landsat_composites':
        year = request.get("year")
        key = reqid + year
      else:
        key = reqid

      self.mapid = memcache.get(key)
      if self.mapid is None:
        
        retry_count = 0
        max_retries = 5
        n = 1

        auth = False

        while retry_count < max_retries:
          try:
            ee.Initialize(config.EE_CREDENTIALS, config.EE_URL)
            auth = True
            break
          except:
            logging.info('RETRY AUTHENTICATION')
            retry_count += 1
            time.sleep(math.pow(2, n - 1))
            n += 1
            if auth:
              break

        if not auth or (retry_count == max_retries):
          return

        retry_count = 0
        max_retries = 5
        n = 1

        while retry_count < max_retries:
          try:
            if reqid == 'landsat_composites':
              # landsat (L7) composites
              # accepts a year, side effect map display of annual L7 cloud free composite
              landSat = ee.Image("L7_TOA_1YEAR/" + year).select("30","20","10")
              self.mapid = landSat.getMapId({
                'min':1, 
                'max':100, 
                'gamma':2.0
              })

            if reqid == 'l7_toa_1year_2012':
              self.mapid = ee.Image("L7_TOA_1YEAR_2012").getMapId({
                'opacity': 1, 
                'bands':'30,20,10', 
                'min':10, 
                'max':120, 
                'gamma':2.0
              })

            if reqid == 'simple_green_coverage':
              # The Green Forest Coverage background created by Andrew Hill
              # example here: http://ee-api.appspot.com/#331746de9233cf1ee6a4afd043b1dd8f
              treeHeight = ee.Image("Simard_Pinto_3DGlobalVeg_JGR")
              elev = ee.Image('srtm90_v4')
              mask2 = elev.gt(0).add(treeHeight.mask())
              water = ee.Image("MOD44W/MOD44W_005_2000_02_24").select(["water_mask"]).eq(0)
              self.mapid = treeHeight.mask(mask2).mask(water).getMapId({'opacity': 1, 'min':0, 'max':50, 'palette':"dddddd,1b9567,333333"})
              

            if reqid == 'simple_bw_coverage':
              # The Green Forest Coverage background created by Andrew Hill
              # example here: http://ee-api.appspot.com/#331746de9233cf1ee6a4afd043b1dd8f
              treeHeight = ee.Image("Simard_Pinto_3DGlobalVeg_JGR")
              elev = ee.Image('srtm90_v4')
              mask2 = elev.gt(0).add(treeHeight.mask())
              self.mapid = treeHeight.mask(mask2).getMapId({'opacity': 1, 'min':0, 'max':50, 'palette':"ffffff,777777,000000"})
            
            if reqid == 'masked_forest_carbon':
              forestCarbon = ee.Image("GME/images/06900458292272798243-10017894834323798527")
              self.mapid = forestCarbon.mask(forestCarbon).getMapId({'opacity': 0.5, 'min':1, 'max':200, 'palette':"FFFFD4,FED98E,FE9929,dd8653"})

            # update cache and datastore
            memcache.set(key, self.mapid, time=82800)  # 23 hours

            break
          except:
            logging.info('RETRY GET MAP ID %s' % reqid)
            retry_count += 1
            time.sleep(math.pow(2, n - 1))
            n += 1

# Depricated method, GFW will move to KeysGFW and not deliver tiles from the proxy directly
class TilesGFW(webapp2.RequestHandler):
    def get(self, m, z, x, y):
        year = self.request.get('year', '')
        key = "%s-tile-%s-%s-%s-%s" % (m, z, x, y, year)
        cached_image = memcache.get(key)

        if cached_image is None:
          # logging.info('MEMCACHE MISS %s' % key)
          entry = TileEntry.get_by_id(key)
          if entry:
            # logging.info('DATASTORE HIT %s' % key)
            cached_image = entry.value
            memcache.set(key, cached_image)
          else:
            # logging.info('DATASTORE MISS %s' % key)
            pass
        else:
          # logging.info('MEMCAHCE HIT %s' % key)
          pass


        if cached_image is None:
          mapid = MapInit(m.lower(), self.request).mapid
          if mapid is None:
            # TODO add better error code control
            self.error(503)
            return
          else:
            retry_count = 0
            max_retries = 5
            n = 1
            url="https://earthengine.googleapis.com/map/%s/%s/%s/%s?token=%s" % (mapid['mapid'], z, x, y, mapid['token'])

            while retry_count < max_retries:
              try:
                result = urlfetch.fetch(url, deadline=60)
                break
              except:
                logging.info('TILE RETRY %s' % url)
                retry_count += 1
                time.sleep(math.pow(2, n - 1))
                n += 1
          if not result or retry_count == max_retries:
            self.error(503)
            return

          if result.status_code == 200:
            memcache.set(key,result.content)
            TileEntry(id=key, value=result.content).put()
            self.response.headers["Content-Type"] = "image/png"
            self.response.headers.add_header("Expires", "Thu, 01 Dec 1994 16:00:00 GMT")
            self.response.out.write(result.content)
          elif result.status_code == 404:
            self.error(404)
            return
          else:
            self.response.set_status(result.status_code)
        else:
          # logging.info('CACHE HIT %s' % key)
          self.response.headers["Content-Type"] = "image/png"
          self.response.headers.add_header("Expires", "Thu, 01 Dec 1994 16:00:00 GMT")
          self.response.out.write(cached_image)


class KeysGFW(webapp2.RequestHandler):
    def get(self, m, year=None):

      mapid = MapInit(m.lower(), self.request).mapid

      if mapid is None:
        # TODO add better error code control
        self.error(404)
      else:
        self.response.headers['Content-Type'] = 'application/json'
        self.response.out.write(json.dumps({
            'mapid' : mapid['mapid'],
            'token' : mapid['token']
          }))


api = webapp2.WSGIApplication([ 
    ('/', MainPage), 
    ('/gee/([^/]+)/([^/]+)/([^/]+)/([^/]+).png', TilesGFW), 
    ('/gee/([^/]+)', KeysGFW)

  ], debug=True)


