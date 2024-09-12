import json
from isodate import parse_datetime, parse_duration, datetime_isoformat, duration_isoformat
from log.logtypes import info
from dazzler.mediachecks import resolveItem

class Playlist:
    
    def __init__(self, cc, client):
        self.cc = cc
        self.client = client

    def __getObject(self, sid, key):
        try:
            r = self.client.get_object(
                Bucket=self.cc.getScheduleBucket(),
                Key=f'{sid}/{key}'
            )
            if 'Body' in r:
                object = r['Body'].read().decode('utf-8')
                return json.loads(object)
            print(sid, 'no body in s3 response', r)
        except Exception as e:
            print(sid, "Unable to fetch key", key, e)
        return None

    def putObject(self, sid, key, value):
        try:
            bucket = self.cc.getScheduleBucket()
            self.client.put_object(
                    Bucket=bucket,
                    Key=f'{sid}/{key}',
                    Body=json.dumps(value),
                    ContentType="application/json"
            )
        except Exception as e:
            print(sid, f"can't save {key} in {bucket}. Error: {str(e)}")

    def get(self):
        sid = self.cc.getSid()
        print(sid, "fetching emergency playlist")
        data = self.__getObject(sid, 'emergency-playlist.json')
        if data is not None:
            print(sid, "Got emergency Playlist with %d items" % len(data))
            return data
        return None

    def makeScheduleItem(self, start, datum):
        item = {
            'origin': 'loop',
            'start': datetime_isoformat(start), 
            'end': datetime_isoformat(start+parse_duration(datum['duration'])),
            'duration': datum['duration'],
            'pid': datum['pid']
        }
        if 'vpid' in datum:
            item['vpid'] = datum['vpid']
        if 'entityType' in datum:
            item["entityType"] = datum['entityType']
        else:
            item["entityType"] = datum['entity_type']
        if item["entityType"] == 'graphic':
            if 'graphic_duration' in datum:
                item['graphic_duration'] = datum['graphic_duration']
            if 's3' in datum:
                item['url'] = datum['s3']
        return resolveItem(self.cc, item, self.client)

    def getOne(self, after):
        data = self.get()
        if data is None:
            return None
        if len(data) == 0:
            return None
        sid = self.cc.getSid()
        state = self.__getObject(sid, 'channel-state.json')
        if state is None:
            state = { 'emergencyPlaylistIndex': 5 }
        i = state['emergencyPlaylistIndex']
        print(sid, 'PlaylistIndex on entry', i)
        for d in data: # make sure we don't go round more than once 
            if i >= len(data):
                i = 0
            datum = data[i]
            i = i + 1
            item = self.makeScheduleItem(after, datum)
            if item is not None:
                break
        print(sid, 'PlaylistIndex on exit', i)
        state['emergencyPlaylistIndex'] = i
        self.putObject(sid, 'channel-state.json', state)
        return item

    """return the longest item shorter than or equal to the requested gap"""
    def longestFitting(self, wantedStart, wantedEnd):
        data = self.get()
        if data is None:
            return None
        if len(data) == 0:
            return None
        wantedDuration = wantedEnd - wantedStart
        usable = [item for item in data if parse_duration(item['duration'])<=wantedDuration]
        if len(usable)==0:
            return None
        return self.makeScheduleItem(wantedStart, max(usable, key=lambda item: parse_duration(item['duration'])))

    def makeSlateItem(self, start):
        duration = self.cc.getSlateDuration()
        return { 
            'origin': 'slate',
            'entityType': 'slate',
            'start': datetime_isoformat(start), 
            'end': datetime_isoformat(start+duration), 
            'duration':  duration_isoformat(duration),
            'live': False
        }

    def getSome(self, wantedStart, wantedEnd):  
        currentEnd = wantedStart
        items = []
        while currentEnd < wantedEnd:
            item = self.getOne(currentEnd)
            if item is not None:
                items.append(item)
                info(self.cc.getSid(), f'got item from emergency loop {item}')
            else:
                info(self.cc.getSid(), "can't find an item in the schedule or emergency loop - adding a slate")
                items.append(self.makeSlateItem(currentEnd))
            info(self.cc.getSid(), f"added EPL item {items[-1]}")
            currentEnd = parse_datetime(items[-1]['end'])
        return items















