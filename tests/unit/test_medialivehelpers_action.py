from medialivehelpers.action import Action, actionName, truncate_middle
from isodate import parse_date
from datetime import timedelta

class TestMain:

    def test_constructor(self):
        date = parse_date('2021-06-10')
        a = Action('', date)
        assert a.name() == ''
        name = "2021-06-10T00'00'00Z b c"
        a = Action(name, date)
        assert a.name() == name

    def test_truncate_middle(self):
        assert truncate_middle('abc', 5) == 'abc'
        assert truncate_middle('abcdefgh', 5) == 'a...h'

    def test_equality(self):
        date = parse_date('2021-06-10')
        name = "2021-06-10T00'00'00Z b c"
        a = Action(name, date)
        b = Action(name, date)
        assert b == a
        b = Action("2021-06-10T00'00'00Z b d", date)
        assert b != a
        b = Action("2021-06-10T00'10'00Z b d", date)
        assert b != a
        b = Action("2021-06-10T00'00'00Z a c", date+timedelta(minutes=10))
        assert b != a

    def test_action_name(self):
        assert actionName(None) == ''
        assert actionName({'origin': 'schedule', 'duration': 'PT10S', 'start': '2021-06-29T09:49:32Z', 'stream': 'x', 'vpid': 'avpid'}) == "2021-06-29T09'49'32Z PT10S x avpid"
        assert actionName({'origin': 'slate', 'duration': 'PT10S', 'start': '2021-06-29T09:49:32Z' }) == "2021-06-29T09'49'32Z PT10S slate"
        assert actionName({'origin': 'other', 'duration': 'PT10S', 'start': '2021-06-29T09:49:32Z' }) == "2021-06-29T09'49'32Z PT10S othe"
        assert actionName({'origin': 'schedule', 'duration': 'PT10S', 'start': '2021-06-29T09:49:32Z' }) == "2021-06-29T09'49'32Z PT10S sched"

    def test_action_new_graphics(self):
        item = {
            'origin': 'schedule', 
            'start': '2022-03-24T14:29:00Z', 
            'end': '2022-03-24T15:13:55Z', 
            'live': False, 
            'rating': 'M - Drug Use, Coarse Language', 
            'duration': 'PT44M55.12S', 
            'vpid': 'p08p014t', 
            'entityType': 'episode', 
            'pid': 'p0891fp3', 
            'url': 's3://ws-dazzler-tv-live/p08p014t.mp4'
        }
        assert actionName(item) == "2022-03-24T14'29'00Z PT44M55S sched p08p014t c,5i"
