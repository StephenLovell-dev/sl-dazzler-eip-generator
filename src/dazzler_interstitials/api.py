import boto3
from botocore.exceptions import ClientError
import re
import json
import os
import requests
from datetime import timedelta, datetime, timezone
from isodate import datetime_isoformat, parse_duration, parse_datetime
from dazzler.channelconfiguration import ChannelConfiguration
from medialivehelpers.action import Action, truncate_middle, startAndDurationFromActionName
from medialivehelpers.schedule import Schedule as MediaLiveSchedule
from dazzler.schedule import Schedule as DazzlerSchedule
from dazzler.emergencyplaylist import Playlist

alex = []

def query(entityType, pid):
    return {
        'episode': {
                '_source': [
                    "pips.episode.title",
                    "pips.episode.presentation_title",
                    "pips.title_hierarchy",
                    "sonata.episode.aggregatedTitle",
                ], 
                'query': { 'match': { 'pips.episode.pid': pid } }
            },
        'clip': {
                '_source': ["pips.clip.title", "pips.title_hierarchy"], 
                'query': { 'match': { 'pips.clip.pid': pid } }
        }
    }[entityType]

def alextitle(e, entityType):
    item = e['_source']['pips'][entityType]
    if 'title' in item and '$' in item['title']:
        title = item['title']['$']
    elif 'presentation_title' in item and '$' in item['presentation_title']:
        title = item['presentation_title']['$']
    else:
        title = None
    th = e['_source']['pips']['title_hierarchy']
    return title, th

def titleFromAlexandria(entityType, pid):
    global alex
    e = [e for e in alex if e['_source']['pips'][entityType]['pid'] == pid]
    print(alex, pid)
    if len(e) > 0:
        return alextitle(e[0], entityType)
    r = requests.post(f'https://{os.environ["ES_HOST"]}/{entityType}/_search', json=query(entityType, pid))
    h = r.json()['hits']['hits']
    if len(h)>0:
        return alextitle(h[0], entityType)
    return None, None

def addStartTimeSeparators(start):
    ns = start
    r = re.search(r"(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.(\d\d\d)Z", start) 
    if r is not None:
        g = r.groups()
        dateString = "-".join(g[0:3])
        timeString = ":".join(g[3:6])
        # Remove the 100ths of seconds - We might want to put this back at some point!
        # ns = f"{dateString}T{timeString}.{g[6]}Z"
        ns = f"{dateString}T{timeString}Z"
    else:
       ns = start.replace("'", ":")
    return ns

def actionNameToItem(actionName, epl, schedule):
    parts = actionName.split(' ')
    if len(parts) == 4:
        [s, duration, t, pid] = parts
    elif len(parts) == 5:
        [s, duration, t, pid, rating] = parts
    else:
        [s, duration, t] = parts
    si = {
        'start': addStartTimeSeparators(s), 
        'duration': duration,
        'vpid': pid,
        'source': t,
    }
    l = []
    if t == 'loop':
        l = [d for d in epl if truncate_middle(d['vpid'], 10)]
        if len(l)>1:
            print('TODO filter by duration', duration, l)
    elif t == 'sched':
        l = [d for d in schedule if d['start'] == si['start']]
        if len(l) == 0:
            print('are we off schedule?', si['start'], si['vpid'], schedule)
            l = [d for d in schedule if d['vpid'] == si['vpid']]
    if len(l)>0:
        s = l[0]
        print(s)
        si['vpid'] = s['vpid']
        si['pid'] = s['pid']
        si['entity_type'] = s['entityType']
        if 'title' in s:
            si['title'] = s['title']
        else:
            title, titleHeirarchy = titleFromAlexandria(s['entityType'], s['pid'])
            if title is not None:
                si['title'] = title
            if titleHeirarchy is not None:
                si['title_hierarchy'] = titleHeirarchy
    return si

def scheduleItemToItem(item):
    si = { 'source': 'sched' }
    if 'title' in item:
        si['title'] = item['title']
    else:
        title, titleHeirarchy = titleFromAlexandria(item['entityType'], item['pid'])
        if title is not None:
            si['title'] = title
        if titleHeirarchy is not None:
            si['title_hierarchy'] = titleHeirarchy
    for key in item:
        if key in ['vpid', 'start', 'duration']:
            si[key] = item[key]
        elif key == 'pid':
            si['epid'] = item[key]
        elif key == 'pid':
            si['pid'] = item[key]
        elif key == 'entityType':
            si['entity_type'] = item['entityType']
    return si

def item(si):
    a = Action(si['ActionName'], None)
    s = datetime_isoformat(a.start())
    return { 'start': s, 'url': si['ScheduleActionSettings']['InputSwitchSettings']['UrlPath']}

# Get the human readable channel title as set in pips/alexandria for an IPlayer
# channel. The title is stored against and episode so we use an episode pid to get
# it.
def getChannelTitle(channel):
    if 'Tags' in channel:
        if 'epid' in channel['Tags']:
            title, titleHeirarchy = titleFromAlexandria('epsiode', channel['Tags']['epid'])
            return title, titleHeirarchy
    return None, None

