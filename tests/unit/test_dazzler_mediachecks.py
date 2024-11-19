from unittest.mock import MagicMock, patch
import responses
import io
import json
from botocore.exceptions import ClientError
from dazzler.mediachecks import getReplacementVersion, checkMediaSelectorResult
from dazzler.mediachecks import checkMS6, checkS3Uri, itemIsLive
from dazzler.mediachecks import validClip, MediaServicesURI, resolveItem
from dazzler.mediachecks import dazzlerURI, MediaServicesURI

class MockS3:

    def __init__(self, val):
        self.val = io.BytesIO(val.encode('utf-8'))

    def get_object(self, **kwargs):
        return {'Body': self.val}

    def assume_role(self, **kwargs):
        return {'Credentials': {'AccessKeyId': '', 'SecretAccessKey': '', 'SessionToken': ''} }
        
class TestMain:

    def test_check_media_selector_result(self):
        assert not checkMediaSelectorResult({})
        assert not checkMediaSelectorResult({'media': []})
        assert not checkMediaSelectorResult({'media': [
            { 'bitrate': 100 }
        ]})
        assert not checkMediaSelectorResult({'media': [
            { 'bitrate': 800, 'type': 'thumbnail' }
        ]})
        assert not checkMediaSelectorResult({'media': [
            { 'bitrate': 800, 'type': 'video/mp4' }
        ]})
        assert not checkMediaSelectorResult({'media': [
            { 'bitrate': 800, 'type': 'video/mp4', 'width': 320 }
        ]})
        assert not checkMediaSelectorResult({'media': [
            { 'bitrate': 800, 'type': 'video/mp4', 'width': 640 }
        ]})
        assert not checkMediaSelectorResult({'media': [
            {
                'bitrate': 800, 'type': 'video/mp4', 'width': 640,
                'connection': []
             }
        ]})
        assert not checkMediaSelectorResult({'media': [
            {
                'bitrate': 800, 'type': 'video/mp4', 'width': 640, 'connection': [{}]
             }
        ]})
        assert not checkMediaSelectorResult({'media': [
            {
                'bitrate': 800, 'type': 'video/mp4', 'width': 640,
                'connection': [
                    { 'transferFormat': 'dash'}
                ]
             }
        ]})
        assert checkMediaSelectorResult({'media': [
            {
                'bitrate': 800, 'type': 'video/mp4', 'width': 640,
                'connection': [
                    { 'transferFormat': 'plain'}
                ]
             }
        ]})

    @patch('dazzler.mediachecks.boto3')
    def test_get_replacement_version_none(self, boto3):
        cc = MagicMock()
        cc.getAppwData = MagicMock(return_value={
            'Bucket': 'x',
            'Prefix': 'y',
            'RoleArn': 'x',
            'RoleSessionName': ''
        })
        assert getReplacementVersion(cc, 'apid', 'avpid') is None

    @patch('dazzler.mediachecks.boto3')
    def test_get_replacement_version_throw(self, boto3):
        cc = MagicMock()
        cc.getAppwData = MagicMock(return_value={
            'Bucket': 'x',
            'Prefix': 'y',
            'RoleArn': 'x',
            'RoleSessionName': ''
        })
        assert getReplacementVersion(cc, 'apid', 'avpid') is None

    @patch('dazzler.mediachecks.boto3')
    def test_get_replacement_version_ok(self, boto3):
        cc = MagicMock()
        cc.getAppwData = MagicMock(return_value={
            'Bucket': 'x',
            'Prefix': 'y',
            'RoleArn': 'x',
            'RoleSessionName': ''
        })
        appw = { 'programme_availability': { 'available_versions': {'available_version':[
            {
                'version': { 'pid': 'avpid'},
                'availabilities': {'ondemand':[{'broadcast_of':{'link':{'pid':'avpid'}}}]}
            },
            {
                'version': { 'pid': 'anothervpid'},
                'availabilities': {'ondemand':[{
                    'broadcaster':{'link':{'sid':'video_streaming_noprot_1732'}},
                    'broadcast_of':{'link':{'pid':'anothervpid'}}
                }]}
            },
        ]}} }
        s3 = MockS3(json.dumps(appw))
        boto3.client=MagicMock(return_value=s3)
        assert getReplacementVersion(cc, 'apid', 'avpid') == 'anothervpid'
        appw = { 'programme_availability': { 'available_versions': {'available_version':[]}} }
        s3 = MockS3(json.dumps(appw))
        assert getReplacementVersion(cc, 'apid', 'avpid') is None

    @patch('dazzler.mediachecks.requests')
    def test_checkms6(self, requests):
        requests.get = MagicMock(return_value=MagicMock(status_code=404))
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value='http://x/')
        cc.getAppwData = MagicMock(return_value={
            'Bucket': 'x',
            'Prefix': 'y',
            'RoleArn': 'x',
            'RoleSessionName': ''
        })
        pid = 'apid'
        vpid = 'avpid'
        assert not checkMS6(cc, pid, vpid)

    @patch('dazzler.mediachecks.checkMediaSelectorResult')
    @patch('dazzler.mediachecks.requests')
    def test_checkms6_unsuitable(self, requests, cms):
        requests.get = MagicMock(return_value=MagicMock(status_code=200))
        cms.return_value=False
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value='http://x/')
        r = checkMS6(cc, 'apid', 'avpid')
        assert r == False

    @patch('dazzler.mediachecks.getReplacementVersion')
    @patch('dazzler.mediachecks.requests')
    def test_checkms6_replaced(self, requests, grv):
        requests.get = MagicMock(return_value=MagicMock(status_code=404))
        grv.return_value = 'anothervpid'
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value='http://x/')
        r = checkMS6(cc, 'apid', 'avpid')
        assert r == 'anothervpid'

    def test_checkms6_no_url(self):
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value=None)
        pid = 'apid'
        vpid = 'avpid'
        assert checkMS6(cc, pid, vpid)

    def test_checkS3Uri_ok(self):
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value=None)
        s3 = MagicMock()
        vpid = 'avpid'
        assert checkS3Uri(cc, dazzlerURI(cc, vpid), s3)

    def test_checkS3Uri_throw(self):
        cc = MagicMock()
        cc.getMediaSelectorSelectURL = MagicMock(return_value=None)
        s3 = MagicMock(head_object=MagicMock(side_effect = ClientError(MagicMock(), 'resource')))
        vpid = 'avpid'
        assert not checkS3Uri(cc, dazzlerURI(cc, vpid), s3)

    def test_item_is_live(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        assert not itemIsLive(cc, {'entityType':'episode'})
        assert itemIsLive(cc, {'entityType':'live'})

    @patch('requests.get')
    @patch('dazzler.mediachecks.checkMediaSelectorResult')
    def test_valid_good_clip(self, cms, patched):
        cms.return_value=True
        patched.return_value = MagicMock(status_code=200,response=json.dumps({'key':'value'})) 
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        assert validClip({'entityType': 'clip', 'pid': 'apid', 'vpid': 'apid'}, cc)

    @patch('dazzler.mediachecks.checkMS6')
    def test_valid_replaced_clip(self, cms6):
        cms6.return_value='anothervpid'
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        assert validClip({'entityType': 'clip', 'pid': 'apid', 'vpid': 'anothervpid'}, cc)

    def test_valid_bad_clip1(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        assert not validClip({'entityType': 'clip'}, cc)

    def test_valid_bad_clip2(self):
        cc = MagicMock()
        cc.getSid = MagicMock(return_value='asid')
        assert not validClip({'entityType': 'clip', 'pid': 'apid', 'vpid': 'apid'}, cc)

    @patch('dazzler.mediachecks.MediaServicesURI')
    @patch('dazzler.mediachecks.checkS3Uri')
    @patch('dazzler.mediachecks.validClip')
    def test_resolve_item(self, mock_validClip, mock_checkS3Uri, mock_MediaServicesURI):
        msuri = 's3://modav/vpid1.mp4'
        mock_validClip.return_value=False
        mock_MediaServicesURI.return_value = msuri
        mock_checkS3Uri.side_effect = [False, False, True, False, True, False, False, False, False]
        cc = MagicMock()
        cc.getMediaSelectorRedirectURL = MagicMock(return_value='http://x/')
        cc.getPlayBucket = MagicMock(return_value='x')
        cc.getSid = MagicMock(return_value='asid')
        s3 = MagicMock()
        assert resolveItem(cc, None, s3) is None
        assert resolveItem(cc, {'entityType':'other'}, s3) is None
        assert resolveItem(cc, {'entityType':'other', 'vpid': 'avpid'}, s3) is None
        assert resolveItem(cc, {'entityType':'clip', 'vpid': 'vpid0'}, s3) is None
        mock_validClip.return_value=True
        assert resolveItem(cc, {'entityType':'clip', 'vpid': 'vpid0'}, s3) == {'entityType':'clip', 'vpid': 'vpid0', 'url': 's3://x/vpid0.mp4'}
        assert resolveItem(cc, {'entityType':'clip', 'vpid': 'vpid1'}, s3) == {'entityType':'clip', 'vpid': 'vpid1', 'url': msuri}
        assert resolveItem(cc, {'entityType':'clip', 'vpid': 'vpid2'}, s3) == {'entityType':'clip', 'vpid': 'vpid2', 'url':'http://x/vpid2.mp4'}
        assert resolveItem(cc, {'entityType':'episode', 'vpid': 'vpid2'}, s3) == {'entityType':'clip', 'vpid': 'vpid2', 'url':'http://x/vpid2.mp4'}

    @responses.activate
    def test_media_services_uri(self):
        pv10 = {
            "drm":"none",
            "media_asset_id":"pips-pid-p0b124gw",
            "sequence_stamp":1635498928001000,
            "profile_id":"pips-map_id-av_pv10_pa4",
            "uri":"s3://livemodavdistributionresources-distributionbucket-182btg2y28f33/av_pv10_pa4/modav/bUnknown-d64df41a-a1fa-499f-9cec-06e53da9ae0c_m00116m0_pips-pid-m00116m0_1635498917461.mp4",
            "last_updated":"2021-10-29T09:15:33.756722Z"
        }
        pv13 = {
            "drm":"none",
            "media_asset_id":"pips-pid-p0b124gr",
            "sequence_stamp":1635498928001000,
            "profile_id":"pips-map_id-av_pv13_pa4",
            "uri":"s3://livemodavdistributionresources-distributionbucket-182btg2y28f33/av_pv13_pa4/modav/bUnknown-d64df41a-a1fa-499f-9cec-06e53da9ae0c_m00116m0_pips-pid-m00116m0_1635498914271.mp4",
            "last_updated":"2021-10-29T09:15:33.194463Z"
        }
        response = {
            "content_version_id":"pips-pid-m00116m0",
            "mediaset":"ws-partner-download",
            "media_assets":[pv10, pv13]
        }
        cc = MagicMock()
        cc.getSid.return_value = MagicMock(return_value='asid')
        vpid = 'm00116m0'
        responses.add(responses.GET, f"https://media-syndication.api.bbci.co.uk/assets/pips-pid-{vpid}",
                  json=response, status=200)
        response = {
            "content_version_id":"pips-pid-m00116m0",
            "mediaset":"ws-partner-download",
            "media_assets":[pv10]
        }
        responses.add(responses.GET, f"https://media-syndication.api.bbci.co.uk/assets/pips-pid-{vpid}",
                  json=response, status=200)
        response = {
            "content_version_id":"pips-pid-m00116m0",
            "mediaset":"ws-partner-download",
            "media_assets":[]
        }
        responses.add(responses.GET, f"https://media-syndication.api.bbci.co.uk/assets/pips-pid-{vpid}",
                  json=response, status=200)
        assert MediaServicesURI(cc, vpid) == pv13['uri']
        assert MediaServicesURI(cc, vpid) == pv10['uri']
        assert MediaServicesURI(cc, vpid) == None

    @responses.activate
    def test_media_services_uri_throw(self):
        cc = MagicMock()
        response = '<html>\r\n<head><title>400 No required SSL certificate was sent</title></head>\r\n<body bgcolor="white">\r\n<center><...nter>\r\n<center>No required SSL certificate was sent</center>\r\n<hr><center>nginx</center>\r\n</body>\r\n</html>\r\n'
        responses.add(responses.GET, f"https://media-syndication.api.bbci.co.uk/assets/pips-pid-avpid",
                  body=response, status=400)
        MediaServicesURI(cc, 'avpid')
        assert True

    def test_check_in_media_services_bucket_ok(self):
        uri = "s3://livemodavdistributionresources-distributionbucket-182btg2y28f33/av_pv13_pa4/modav/bUnknown-d64df41a-a1fa-499f-9cec-06e53da9ae0c_m00116m0_pips-pid-m00116m0_1635498914271.mp4"
        cc = MagicMock()
        s3 = MagicMock()
        vpid = 'm00116m0'
        assert checkS3Uri(cc, None, s3) == None
        assert checkS3Uri(cc, uri, s3) == uri
        s3 = MagicMock(head_object=MagicMock(side_effect = ClientError(MagicMock(), 'resource')))
        assert checkS3Uri(cc, uri, s3) == None
