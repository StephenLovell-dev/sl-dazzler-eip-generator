from os import environ
from unittest.mock import MagicMock
from medialivehelpers.motiongraphics import *
class TestMain:
 
    def test_s3ToHttpPath(self):
        assert s3ToHttpPath(None) is None

    def test_motionGraphicsOverlayForItem(self):
        environ['AWS_REGION'] = 'eu-west-1'
        cc = MagicMock()
        item = {
            'graphic_duration':'PT0S', 'start': '2023-06-07T00:00:00Z',
            'url': 'https://a/b',
        }
        assert motionGraphicsOverlayForItem(cc, item) is not None

    def test_fixedMotionGraphicsOverlayForItem(self):
        cc = MagicMock()
        item = {
            'graphic_duration':'PT0S', 'start': '2023-06-07T00:00:00Z',
            'url': 'https://a/b',
        }
        fixedMotionGraphicsOverlayForItem(cc, item) is not None
