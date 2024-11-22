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
from dazzler.profiling import logStart, logEnd

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

def alextitle(e, entity_type):
    item = e[entity_type]
    title = item.get('title', { '$': None })['$']
    if title is None:
        title = item.get('presentation_title', { '$': None })['$']
    return title, e.get('title_hierarchy', None)

def titleFromAlexandria(entityType, pid):
    try:
        global alex
        e = [e for e in alex if e['_source']['pips'][entityType]['pid'] == pid]
        print(alex, pid)
        if len(e) > 0:
            return alextitle(e[0], entityType)
        r = requests.post(f'https://{os.environ["ES_HOST"]}/{entityType}/_search', json=query(entityType, pid))
        h = r.json()['hits']['hits']
        if len(h)>0:
            return alextitle(h[0], entityType)
    except Exception as err:
        print(f"Unexpected {err=}, {type(err)=}")
    return None, None

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

def scheduleItemToItem(item, alex):
    si = { 'source': 'sched'}
    for key in item:
        if key in ['title', 'vpid', 'start', 'duration']:
            si[key] = item[key]
        elif key == 'pid':
            si['epid'] = item[key]
        elif key == 'entityType':
            si['entity_type'] = item['entityType']
    if 'title' in si or alex is None:
        return si
    if si['entity_type'] == 'episode':
        e = [e for e in alex['episodes'] if e['episode']['pid'] == item['pid']]
    else:
        e = [e for e in alex['clips'] if e['clip']['pid'] == item['pid']]
    if len(e) > 0:
        title, titleHeirarchy = alextitle(e[0], si['entity_type'])
        if title is not None:
            si['title'] = title
        if titleHeirarchy is not None:
            si['title_hierarchy'] = titleHeirarchy
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
            title, titleHeirarchy = titleFromAlexandria('episode', channel['Tags']['epid'])
            return title, titleHeirarchy
    return None, None

def createUpcoming(cc, active, region_name):
    sid = cc.getSid()
    start = logStart(sid, 'nowNext')
    ml = cc.getML(region_name)
    cd = ml.describe_channel(ChannelId = cc.getChannelId())
    chTitle, chTitleHierarchy = getChannelTitle(cd)
   
    cd = ml.describe_channel(ChannelId = cc.getChannelId())
    currentStart, currentDuration = startAndDurationFromActionName(active)
    scheduleObject = MediaLiveSchedule(cc.getSid(), cc.getChannelId(), ml)
    mlSchedule = [s for s in scheduleObject.describe().itemNames() if 'Z P' in s]
    if len(mlSchedule) == 0:
        return {'status': 'running, not scheduled' }
    s3 = cc.getS3(region_name)
    dz = DazzlerSchedule(cc, s3)
    epl = Playlist(cc, s3).get()
    lastStart, lastDuration = startAndDurationFromActionName(mlSchedule[-1])
    endOfMlSchedule = lastStart + lastDuration
    scheduleItems = dz.upcomingItems(currentStart, endOfMlSchedule)
    upcoming = []
    for actionName in mlSchedule:
        if ' sched ' in actionName or ' loop ' in actionName:
            s, d = startAndDurationFromActionName(actionName)
            if s >= currentStart + currentDuration:
                upcoming.append(actionNameToItem(actionName, epl, scheduleItems))
    
    next = {
        'status': 'running',
        'next': upcoming,
    }
    if chTitle is not None:
        next['title'] = chTitle
    if chTitleHierarchy is not None:
        next['title_hierarchy'] = chTitleHierarchy
    logEnd(sid, 'nowNext', start)    

    return next

def nowNext(cc, ml, s3, hours):
    sid = cc.getSid()
    start = logStart(sid, 'nowNext')
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
    logEnd(sid, 'nowNext', start)    

    return nownext

def fetchtitles(sid, episodeItems, clipItems):
    start = logStart(sid, 'fetchtitles')
    episodes = []
    if len(episodeItems) > 0:
        pids = set([i['pid'] for i in episodeItems])
        print('F episodes', pids)
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
        episodes.extend([i['_source']['pips'] for i in r.json()['hits']['hits']])
    clips = []
    if len(clipItems) > 0:
        pids = set([i['pid'] for i in clipItems])
        print('F clips', pids)
        q = {
            '_source': [
                "pips.clip.pid",
                "pips.clip.title", 
                "pips.title_hierarchy",
            ], 
            'query': { 'terms': { 'pips.clip.pid': list(pids) } }
        }
        r = requests.post(f'https://{os.environ["ES_HOST"]}/_search', json=q)
        clips.extend([i['_source']['pips'] for i in r.json()['hits']['hits']])
    logEnd(sid, 'fetchtitles', start)
    return { 'episodes': episodes, 'clips': clips }

