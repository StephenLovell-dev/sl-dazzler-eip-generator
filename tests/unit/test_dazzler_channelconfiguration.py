from unittest.mock import MagicMock
from datetime import timedelta
from isodate import parse_datetime
import pytz
from dazzler.channelconfiguration import ChannelConfiguration

class TestMain:

    def test_getsid(self):
        cc = ChannelConfiguration('asid', None)
        assert cc.getSid() == 'asid'

    def test_get_channel_id(self):
        cc = ChannelConfiguration('asid', None)
        cc.setChannelId('1')
        assert cc.getChannelId() == '1'

    def test_get_quiet_hour(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getQuietHour() == 2

    def test_is_local_quiet_time(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {
            "quietHour": 2,
            "Timezone": "europe/london",
        }})
        cc = ChannelConfiguration('asid', table)
        assert cc.isLocalQuietTime(parse_datetime('2021-06-25T01:10:00Z'))

    def test_get_channel_name_prefix(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {'ChannelNamePrefix':'pref'}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getChannelNamePrefix() == 'pref'

    def test_get_mediaselector_select_url(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getMediaSelectorSelectURL() == 'https://open.live.bbc.co.uk/mediaselector/6/select/version/2.0/mediaset/ws-clip-syndication-high/proto/https/vpid/'

    def test_get_mediaselector_redirect_url(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getMediaSelectorRedirectURL() == 'https://open.live.bbc.co.uk/mediaselector/6/redir/version/2.0/mediaset/ws-clip-syndication-high/proto/https/vpid/'

    def test_get_ignore_schedule(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getIgnoreSchedule() == False

    def test_get_slate_duration(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getSlateDuration() == timedelta(seconds=30)
        cc.map['slateDuration'] = None
        assert cc.getSlateDuration() == timedelta(seconds=30)
        cc.map['slateDuration'] = 'PT1M'
        assert cc.getSlateDuration() == timedelta(seconds=60)
        cc.map['slateDuration'] = '00:01:30'
        assert cc.getSlateDuration() == timedelta(seconds=90)
        cc.map['slateDuration'] = ''
        assert cc.getSlateDuration() == timedelta(seconds=30)

    def test_get_schedule_limit_reached(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.scheduleLimitReached(500)

    def test_get_schedule_bucket(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getScheduleBucket() == 'ws-dazzler-assets-test'

    def test_get_timezone(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': {}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getTimezone() == pytz.timezone('europe/london')
        cc.map = { 'Timezone': 'Kansas/Oz' }
        assert cc.getTimezone() == pytz.utc

    def test_get_appw_data(self):
        table = MagicMock()
        appw = {
            'Bucket': 'x',
            'Prefix': 'y',
            'RoleArn': 'x',
            'RoleSessionName': ''
        }
        table.get_item = MagicMock(return_value={'Item': { 'APPW': appw }})
        cc = ChannelConfiguration('asid', table)
        assert cc.getAppwData() == appw

    def test_get_missing(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={})
        cc = ChannelConfiguration('asid', table)
        assert cc.getTimezone() == pytz.timezone('europe/london')

    def test_get_capture_queue(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={})
        cc = ChannelConfiguration('asid', table)
        assert cc.getCaptureQueue() is None

    def test_get_stream_url(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': { 'inputs': [] }})
        cc = ChannelConfiguration('asid', table)
        assert cc.getStreamUrl('') == ''
        assert cc.getStreamUrl('sport_stream_11') == ""
        table.get_item = MagicMock(return_value={})
        cc = ChannelConfiguration('asid', table)
        assert cc.getStreamUrl('sport_stream_11') == "http://a.files.bbci.co.uk/media/live/manifesto/audio_video/webcast/hls/uk/b2b/sport_stream_11.m3u8"

    def test_get_authorisation(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': { 'inputs': [] }})
        cc = ChannelConfiguration('asid', table)
        assert cc.getAuthorisation() == 'agerating'

    def test_get_agerating_image_dimensions(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': { 'inputs': [] }})
        cc = ChannelConfiguration('asid', table)
        assert cc.getAgeratingImageDimensions() == { "width": 427, "height": 166, "left": 0, "top": 15 }

    def test_get_do_cleanup(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={})
        cc = ChannelConfiguration('asid', table)
        assert cc.getDoCleanUp()
        table.get_item = MagicMock(return_value={'Item': { 'doCleanUp': True }})
        cc = ChannelConfiguration('asid', table)
        assert cc.getDoCleanUp()
        
    def test_getRegionData(self):
        table = MagicMock()
        table.get_item = MagicMock(return_value={'Item': { 'eu-west-2': {}}})
        cc = ChannelConfiguration('asid', table)
        assert cc.getRegionData('eu-west-1') is None
        assert cc.getRegionData('eu-west-2') == {}