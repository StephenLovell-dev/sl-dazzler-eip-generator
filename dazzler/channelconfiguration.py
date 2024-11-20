import pytz
from datetime import timedelta

from boto3 import Session
from isodate import parse_duration
import boto3
from botocore.exceptions import ClientError

defaultValues = {
  "EventsInNearlyFullSchedule": 500,
  "ignoreSchedule": False,
  "MediaSelectorURL": "https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/ws-clip-syndication-high/proto/https/vpid/",
  "MS6URL": "https://open.live.bbc.co.uk/mediaselector/6/redir/version/2.0/mediaset/ws-clip-syndication-high/proto/https/vpid/",
  "quietHour": 2,
  "authorisation": "agerating",
  "agerating_image_dimensions": {
    "width": 427,
    "height": 166,
    "left": 0,
    "top": 15,
  },
  "Timezone": "europe/london",
  "schedule_bucket": "ws-dazzler-assets-test",
  "playBucket": "ws-dazzler-assets-test",
  "capture_queue_url": None,
  "inputs": [
    {
    "type": "dynamic",
    "url": "$urlPath$",
    "label_suffix": "dynamic"
    },
    {
    "duration": "00:00:10",
    "type": "static",
    "url": "https://ws-dazzler-assets.s3-eu-west-1.amazonaws.com/silver_10s_slate.mp4",
    "label_suffix": "slate"
    },
    {
    "type": "hls",
    "url": "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/webcast/hls/uk/b2b/sport_stream_11.m3u8",
    "label_suffix": "live",
    "sid": "sport_stream_11"
    }
   ]
 }

class ChannelConfiguration():

    def __init__(self, sid, table):
        self.sid = sid
        self.table = table
        self.chanId = None
        self.map = None

    def _get(self):
        if self.map is None:
            response = self.table.get_item(Key={"sid": self.sid})
            if 'Item' in response:
                self.map = { **defaultValues, **response['Item'] }
            else:
                self.map = defaultValues

    def _getItem(self, key):
        self._get()
        if key in self.map:
            return self.map[key]
        return None

    def _getBool(self, key):
        return self._getItem(key)

    def getSid(self):
        return self.sid

    def getQuietHour(self) -> int:
        return self._getItem('quietHour')

    def getGuardTime(self):
        return timedelta(seconds=60)

    def getMaxDriftSeconds(self):
        return 10

    def isLocalQuietTime(self, time) -> bool:
        localTimeZone = self.getTimezone()
        timeInTZ = time.astimezone(localTimeZone)
        quietHour = self.getQuietHour()
        return timeInTZ.hour == quietHour

    def setChannelId(self, chanId):
        self.chanId = chanId

    def getChannelId(self):
        return self.chanId

    def getAppwData(self):
        return self._getItem('APPW')

    def getChannelNamePrefix(self) -> str:
        return self._getItem('ChannelNamePrefix')

    def getIgnoreSchedule(self) -> bool:
        return self._getBool('ignoreSchedule')

    def getMediaSelectorSelectURL(self) -> str:
        return self._getItem('MediaSelectorURL')

    def getMediaSelectorRedirectURL(self) -> str:
        return self._getItem('MS6URL')

    def scheduleLimitReached(self, records) -> int:
        return int(self._getItem('EventsInNearlyFullSchedule')) <= records

    def getScheduleBucket(self) -> str:
        return self._getItem('schedule_bucket')

    def getPlayBucket(self) -> str:
        return self._getItem('playBucket')

    def getTimezone(self):
        tz = self._getItem('Timezone')
        try:
            return pytz.timezone(tz)
        except pytz.exceptions.UnknownTimeZoneError as e:
            print(f'unknown timezone {e} falling back to UTC')
            return pytz.utc

    def getSlateDuration(self) -> str:
        duration = self._getItem('slateDuration')
        if duration is None:
            return timedelta(seconds=30)
        elif ':' in duration:
            h,m,s = duration.split(":")
            seconds = (int(h) * 3600 + (int(m) * 60) + int(s))
            return timedelta(seconds=seconds)
        elif duration.startswith('P'):
            return parse_duration(duration)
        return timedelta(seconds=30)

    def getCaptureQueue(self) -> str:
        return self._getItem('capture_queue_url')
    
    def getStreamUrl(self, sid) -> str:
        for inp in self._getItem('inputs'):
            if 'sid' in inp and inp['sid'] == sid:
                return inp['url']
        return ''

    def getDoCleanUp(self) -> bool:
        r = self._getBool('doCleanUp')
        if r is None:
            return True
        return r

    def getAuthorisation(self) -> str:
        return self._getItem('authorisation')

    def getAgeratingImageDimensions(self) -> dict:
        return self._getItem('agerating_image_dimensions')

    def getML(self, region):
        channelRole = self._getItem('channelRole')
        if channelRole is not None:
            channelExternalId = self._getItem('channelExternalId')
            sts=boto3.client('sts')
            rr=sts.assume_role(
                RoleArn=channelRole,
                RoleSessionName='newsession',
                ExternalId=channelExternalId
            )
            session = Session(
                aws_access_key_id=rr['Credentials']['AccessKeyId'],
                aws_secret_access_key=rr['Credentials']['SecretAccessKey'],
                aws_session_token=rr['Credentials']['SessionToken']
            )
            ml = session.client('medialive', region_name=region)
        else:
            ml = boto3.client('medialive', region_name=region)
        return ml

    def getS3(self, region):
        channelRole = self._getItem('channelRole')
        if channelRole is not None:
            channelExternalId = self._getItem('channelExternalId')
            sts=boto3.client('sts')
            rr=sts.assume_role(
                RoleArn=channelRole,
                RoleSessionName='newsession',
                ExternalId=channelExternalId
            )
            session = Session(
                aws_access_key_id=rr['Credentials']['AccessKeyId'],
                aws_secret_access_key=rr['Credentials']['SecretAccessKey'],
                aws_session_token=rr['Credentials']['SessionToken']
            )
            return session.client('s3', region_name=region)
        else:
            return boto3.client('s3', region_name=region)

    def getRegionData(self, region):
        try:
            return self._getItem(region)
        except:
            return None
        
    def getShouldGenerateUpcoming(self):
        se = self._getItem('secondary_events')
        if se is not None:
            if 'overlays' in se:
                for item in se['overlays']:
                    if 'type' in item:
                        if item['type'] == 'interstitial':
                            return True
        return False