import io
import json
from datetime import timedelta
from isodate import parse_datetime
from unittest.mock import MagicMock, patch
from botocore.exceptions import ClientError
from dazzler.emergencyplaylist import Playlist

class MockS3:

    def __init__(self, val):
        self.val = io.BytesIO(val.encode('utf-8'))

    def head_object(self, **kwargs):
        print('head_object', kwargs)
        return None

    def get_object(self, **kwargs):
        return {'Body': self.val}

    def put_object(self, **kwargs):
        return {'Body': self.val}

class TestMain:

    def test_get_one_empty(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps([]))
        epl = Playlist(cc, s3)
        assert epl.getOne(parse_datetime('2021-06-26T16:00:00Z')) is None

    @patch('dazzler.mediachecks.checkMS6')
    def test_get_one_ok(self, mock_check_ms6):
        mock_check_ms6.return_value=True
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps([
            {
                'duration': 'PT10S',
                'pid': 'apid',
                'vpid': 'avpid',
                'entity_type': 'clip'
            }
        ]))
        epl = Playlist(cc, s3)
        assert epl.getOne(parse_datetime('2021-06-26T16:00:00Z')) is not None

    @patch('dazzler.emergencyplaylist.Playlist')
    def test_get_nothing(self, mock_Playlist):
        epl_instance = mock_Playlist.return_value
        epl_instance.get.return_value = [{'entity_type':'episode', 'start':'2021-06-26T16:00:00Z', 'duration': 'PT1M', 'vpid': 'avpid', 'pid': 'apid'}]
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s3.get_object = MagicMock()
        epl = Playlist(cc, s3)
        assert epl.getOne(parse_datetime('2021-06-26T16:00:00Z')) is None
    
    @patch('dazzler.mediachecks.checkMS6')
    def test_get_some_ok(self, mock_check_ms6):
        mock_check_ms6.return_value=True
        cc = MagicMock()
        cc.getSlateDuration = MagicMock(return_value=timedelta(seconds=30))
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps([
            {
                'duration': 'PT10S',
                'pid': 'apid',
                'vpid': 'avpid',
                'entity_type': 'clip'
            }
        ]))
        s = parse_datetime('2021-06-26T16:00:00Z')
        e = parse_datetime('2021-06-26T17:00:00Z')
        epl = Playlist(cc, s3)
        assert epl.getSome(s, e) is not None

    @patch('dazzler.mediachecks.checkInSomeBucket')
    @patch('dazzler.mediachecks.checkMS6')
    @patch('dazzler.mediachecks.MediaServicesURI')
    def test_make_schedule_item_from_clip(self, mock_mediaservices_uri, mock_check_ms6, mock_checkInSomeBucket):
        mock_mediaservices_uri.return_value = None
        mock_check_ms6.return_value = True
        mock_checkInSomeBucket.return_value = False
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getMediaSelectorRedirectURL = MagicMock(return_value='http://x/')
        epl = Playlist(cc, None)
        item = {
                'duration': 'PT10S',
                'pid': 'apid',
                'vpid': 'avpid',
                'entity_type': 'clip'
            }
        assert epl.makeScheduleItem(parse_datetime('2021-06-26T16:00:00Z'), item) == {
            'origin': 'loop',
            'duration': 'PT10S',
            'end': '2021-06-26T16:00:10Z',
            'entityType': 'clip',
            'pid': 'apid',
            'vpid': 'avpid',
            'start': '2021-06-26T16:00:00Z',
            'url': 'http://x/avpid.mp4',
        }

    @patch('dazzler.mediachecks.checkInSomeBucket')
    @patch('dazzler.mediachecks.checkS3Uri')
    def test_make_schedule_item_from_episode(self, mock_checkS3Uri, mock_checkInSomeBucket):
        mock_checkS3Uri.return_value = True
        mock_checkInSomeBucket.return_value = True
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        epl = Playlist(cc, None)
        item = {
                'duration': 'PT10S',
                'pid': 'apid',
                'vpid': 'avpid',
                'entityType': 'episode'
            }
        assert epl.makeScheduleItem(parse_datetime('2021-06-26T16:00:00Z'), item) == {
          'origin': 'loop',
          'start': '2021-06-26T16:00:00Z',
          'end': '2021-06-26T16:00:10Z',
          'duration': 'PT10S',
          'entityType': 'episode',
           'pid': 'apid',
          'vpid': 'avpid',
          'url': 's3://x/avpid.mp4',
        }

    @patch('dazzler.emergencyplaylist.Playlist.get')
    def test_longest_fitting_none(self, mock_get):
        mock_get.return_value = None
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps([]))
        epl = Playlist(cc, s3)
        assert epl.longestFitting(None, None) is None

    @patch('dazzler.mediachecks.checkS3Uri')
    def test_longest_fitting(self, mock_checkS3Uri):
        mock_checkS3Uri.return_value = True
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MockS3(json.dumps([]))
        epl = Playlist(cc, s3)
        wantedStart = parse_datetime('2021-07-08T00:00:00Z')
        wantedEnd = parse_datetime('2021-07-08T00:10:00Z')
        assert epl.longestFitting(wantedStart, wantedEnd) is None
        s3 = MockS3(json.dumps([
            {'entity_type':'episode','duration':'PT09M','pid': 'pid1', 'vpid':'vpid1'},
            {'entity_type':'episode','duration':'PT10M','pid': 'pid1', 'vpid':'vpid1'},
            {'entity_type':'episode','duration':'PT15M','pid': 'pid2', 'vpid':'vpid2'},
        ]))
        epl = Playlist(cc, s3)
        assert epl.longestFitting(wantedStart, wantedEnd) == {
            'duration': 'PT10M', 
            'end': '2021-07-08T00:10:00Z', 
            'entityType': 'episode', 
            'origin': 'loop', 
            'pid': 'pid1', 
            'start': '2021-07-08T00:00:00Z', 
            'vpid': 'vpid1',
            'url': 's3://x/vpid1.mp4',
        }

    def test_longest_fitting_nothing_fits(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        wantedStart = parse_datetime('2021-07-08T00:00:00Z')
        wantedEnd = parse_datetime('2021-07-08T00:08:00Z')
        s3 = MockS3(json.dumps([
            {'entity_type':'episode','duration':'PT09M','pid': 'pid1', 'vpid':'vpid1'},
            {'entity_type':'episode','duration':'PT10M','pid': 'pid1', 'vpid':'vpid1'},
            {'entity_type':'episode','duration':'PT15M','pid': 'pid2', 'vpid':'vpid2'},
        ]))
        epl = Playlist(cc, s3)
        assert epl.longestFitting(wantedStart, wantedEnd) is None

    @patch('dazzler.mediachecks.MediaServicesURI')
    @patch('dazzler.mediachecks.checkS3Uri')
    def test_longest_fitting_from_file(self, mock_checkS3Uri, mock_MediaServicesURI):
        mock_checkS3Uri.return_value = True
        mock_MediaServicesURI.return_value = 's3://modav/p084lfpl.mp4'
        with open('tests/unit/emergency-playlist.json', 'r') as file:
            data=file.read()
        cc = MagicMock()
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        wantedStart = parse_datetime('2021-07-08T00:00:00Z')
        wantedEnd = parse_datetime('2021-07-08T00:08:00Z')
        s3 = MockS3(data)
        epl = Playlist(cc, s3)
        assert epl.longestFitting(wantedStart, wantedEnd) == {
            'start': '2021-07-08T00:00:00Z', 
            'duration': 'PT2M21S', 
            'end': '2021-07-08T00:02:21Z', 
            'entityType': 'episode', 
            'origin': 'loop', 
            'pid': 'p084kklwp084lfpl', 
            'vpid': 'p084lfpl',
            'url': 's3://x/p084lfpl.mp4',
        }

    def test_s3(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        s3.put_object = MagicMock(side_effect=ClientError(MagicMock(),'put_object'))
        epl = Playlist(cc, s3)
        assert epl.putObject('a', 'b', 'c') is None