def nowNext(cc, ml, s3, qsp):
    hours = int(qsp.get('hours', '3'))
    cd = ml.describe_channel(ChannelId = cc.getChannelId())
    chTitle, chTitleHierarchy = getChannelTitle(cd)
    pd = cd['PipelineDetails']
    dz = DazzlerSchedule(cc, s3)
    epl = Playlist(cc, s3).get()
    if len(pd) == 0:
        return {'status': 'not running' }
    active = pd[0]['ActiveInputSwitchActionName']
    currentStart, currentDuration = startAndDurationFromActionName(active)
    scheduleObject = MediaLiveSchedule(cc.getSid(), cc.getChannelId(), ml)
    mlSchedule = [s for s in scheduleObject.describe().itemNames() if 'Z P' in s]
    if len(mlSchedule) == 0:
        return {'status': 'running, not scheduled' }
    upcoming = []
    lastStart, lastDuration = startAndDurationFromActionName(mlSchedule[-1])
    endOfMlSchedule = lastStart + lastDuration
    scheduleItems = dz.upcomingItems(currentStart, endOfMlSchedule)
    for actionName in mlSchedule:
        if ' sched ' in actionName or ' loop ' in actionName:
            s, d = startAndDurationFromActionName(actionName)
            if s >= currentStart + currentDuration:
                upcoming.append(actionNameToItem(actionName, epl, scheduleItems))
    scheduleItems = dz.upcomingItems(endOfMlSchedule, endOfMlSchedule+timedelta(hours=hours))
    for item in scheduleItems:
        upcoming.append(scheduleItemToItem(item))
    slop = timedelta(minutes=10)
    scheduleItems = dz.upcomingItems(currentStart - slop, currentStart + slop)
    current = actionNameToItem(active, epl, scheduleItems)

    nownext = {
        'status': 'running',
        'now': current,
        'next': upcoming,
    }
    if chTitle is not None:
        nownext['title'] = chTitle
    if chTitleHierarchy is not None:
        nownext['title_hierarchy'] = chTitleHierarchy

    return nownext

def setalex(val):
    global alex
    alex = val

def fetchtitles(items):
    global alex
    pids = set([i['pid'] for i in items])
    print('F', pids)
    q = {
        '_source': [
            "pips.episode.pid",
            "pips.episode.title",
            "pips.episode.presentation_title",
            "pips.title_hierarchy",
        ], 
        'query': { 'terms': { 'pips.episode.pid': list(pids) } }
    }
    r = requests.post(f'https://{os.environ["ES_HOST"]}/_search', json=q)
    setalex(r.json()['hits']['hits'])

def onnow(item):
    s = parse_datetime(item['start'])
    d = parse_duration(item['duration'])
    n = datetime.now(timezone.utc)
    if s > n: return False
    if (s + d) < n: return False
    return True

def scheduleOnly(cc, s3):
    dz = DazzlerSchedule(cc, s3)
    epl = Playlist(cc, s3).get()
    n = datetime_isoformat(datetime.now(timezone.utc))
    scheduleItems = dz.upcomingItems(datetime.now(timezone.utc) - timedelta(hours=4), datetime.now(timezone.utc) + timedelta(hours=4))
    c = [s for s in scheduleItems if onnow(s)]
    if len(c) == 0:
          return {
            'statusCode': 404,
            'body': 'not found',
        }
    current = c[0]
    upcoming = [s for s in scheduleItems if s['start'] > current['start']]
    fetchtitles([current] + upcoming)
    return {
        'status': 'not_running',
        'now': scheduleItemToItem(current),
        'next': [scheduleItemToItem(s) for s in upcoming],
    }

def apiMain(region_name, sid, table, qsp, ml=None):
    cc = ChannelConfiguration(sid, table)
    rd = cc.getRegionData(region_name)
    s3 = cc.getS3(region_name)
    if rd is None:
        return {
            'statusCode': 200,
            'body': json.dumps(scheduleOnly(cc, s3))
        }
    if 'schedule_only' in qsp and (qsp['schedule_only'] == 'true' or qsp['schedule_only'] == '1'):
        return {
            'statusCode': 200,
            'body': json.dumps(scheduleOnly(cc, s3))
        }
    if ml is None:
        ml = cc.getML(region_name)
    channels = ml.list_channels()
    for channel in channels['Channels']:
        if sid in channel['Name']:
            print(channel['Name'], channel['Id'])
            cc.setChannelId(channel['Id'])
            s = nowNext(cc, ml, s3, qsp)
            t = json.dumps(s)
            return {
                'statusCode': 200,
                'body': t
            }
    return {
        'statusCode': 404,
        'body': 'not found',
    }

def handleApiCall(event, table_name):
    if 'queryStringParameters' in event:
        qsp = event['queryStringParameters']
        print(qsp)
    else:
        qsp = {}
    try: 
        path_values = event['requestContext']['http']['path'].split('/')
        if (len(path_values)) != 3:
            return
        [n, sid, region_name] = path_values
        if len(sid) > 0 and len(region_name) > 0:
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            table = dynamodb.Table(table_name)
            return apiMain(region_name, sid, table, qsp)
        return {
            'statusCode': 404,
            'body': 'path must be /<sid>/<region>',
        }
    except ClientError as e:
        return e