def onnow(item):
    s = parse_datetime(item['start'])
    d = parse_duration(item['duration'])
    n = datetime.now(timezone.utc)
    if s > n: return False
    if (s + d) < n: return False
    return True

def scheduleOnly(cc, s3):
    sid = cc.getSid()
    start = logStart(sid, 'scheduleOnly')
    dz = DazzlerSchedule(cc, s3)
    scheduleItems = dz.upcomingItems(datetime.now(timezone.utc) - timedelta(hours=4), datetime.now(timezone.utc) + timedelta(hours=4))
    c = [s for s in scheduleItems if onnow(s)]
    if len(c) == 0:
        logEnd(sid, 'scheduleOnly - schedule not found', start)
        return {
            'statusCode': 404,
            'body': 'not found',
        }
    current = c[0]
    upcoming = [s for s in scheduleItems if s['start'] > current['start']]
    items = [current] + upcoming
    episodeItems = [e for e in items if e['entityType'] == 'episode' and 'title' not in e]
    clipItems = [c for c in items if c['entityType'] == 'clip' and 'title' not in c]
    if len(episodeItems) > 0 or len(clipItems) > 0:
        alex = fetchtitles(sid, episodeItems, clipItems)
    else:
        alex = None
    now = scheduleItemToItem(current, alex)
    next = [scheduleItemToItem(s, alex) for s in upcoming]
    logEnd(sid, 'scheduleOnly', start)
    return {
        'status': 'not_running',
        'now': now,
        'next': next,
    }

def mediaLivePlusSchedule(cc, region_name, sid, hours, ml, s3):
    start = logStart(sid, 'mediaLivePlusSchedule')
    if ml is None:
        mlstart = logStart(sid, 'cc.getML')
        ml = cc.getML(region_name)
        logEnd(sid, 'cc.getML', mlstart)
    mllcstart =logStart(sid, 'ml.list_channels()')
    channels = ml.list_channels()
    logEnd(sid, 'cc.getML', mllcstart)
    for channel in channels['Channels']:
        if sid in channel['Name']:
            print(channel['Name'], channel['Id'])
            cc.setChannelId(channel['Id'])
            s = nowNext(cc, ml, s3, hours)
            logEnd(sid, 'mediaLivePlusSchedule', start)
            return s
    logEnd(sid, 'mediaLivePlusSchedule - channel not found', start)

def apiMain(cc, region_name, sid, schedule_only, hours, ml=None):
    apiMainStart = logStart(sid, 'apiMain')
    start = logStart(sid, 'cc = ChannelConfiguration(sid, table)')
    logEnd(sid, 'cc = ChannelConfiguration(sid, table)', start)
    s3 = cc.getS3(region_name)
    if schedule_only:
        r = scheduleOnly(cc, s3)
        logEnd(sid, 'apiMain > now/next from schedule_only', apiMainStart)
    else:
        r = mediaLivePlusSchedule(cc, region_name, sid, hours, ml, s3)
        logEnd(sid, 'apiMain > now/next from medialive and schedule', apiMainStart)
    if r is not None:
        return {
            'statusCode': 200,
            'body': json.dumps(r)
        }
    return {
        'statusCode': 404,
        'body': 'not found',
    }

def handleApiCall(event, table_name):
    path_values = event['requestContext']['http']['path'].split('/')
    if (len(path_values)) != 3:
        return
    [n, sid, region_name] = path_values
    if 'queryStringParameters' in event:
        qsp = event['queryStringParameters']
        schedule_only = qsp.get('schedule_only', '0') in ['true', '1']
        hours = int(qsp.get('hours', '3'))
    else:
        hours = 3
        schedule_only = False
    try:
        start = logStart(sid, 'handleApiCall')
        if len(sid) > 0 and len(region_name) > 0:
            dynamodb = boto3.resource('dynamodb', region_name=region_name)
            table = dynamodb.Table(table_name)
            cc = ChannelConfiguration(sid, table)
            res = apiMain(cc, region_name, sid, schedule_only, hours)
            logEnd(sid,'handleApiCall', start)
            return res
        logEnd(sid,'handleApiCall 404', start)
        return {
            'statusCode': 404,
            'body': 'path must be /<sid>/<region>',
        }  
    except ClientError as e:
        return e
