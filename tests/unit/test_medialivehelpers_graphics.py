from unittest.mock import MagicMock
from medialivehelpers.graphics import graphicAction, graphicsOverlayForItem

class TestMain:

    def test_graphic_action(self):
        cc = MagicMock(
            getSid = MagicMock(return_value='x'),
            getPlayBucket = MagicMock(return_value='x'),
            getAuthorisation = MagicMock(return_value='agerating'),
            getAgeratingImageDimensions = MagicMock(return_value={ "width": 427, "height": 166, "left": 0, "top": 15 }),
        )
        start = '2021-01-01T00:00:00:00Z'
        wanted = {
            "ActionName": "2021-01-01T00'00'00'00Z PT25S graphic",
            "ScheduleActionStartSettings": {
                'ImmediateModeScheduleActionStartSettings': {}
            },
            "ScheduleActionSettings": {
                "StaticImageActivateSettings": {
                "Image": {
                    "Uri": 's3://x/graphics/agerating/TV-14.png'
                },
                "Layer": 7,
                "ImageX": 0,
                "ImageY": 15,
                "Width": 427,
                "Height": 166,
                "Duration": 22000,
                "FadeOut": 3000
                }
            }
        }
        assert graphicAction(cc, 'TV-14', 'av_pv44_pa4', start) == wanted
        assert graphicAction(cc, 'TV-14', 'av_pv43_pa4', start) == wanted
        r = graphicAction(cc, 'TV-14', 'av_pv14_pa4', start)
        i = r['ScheduleActionSettings']['StaticImageActivateSettings']
        assert i['ImageX'] == 0
        assert i['ImageY'] == 10
        assert i['Width'] == 284
        assert i['Height'] == 110
        r = graphicAction(cc, 'TV-14', 'av_pv42_pa4', start)
        i = r['ScheduleActionSettings']['StaticImageActivateSettings']
        assert i['ImageX'] == 0
        assert i['ImageY'] == 8
        assert i['Width'] == 160
        assert i['Height'] == 88
        r = graphicAction(cc, 'TV-14', 'av_pv10_pa4', start)
        i = r['ScheduleActionSettings']['StaticImageActivateSettings']
        assert i['ImageX'] == 0
        assert i['ImageY'] == 7
        assert i['Width'] == 213
        assert i['Height'] == 83
        r = graphicAction(cc, 'TV-14', 'av_pv13_pa4', start)
        i = r['ScheduleActionSettings']['StaticImageActivateSettings']
        assert i['ImageX'] == 0
        assert i['ImageY'] == 7
        assert i['Width'] == 213
        assert i['Height'] == 83


    def test_graphics_overlay_for_item(self):
        cc = MagicMock(
            getPlayBucket = MagicMock(return_value='x'),
            getAuthorisation = MagicMock(return_value='agerating'),
            getAgeratingImageDimensions = MagicMock(return_value={ "width": 427, "height": 166, "left": 0, "top": 15 }),
            )
        item = {
            'start': '2021-01-01T00:00:00:00Z',
            'duration': 'PT1H',
        }
        assert graphicsOverlayForItem(cc, item) is None
        item = {
            'start': '2021-01-01T00:00:00:00Z',
            'duration': 'PT1H',
            'rating': 'TV-14',
            'profile': 'av_pv44_pa4'
        }
        assert graphicsOverlayForItem(cc, item) == {
            "ActionName": "2021-01-01T00'00'00'00Z PT25S graphic",
            "ScheduleActionStartSettings": {
                'ImmediateModeScheduleActionStartSettings': {}
            },
            "ScheduleActionSettings": {
                "StaticImageActivateSettings": {
                "Image": {
                    "Uri": 's3://x/graphics/agerating/TV-14.png'
                },
                "Layer": 7,
                "ImageX": 0,
                "ImageY": 15,
                "Width": 427,
                "Height": 166,
                "Duration": 22000,
                "FadeOut": 3000
                }
            }
        }

    def test_graphics_overlay_for_item_au(self):
        cc = MagicMock(
            getPlayBucket = MagicMock(return_value='x'),
            getAuthorisation = MagicMock(return_value='britbox_au'),
            getAgeratingImageDimensions = MagicMock(return_value={ "width": 527, "height": 166, "left": 0, "top": 15 }),
        )
        item = {
            'start': '2021-01-01T00:00:00:00Z',
            'duration': 'PT1H',
        }
        assert graphicsOverlayForItem(cc, item) is None
        item = {
            'start': '2021-01-01T00:00:00:00Z',
            'duration': 'PT1H',
            'rating': 'M - Coarse Language, Mature Themes',
            'profile': 'av_pv44_pa4'
        }
        assert graphicsOverlayForItem(cc, item) == {
            "ActionName": "2021-01-01T00'00'00'00Z PT25S graphic",
            "ScheduleActionStartSettings": {
                'ImmediateModeScheduleActionStartSettings': {}
            },
            "ScheduleActionSettings": {
                "StaticImageActivateSettings": {
                "Image": {
                    "Uri": 's3://x/graphics/britbox_au/M - Coarse Language, Mature Themes.png'
                },
                "Layer": 7,
                "ImageX": 0,
                "ImageY": 15,
                "Width": 527,
                "Height": 166,
                "Duration": 22000,
                "FadeOut": 3000
                }
            }
        }
