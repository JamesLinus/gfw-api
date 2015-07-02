# -- launch shell
# remote_api_shell.py -s dev.gfw-apis.appspot.com\
# 
# ex:
#
# import gfw.console.pubsub as ps
# b = '2015-06-01'
# rpt = ps.report(b)
# print ps.report_summary(rpt)
# print ps.report_csv(rpt)
#

import json
import arrow

from google.appengine.ext import ndb

from gfw.pubsub.event import Event
from gfw.pubsub.notification import Notification
from gfw.pubsub.subscription import Subscription

#
# PUBLISHING
#

drb = "bguzder-williams@wri.org,bguzder.wri.org"
dra = "abarrett@wri.org,bguzder.wri.org"
dr8 = "asteele@wri.org,bguzder.wri.org"

def publish(**params):
    # Force DryRun unless explicitly False
    dry_run = params.get('dry_run')
    if (dry_run == None):
      dry_run = "bguzder-williams@wri.org,bguzder.wri.org"
    topic = params.get('topic')
    event = Event.publish(topic,params,dry_run)
    print "topic: %s, dry_run: %s, params: %s, event: %s" % (topic,dry_run,params,event)

#
# REPORTING
#
def report(begin=None,end=None):
  if not end:
    end = arrow.now().format('YYYY-MM-DD')
  rpt = {}
  confirmed = Subscription.query(Subscription.confirmed==True)
  unconfirmed = Subscription.query(ndb.OR(Subscription.confirmed==False,Subscription.confirmed==None))
  rpt['total'] = {
    'confirmed': confirmed.count(),
    'unconfirmed': unconfirmed.count()
  }
  def sub_tuple(sub):
    params=sub.params
    typ = params.get('iso','geojson')
    date = arrow.get(sub.created).format("YYYY-MM-DD")
    return (typ,date,sub.email)

  if begin:
    filtered_confirmed = filter_subscriptions(confirmed,begin,end)
    filtered_unconfirmed = filter_subscriptions(unconfirmed,begin,end)
    rpt['filtered'] = {
      'begin': begin,
      'end': end
    }
    rpt['filtered']['confirmed'] = {
      'count': filtered_confirmed.count(),
      'subscriptions': map(sub_tuple,filtered_confirmed)
    }
    rpt['filtered']['unconfirmed'] = {
      'count': filtered_unconfirmed.count(),
      'subscriptions': map(sub_tuple,filtered_unconfirmed)
    }
  return rpt

def report_summary(rpt):
  rpt_params = {
    'today': arrow.now().format('YYYY-MM-DD'),
    'begin':rpt['filtered']['begin'],
    'end':rpt['filtered']['end'],
    'confirmed_count':rpt['total']['confirmed'],
    'unconfirmed_count':rpt['total']['unconfirmed'],
    'filtered_confirmed_count':rpt['filtered']['confirmed']['count'],
    'filtered_unconfirmed_count':rpt['filtered']['unconfirmed']['count']
  }

  rpt_str = """
    Subscription API Report ({today})

    Totals:
      confirmed:{confirmed_count}
      unconfirmed: {unconfirmed_count}

    Filtered[{begin} to {end}]:
      confirmed: {filtered_confirmed_count}
      unconfirmed: {filtered_unconfirmed_count}
  """
  return rpt_str.format(**rpt_params)

def report_csv(rpt):
  csv = "iso-geojson,date,email\n"
  for sub in rpt['filtered']['confirmed']['subscriptions']:
    csv += "%s, %s, %s\n" % (sub)
  unconfirmed_subscriptions = ""
  for sub in rpt['filtered']['unconfirmed']['subscriptions']:
    csv += "%s, %s, %s\n" % (sub)
  return csv





#
# SUBSCRIBE 
#
def subscribe(**params):
  auto_confirm = params.pop('auto_confirm',False)
  token = Subscription.subscribe(params)
  if token and auto_confirm:
    confirm(token)
  return token

def confirm(token):
  return Subscription.confirm(token)

def unsubscribe(token):
  return Subscription.unsubscribe(token)

#
# INSPECT/RESET
#
def filter_subscriptions(subscriptions,begin=None,end=None):
  if begin:
    begin_date = arrow.get(begin).datetime
    filtered_subscriptions = subscriptions.filter(Subscription.created>=begin_date)
    if end:
      end_date = arrow.get(end).datetime
    else:
      end_date = arrow.now().datetime
    filtered_subscriptions = filtered_subscriptions.filter(Subscription.created<=end_date)
    return filtered_subscriptions
  else:
    return subscriptions


def resetUpdates():
  subs = Subscription.query()
  for s in subs:
    if s.updates:
      print("s %s" % s.email)
      s.updates = None
      s.put()

def checkSubs(email=None):
  if not email:
    email = 'bguzder.wri.org'
  subs = Subscription.query(Subscription.email==email)
  for s in subs:
      print("check sub:  %s" % s)

def clearSubs(email=None):
  if not email:
    email = 'bguzder.wri.org'
  subs = Subscription.query(Subscription.email==email)
  for s in subs:
      print("clear sub:  %s" % s)
      s.updates = None
      s.put()

def confirmed():
  subs = Subscription.with_confirmation()
  for s in subs:
    print("%s" % s)

def unconfirmed():
  subs = Subscription.without_confirmation()
  for s in subs:
    print("%s" % s)

def printUpdates():
  subs = Subscription.query()
  for s in subs:
    print("s %s" % s.updates)