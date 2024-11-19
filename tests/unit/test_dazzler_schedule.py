from unittest.mock import MagicMock, patch
import json
import io
from isodate import parse_datetime
from dazzler.schedule import Schedule
from botocore.exceptions import ClientError

class MockS3:

    def __init__(self, val):
        self.default = val
        self.objects = {}

    def add(self, key, val):
        self.objects[key] = val

    def get_object(self, **kwargs):
        print('get_object', kwargs)
        if kwargs['Key'] in self.objects:
            val = self.objects[kwargs['Key']]
        else:
            val = self.default
        return {'Body': io.BytesIO(val.encode('utf-8'))}

class TestMain:

    @patch('dazzler.mediachecks.checkMS6')
    def test_upcoming_across_midnight(self, mock_check_ms6):
        mock_check_ms6.return_value=True
        cc = MagicMock()
        cc.getScheduleBucket = MagicMock(return_value='x')
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps({}))
        s3.add('asid/schedule/2021-06-26-schedule.json', json.dumps({
            'items': [
                {
                    'start': '2021-06-26T23:58:00Z',
                    'end': '2021-06-26T23:59:00Z',
                },
                {
                    'start': '2021-06-26T23:59:00Z',
                    'end': '2021-06-27T00:00:30Z',
                },
            ]
        }))
        s3.add('asid/schedule/2021-06-27-schedule.json', json.dumps({
            'items': [
                {
                    'start': '2021-06-27T00:00:30Z',
                    'end': '2021-06-27T00:01:00Z',
                },
            ]            
        }))
        s = Schedule(cc, s3)
        start = parse_datetime('2021-06-26T23:59:00Z')
        end = parse_datetime('2021-06-27T00:01:00Z')
        sh = s.upcoming(start, end)
        assert sh == []

    def test_schedule_exists(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s = Schedule(cc, None)

    def test_bad_s3_schedule(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3('{')
        s = Schedule(cc, s3)
        assert s.getScheduleForDate('2021-06-26') == []
    
    def test_get_schedule_for_date(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s = Schedule(cc, None)
        sh = s.getScheduleForDate('2021-06-26')
        assert sh == []

    def test_get_schedule(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s = Schedule(cc, None)
        sh = s.getSchedule(parse_datetime('2021-06-26T16:00:00Z'))
        assert sh == []

    def test_get_schedule_ok(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps({
                'items': []
        }))
        s = Schedule(cc, s3)
        sh = s.getScheduleForDate('2021-06-26')
        assert sh is not None

    def test_get_schedule_throws(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s = Schedule(cc, s3)
        sh = s.getScheduleForDate('2021-06-26')
        assert sh == []
        s3 = MagicMock()
        s3.get_object = MagicMock(side_effect = ClientError({'Error':{'Code':'SomeCode'}}, 'get_object'))
        s = Schedule(cc, s3)
        sh = s.getScheduleForDate('2021-06-26')
        s3.get_object = MagicMock(side_effect = ClientError({'Error':{'Code':'NoSuchKey'}}, 'get_object'))
        s = Schedule(cc, s3)
        sh = s.getScheduleForDate('2021-06-26')

    def test_schedule_item_to_playlist_item(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s = Schedule(cc, s3)
        assert s.scheduleItemToPlaylistItem({}) is None
        assert s.scheduleItemToPlaylistItem({'end': '2021-06-26T16:00:00Z'}) is None
        assert s.scheduleItemToPlaylistItem({'start': '2021-06-26T16:00:00Z'}) is None
        assert s.scheduleItemToPlaylistItem({'start': '2021-06-26T16:00:00Z', 'end': '2021-06-26T16:00:00Z'}) is None

    @patch('dazzler.mediachecks.MediaServicesURI')
    @patch('dazzler.mediachecks.checkInSomeBucket')
    @patch('dazzler.mediachecks.checkMS6')
    def test_schedule_item_to_playlist_item_clip(self, mock_check_ms6, mock_checkInSomeBucket, mock_mediaservices_uri):
        mock_check_ms6.return_value=True
        mock_checkInSomeBucket.return_value = False
        mock_mediaservices_uri.return_value = None
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value='http://x/')
        cc.getMediaSelectorRedirectURL = MagicMock(return_value='http://x/')
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s = Schedule(cc, s3)
        assert s.scheduleItemToPlaylistItem({
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'version': {
                'pid': 'avpid', 'version_of': 'apid', 'entity_type': 'clip',
                'duration': 'PT10M',
            }, 
        }) == {
            'origin': 'schedule',
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'duration': 'PT10M',
            'entityType': 'clip',
            'pid': 'apid',
            'vpid': 'avpid',
            'live': False,
            'url': 'http://x/avpid.mp4',
        }

    def test_schedule_item_to_playlist_item_episode(self):
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s = Schedule(cc, s3)
        assert s.scheduleItemToPlaylistItem({
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'version': {
                'pid': 'avpid',
                'duration': 'PT10M',
            }, 
            'version_of': { 'pid': 'apid', 'entity_type': 'episode' }
        }) == {
            'origin': 'schedule',
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'duration': 'PT10M',
            'entityType': 'episode',
            'pid': 'apid',
            'vpid': 'avpid',
            'live': False,
            'url': 's3://x/avpid.mp4',
        }
        assert s.scheduleItemToPlaylistItem({
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'pg': { 'rating': 'arating' },
            'profiles': ['aprofile'],
            's3': 's3://y/avpid.mp4',
            'version': {
                'pid': 'avpid',
                'duration': 'PT10M',
            }, 
            'version_of': { 'pid': 'apid', 'entity_type': 'episode' }
        }) == {
            'origin': 'schedule',
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'duration': 'PT10M',
            'entityType': 'episode',
            'pid': 'apid',
            'vpid': 'avpid',
            'live': False,
            'url': 's3://y/avpid.mp4',
            'rating': 'arating',
            'profile': 'aprofile',
        }

    def test_schedule_item_to_playlist_item_live(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        cc.getPlayBucket = MagicMock(return_value='x')
        s3 = MagicMock()
        s = Schedule(cc, s3)
        assert s.scheduleItemToPlaylistItem({
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'live': True,
            'source': 'world_service_stream_08',
            'version': {
                'pid': 'avpid',
                'duration': 'PT10M',
            }, 
            'version_of': { 'pid': 'apid', 'entity_type': 'episode' }
        }) == {
            'origin': 'schedule',
            'start': '2021-06-26T16:00:00Z',
            'end': '2021-06-26T16:10:00Z', 
            'duration': 'PT10M',
            'entityType': 'episode',
            'pid': 'apid',
            'vpid': 'avpid',
            'stream': 'world_service_stream_08',  
            'live': True,  
        }