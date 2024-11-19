from unittest.mock import patch
from testfixtures import Replace, mock_datetime
from tests.stubs.requests.mock_request_response import MockRequestResponse
from isodate import parse_datetime, parse_duration
import pytz
from dazzler.schedule import datetime_isoformat
from dazzler.api import addStartTimeSeparators, onnow, query, alextitle, actionNameToItem, getChannelTitle
from dazzler.api import scheduleItemToItem

def makeItem(start, duration, type, origin):
    s = parse_datetime(start)
    if s.tzinfo is None:
        utc = pytz.timezone('UTC')
        s = utc.localize(s)
    end = datetime_isoformat(s + parse_duration(duration))
    item = {'origin': origin, 'entityType': type,
            'duration': duration, 'start': start, 'end': end}
    if origin in ['loop', 'schedule']:
        item['url'] = 'http://test'
        item['vpid'] = 'avpid'
    item['live'] = type == 'live'
    if type == 'live':
        item['stream'] = 'world_service_stream_08'
    if type == 'graphic':
        item['graphic_duration'] = 'PT24H'
    return item    

class TestMain:

    def test_query(self):
        assert query('clip', 'apid') is not None
        assert query('episode', 'apid') is not None

    def test_alextitle(self):
        assert alextitle({ 'episode': {}, 'title_hierarchy': {}}, 'episode') is not None

    def test_addStartTimeSeparators(self):
        startDate = '20230206T140934.000Z'
        assert addStartTimeSeparators(startDate) == '2023-02-06T14:09:34Z'
        startDate = "2023-02-06T14'09'34Z"
        assert addStartTimeSeparators(startDate) == '2023-02-06T14:09:34Z'

    def test_actionNameToItem(self):
        actionName = '20231023T000000Z PT10M sched p0'
        epl = []
        schedule = [{ 'start': '2023-10-23T00:00:00Z', 'pid': 'p1', 'vpid': 'p0', 'duration': 'PT10M', 'entityType': 'episode'}]
        assert actionNameToItem(actionName, epl, schedule) is not None

    @patch('dazzler.api.titleFromAlexandria')
    def test_scheduleItemToItem(self, mock_titleFromAlexandria):
        mock_titleFromAlexandria.return_value = (None, None)
        item = {
            "title": "Series 1 - Cheese Moon",
            "start": "2023-01-13T00:29:34.760Z",
            "end": "2023-01-13T00:36:34.800Z",
            "live": False,
            "duration": "PT7M0.04S",
            "vpid": "m001gqdb",
            "entityType": "episode",
            "pid": "p0d3rxj0",
            "s3": "s3://livemodavdistributionresources-distributionbucket-182btg2y28f33/av_pv13_pa4/modav/bUnknown-d024e48b-a49e-4d42-8954-ee5f9deadf0f_m001gqdb_pips-pid-m001gqdb_1672423724909.mp4",
            "profiles": "av_pv13_pa4"
        }
        expectedItem = {
            'source': 'sched', 
            'title': 'Series 1 - Cheese Moon', 
            'start': '2023-01-13T00:29:34.760Z', 
            'duration': 'PT7M0.04S', 
            'vpid': 'm001gqdb', 
            'entity_type': 'episode', 
            'epid': 'p0d3rxj0'
        }
        resultItem = scheduleItemToItem(item, {})
        assert resultItem == expectedItem
        mock_titleFromAlexandria.return_value = ('Series 1 - Cheese Moon', None)
        item = {
            "start": "2023-01-13T00:29:34.760Z",
            "end": "2023-01-13T00:36:34.800Z",
            "live": False,
            "duration": "PT7M0.04S",
            "vpid": "m001gqdb",
            "entityType": "episode",
            "pid": "p0d3rxj0",
            "s3": "s3://livemodavdistributionresources-distributionbucket-182btg2y28f33/av_pv13_pa4/modav/bUnknown-d024e48b-a49e-4d42-8954-ee5f9deadf0f_m001gqdb_pips-pid-m001gqdb_1672423724909.mp4",
            "profiles": "av_pv13_pa4"
        }
        resultItem = scheduleItemToItem(item, { 'episodes': [{ 'episode': {'pid':'p0d3rxj0', 'title': { '$': 'Series 1 - Cheese Moon'}}}]})
        assert resultItem == expectedItem

    def test_onnow(self):
        assert not onnow({ 'start': '2023-10-23T00:00:00Z', 'duration': 'PT1M'})
        with Replace('dazzler.api.datetime', mock_datetime(2023, 10, 23, 00, 00, 30)):
            assert onnow({ 'start': '2023-10-23T00:00:00Z', 'duration': 'PT1M'})

    @patch('dazzler.api.titleFromAlexandria')
    def test_get_channel_title(self, mock_titleFromAlexandria):
        channel = {

        }
        assert getChannelTitle(channel) == (None, None)
        mock_titleFromAlexandria.return_value = ('Some Test Channel', None)
        channel = {
            'Tags': {
                'epid': 'somePid'
            }
        }
        assert getChannelTitle(channel) == ('Some Test Channel', None)
        channel = {
            'Tags': {
                'epid': 'somePid'
            }
        }
        assert getChannelTitle(channel) == ('Some Test Channel', None)
