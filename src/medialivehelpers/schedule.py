import json
from isodate import parse_datetime, parse_duration, datetime_isoformat
from botocore.exceptions import ClientError
from log.logtypes import info
from dazzler.mediachecks import resolveItem

# Fields from schedule json examples
#
# Insert Immediate values:
#
# "liveOp": "insertimmediate",
# "nextItemStartTime": "2022-01-18T17:54:50.899Z",
#
# Extend Duration values:
#
# "liveOp": "moveback",
# "nextItemStartTime": "2022-01-18T17:43:18.450Z",
#
# Take Next values:
#
# "liveOp": "bringforward",
# "nextItemStartTime": "2022-01-18T17:12:57.973Z",
# 

class Schedule:
    def __init__(self, cc, client):
        self.cc = cc
        self.client = client
        self.sid = self.cc.getSid()
        
    def mapScheduleItemToPlaylistItem(self, item):
        r = {
            'origin': 'schedule',
            'live': 'live' in item and item['live']
        }
        if 'start' in item:
            r['start'] = datetime_isoformat(parse_datetime(item['start']))
        if 'end' in item:
            r['end'] = datetime_isoformat(parse_datetime(item['end']))
        if 'profiles' in item:
            r['profile'] = item['profiles'][0]
        if 'pg' in item and 'rating' in item['pg']:
            r['rating'] = item['pg']['rating']
        if 's3' in item:
            r['url'] = item['s3']
        if 'source' in item:
            r['stream'] = item['source']
        if 'graphic_duration' in item:
            r['graphic_duration'] = item['graphic_duration']
        if "version" in item:
            version = item['version']
            r['duration'] = version['duration']
            if 'pid' in version:
                r['vpid'] = version['pid']
            if 'entity_type' in version:
                r['entityType'] = version['entity_type']
            if 'version_of' in version:
                r['pid'] = version['version_of']
        if 'broadcast_of' in item: # legacy
            if 'pid' in item['broadcast_of']:
                r['vpid'] = item['broadcast_of']['pid']
        if "version_of" in item:
            versionOf = item['version_of']
            if 'entity_type' in versionOf:
                r['entityType'] = versionOf['entity_type']
            if 'pid' in versionOf:
                r['pid'] = versionOf['pid']
        return r

    def upcomingItems(self, startingOnOrAfter, startingOnOrBefore):
        info(self.sid, f'looking for schedule items starting between {startingOnOrAfter} and {startingOnOrBefore}')
        d1 = startingOnOrAfter.strftime("%Y-%m-%d")
        d2 = startingOnOrBefore.strftime("%Y-%m-%d")
        if d1 == d2:
            all = self.getScheduleForDate(d1)
        else:
            all = self.getScheduleForDate(d1) + self.getScheduleForDate(d2)
        def wanted(item):
            start = parse_datetime(item['start'])
            if start < startingOnOrAfter:
                return False
            if start > startingOnOrBefore:
                return False
            return True
        return [self.mapScheduleItemToPlaylistItem(item) for item in filter(wanted, all)]

    def goodItemOrNone(self, item):
        if "start" not in item:
            print('no start in item so not using')
            return None
        if "end" not in item:
            print('no end in item so not using')
            return None
        if 'vpid' not in item and not item['live']:
            print('no version pid in item and not live so not using', item)
            return None
        return resolveItem(self.cc, item, self.client)

    def scheduleItemToPlaylistItem(self, item):
        r = self.mapScheduleItemToPlaylistItem(item)
        return self.goodItemOrNone(r)

    def upcoming(self, startingOnOrAfter, startingOnOrBefore):
        items = self.upcomingItems(startingOnOrAfter, startingOnOrBefore)
        goodOrNone = [self.goodItemOrNone(item) for item in items]
        return [item for item in goodOrNone if item is not None]

    def getSchedule(self, date):
        pass # to make coverage analysis work
        return self.getScheduleForDate(date.strftime("%Y-%m-%d"))

    def getScheduleHeaderForDate(self, date):
        if self.client is None:
            return None
        items = {}
        key = f'{self.sid}/schedule/{date}-schedule.json'
        scheduleBucket = self.cc.getScheduleBucket()
        try:
            data = self.client.get_object(
                Bucket=scheduleBucket,
                Key=key
            )['Body'].read().decode('utf-8')
            try:
                dzSchedule = json.loads(data)
                if 'liveOp' in dzSchedule:
                    items['liveOp'] = dzSchedule['liveOp']
                    print(self.sid, f'Dazzler Schedule liveOp: {items["liveOp"]}')
                if 'nextItemStartTime' in dzSchedule:
                    items['liveNextItemStartTime'] = dzSchedule['nextItemStartTime']
                else:
                    print(self.sid, 'Dazzler Schedule does not have a live operation! - noop')
            except json.decoder.JSONDecodeError as e:
                print(self.sid, "Unable to decode schedule", key, e)
            except TypeError as e:
                print(self.sid, "Unable to decode schedule", key, e)             
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(self.sid, "no schedule for", date, e)
                print(self.sid, "Used key", key, "for Schedule Bucket", scheduleBucket)
            else:
                print(self.sid, "Unable to fetch schedule", key, e)
        return items    

    def getScheduleForDate(self, date):
        if self.client is None:
            return []
        items = []
        key = f'{self.sid}/schedule/{date}-schedule.json'
        scheduleBucket = self.cc.getScheduleBucket()
        try:
            data = self.client.get_object(
                Bucket=scheduleBucket,
                Key=key
            )['Body'].read().decode('utf-8')
            try:                              
                items = json.loads(data)['items']
                print(f'{self.sid} getSchedule got {len(items)} items')
                self.fixUpSchedule(items)
            except json.decoder.JSONDecodeError as e:
                print(self.sid, "Unable to decode schedule", key, e)
            except TypeError as e:
                print(self.sid, "Unable to decode schedule", key, e)
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                print(self.sid, "no schedule for", date, e)
                print(self.sid, "Used key", key, "for Schedule Bucket", scheduleBucket)
            else:
                print(self.sid, "Unable to fetch schedule", key, e)
        return items

    def fixUpSchedule(self, items):
        for i in range(len(items) - 1):
            if "version" in items[i]:
                essenceDuration = parse_duration(items[i]['version']['duration'])
                essenceEnd = parse_datetime(items[i]['start']) + essenceDuration
                nextStart = parse_datetime(items[i+1]['start'])
                items[i]['end'] = datetime_isoformat(min(essenceEnd, nextStart))
            else:
                items[i]['end'] = items[i+1]['start']
