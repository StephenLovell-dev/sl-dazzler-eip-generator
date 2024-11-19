from unittest.mock import patch
from medialivehelpers.action import truncate_middle
from medialivehelpers.actions import findInput, fixedAction, immediateAction, followAction, someAction

cd = {
    'InputAttachments': [
        { 'InputAttachmentName': 'the stream 1 input' },
        { 'InputAttachmentName': 'a dynamic input' },
        { 'InputAttachmentName': 'a slate input' },
    ],
    'Name': 'a dazzler channel'
}

class TestMain:

    def test_truncate_middle(self):
        assert truncate_middle('abcdefghijk', 7) == 'ab...jk'

    def test_find_input_none(self):
        assert findInput(None, None) is None
        assert findInput(None, {}) is None
        assert findInput({}, {'InputAttachments': []}) is None

    def test_find_input(self):
        assert findInput({'url': 'http://x/'}, cd) == 'a dynamic input'
        assert findInput({'stream': 'stream 1'}, cd) == 'the stream 1 input'
        assert findInput({}, cd) == 'a slate input'

    @patch('medialivehelpers.actions.findInput')
    def test_some_action_no_ref(self, findInput):
        assert someAction({'origin':'schedule', 'start': '2016-06-26T16:00:00Z', 'url': '', 'stream': 'w'}, cd) is not None

    def test_fixed_action(self):
        assert fixedAction({ 'origin': 'schedule', 'start': '2016-06-26T16:00:00Z', 'url': ''}, cd) is not None

    def test_immediate_action(self):
        assert immediateAction({ 'origin': 'schedule', 'start': '2016-06-26T16:00:00Z', 'url': ''}, cd) is not None
    
    def test_follow_action(self):
        assert followAction(
            { 'origin': 'schedule', 'start': '2016-06-26T16:00:00Z', 'url': ''}, 
            cd,
            'a'
        ) is not None


    def test_immediate_action2(self):
        item = {
            'origin': 'schedule', 
            'start': '2022-03-24T15:18:48Z', 
            'end': '2022-03-24T16:04:18Z', 
            'live': False, 
            'rating': 'M - Coarse Language, Mature Themes', 
            'duration': 'PT45M29.88S', 
            'vpid': 'p08p0140', 
            'entityType': 'episode', 
            'pid': 'p0891fnx', 
            'url': 's3://ws-dazzler-tv-live/p08p0140.mp4'
            }
        cd = {
            'ResponseMetadata': {'RequestId': '5bf0672b-aaac-45e1-a64b-0574796c6810', 'HTTPStatusCode': 200, 'HTTPHeaders': {'content-type': 'application/json', 'content-length': '5680', 'connection': 'keep-alive', 'date': 'Thu, 24 Mar 2022 15:18:53 GMT', 'x-amzn-requestid': '5bf0672b-aaac-45e1-a64b-0574796c6810', 'access-control-allow-origin': '*', 'access-control-allow-headers': '*,Authorization,Date,X-Amz-Date,X-Amz-Security-Token,X-Amz-Target,content-type,x-amz-content-sha256,x-amz-user-agent,x-amzn-platform-id,x-amzn-trace-id', 'x-amz-apigw-id': 'PfrKpEPyDoEFYmg=', 'access-control-allow-methods': 'GET,HEAD,PUT,POST,DELETE,OPTIONS', 'access-control-expose-headers': 'x-amzn-errortype,x-amzn-requestid,x-amzn-errormessage,x-amzn-trace-id,x-amz-apigw-id,date', 'x-amzn-trace-id': 'Root=1-623c8bdd-2733e64327bdb8574c08f216;Sampled=0', 'access-control-max-age': '86400', 'x-cache': 'Miss from cloudfront', 'via': '1.1 8313bbb5b34d1ea0742b64ffbb83b692.cloudfront.net (CloudFront)', 'x-amz-cf-pop': 'DUB56-P1', 'x-amz-cf-id': '7K2VQdkI8rl7-cK8r6JdCGghPfFf_KHLERW5o5jqLSJIvqvss5M2lQ=='}, 'RetryAttempts': 0},
            'Arn': 'arn:aws:medialive:eu-west-1:205979497597:channel:1098764', 
            'ChannelClass': 'SINGLE_PIPELINE', 
            'Destinations': [
                {'Id': 'destination1', 'MediaPackageSettings': [], 'Settings': [{'StreamName': 'thwrcbgw', 'Url': 'rtmp://in.test.bbcav.uk/live'}]}], 'EgressEndpoints': [{'SourceIp': '52.208.141.108'}], 'EncoderSettings': {'AudioDescriptions': [{'AudioSelectorName': 'Audio1', 'AudioTypeControl': 'FOLLOW_INPUT', 'CodecSettings': {'AacSettings': {'Bitrate': 192000, 'CodingMode': 'CODING_MODE_2_0', 'InputType': 'NORMAL', 'Profile': 'LC', 'RateControlMode': 'CBR', 'RawFormat': 'NONE', 'SampleRate': 48000, 'Spec': 'MPEG4'}}, 'LanguageCodeControl': 'FOLLOW_INPUT', 'Name': 'audio_1'}], 'CaptionDescriptions': [], 'MotionGraphicsConfiguration': {'MotionGraphicsInsertion': 'ENABLED', 'MotionGraphicsSettings': {'HtmlMotionGraphicsSettings': {}}}, 'OutputGroups': [{'Name': 'RTMPGroup', 'OutputGroupSettings': {'RtmpGroupSettings': {'AdMarkers': [], 'AuthenticationScheme': 'COMMON', 'CacheFullBehavior': 'DISCONNECT_IMMEDIATELY', 'CacheLength': 30, 'CaptionData': 'ALL', 'RestartDelay': 15}}, 'Outputs': [{'AudioDescriptionNames': ['audio_1'], 'CaptionDescriptionNames': [], 'OutputName': 'output_1', 'OutputSettings': {'RtmpOutputSettings': {'CertificateMode': 'VERIFY_AUTHENTICITY', 'ConnectionRetryInterval': 2, 'Destination': {'DestinationRefId': 'destination1'}, 'NumRetries': 10}}, 'VideoDescriptionName': 'video_1'}]}], 'TimecodeConfig': {'Source': 'EMBEDDED'}, 'VideoDescriptions': [{'CodecSettings': {'H264Settings': {'AdaptiveQuantization': 'MEDIUM', 'AfdSignaling': 'NONE', 'Bitrate': 4000000, 'ColorMetadata': 'INSERT', 'EntropyEncoding': 'CABAC', 'FlickerAq': 'ENABLED', 'FramerateControl': 'SPECIFIED', 'FramerateDenominator': 1, 'FramerateNumerator': 25, 'GopBReference': 'DISABLED', 'GopClosedCadence': 1, 'GopNumBFrames': 2, 'GopSize': 90, 'GopSizeUnits': 'FRAMES', 'Level': 'H264_LEVEL_AUTO', 'LookAheadRateControl': 'MEDIUM', 'NumRefFrames': 1, 'ParControl': 'SPECIFIED', 'Profile': 'MAIN', 'RateControlMode': 'CBR', 'ScanType': 'PROGRESSIVE', 'SceneChangeDetect': 'ENABLED', 'SpatialAq': 'ENABLED', 'SubgopLength': 'FIXED', 'Syntax': 'DEFAULT', 'TemporalAq': 'ENABLED', 'TimecodeInsertion': 'DISABLED'}}, 'Height': 1080, 'Name': 'video_1', 'RespondToAfd': 'NONE', 'ScalingBehavior': 'DEFAULT', 'Sharpness': 50, 'Width': 1920}]}, 
                'Id': '1098764', 
                'InputAttachments': [
                    {'InputAttachmentName': 'britbox_tv_au_za slate', 'InputId': '9386046', 'InputSettings': {'AudioSelectors': [], 'CaptionSelectors': [], 'DeblockFilter': 'DISABLED', 'DenoiseFilter': 'DISABLED', 'FilterStrength': 1, 'InputFilter': 'AUTO', 'SourceEndBehavior': 'CONTINUE'}}, 
                    {'InputAttachmentName': 'britbox_tv_au_za sport_stream_11 live', 'InputId': '2817332', 'InputSettings': {'AudioSelectors': [], 'CaptionSelectors': [], 'NetworkInputSettings': {'HlsInputSettings': {'Bandwidth': 5, 'BufferSegments': 5, 'Retries': 5, 'RetryInterval': 5}}}}, 
                    {'InputAttachmentName': 'britbox_tv_au_za sport_stream_12 live', 'InputId': '6828400', 'InputSettings': {'AudioSelectors': [], 'CaptionSelectors': [], 'NetworkInputSettings': {'HlsInputSettings': {'Bandwidth': 5, 'BufferSegments': 5, 'Retries': 5, 'RetryInterval': 5}}}}, 
                    {'InputAttachmentName': 'britbox_tv_au_za dynamic', 'InputId': '877744', 'InputSettings': {'AudioSelectors': [], 'CaptionSelectors': [], 'DeblockFilter': 'DISABLED', 'DenoiseFilter': 'DISABLED', 'FilterStrength': 1, 'InputFilter': 'AUTO', 'SourceEndBehavior': 'CONTINUE'}}
                ],
            'InputSpecification': {'Codec': 'AVC', 'MaximumBitrate': 'MAX_10_MBPS', 'Resolution': 'HD'}, 
            'LogLevel': 'DISABLED', 
            'Name': 'DazzlerV4 britbox_tv_au_za 1', 
            'PipelineDetails': [{'ActiveInputAttachmentName': 'britbox_tv_au_za dynamic', 'ActiveInputSwitchActionName': "2022-03-24T14'56'50Z PT45M30S sched p08p0140 6,5i", 'ActiveMotionGraphicsActionName': '', 'ActiveMotionGraphicsUri': '', 'PipelineId': '0'}], 
            'PipelinesRunningCount': 1, 
            'RoleArn': 'arn:aws:iam::205979497597:role/MediaLiveAccessRole', 
            'State': 'RUNNING', 
            'Tags': {'customer': 'dummybritbox'}
            }
        assert immediateAction(item, cd) == {
            'ActionName': "2022-03-24T15'18'48Z PT45M30S sched p08p0140 7,5i", 
            'ScheduleActionSettings': {
                'InputSwitchSettings': {
                    'InputAttachmentNameReference': 'britbox_tv_au_za dynamic',
                    'UrlPath': ['s3://ws-dazzler-tv-live/p08p0140.mp4'],
                }
            },
            'ScheduleActionStartSettings': {'ImmediateModeScheduleActionStartSettings': {}}
        }

