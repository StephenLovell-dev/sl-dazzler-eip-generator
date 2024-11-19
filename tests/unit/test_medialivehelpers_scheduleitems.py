from medialivehelpers.action import Action
from medialivehelpers.schedule_items import ScheduleItems

class TestMain:

    def test_empty(self):
        assert ScheduleItems(None).empty()
        assert ScheduleItems([]).empty()
        assert not ScheduleItems([{'ScheduleActionSettings': {'InputSwitchSettings':{}}}]).empty()

    def test_completely_empty(self):
        assert ScheduleItems(None).completelyEmpty()
        assert ScheduleItems([]).completelyEmpty()
        assert not ScheduleItems([{'ScheduleActionSettings': {}}]).completelyEmpty()

    def test_last_switch(self):
        assert ScheduleItems(None).lastSwitch() is None
        assert ScheduleItems([]).lastSwitch() is None
        assert ScheduleItems([{'ActionName':'1', 'ScheduleActionSettings': {'InputSwitchSettings':{}}}]).lastSwitch()['ActionName'] == '1'
        assert ScheduleItems([
            {'ActionName':'1', 'ScheduleActionSettings': {'InputSwitchSettings':{}}},
            {'ActionName': '2', 'ScheduleActionSettings': {'InputSwitchSettings':{}}}
        ]).lastSwitch()['ActionName'] == '2'


    def test_last_any(self):
        assert ScheduleItems(None).lastAny() is None
        assert ScheduleItems([]).lastAny() is None
        assert ScheduleItems([{'ActionName':'1', 'ScheduleActionSettings': {}}]).lastAny()['ActionName'] == '1'
        assert ScheduleItems([
            {'ActionName':'1', 'ScheduleActionSettings': {}},
            {'ActionName': '2', 'ScheduleActionSettings': {}}
        ]).lastAny()['ActionName'] == '2'


    def test_after(self):
        name = "2021-06-26T16'10'00"
        s = ScheduleItems([
            {'ActionName':name,'ScheduleActionSettings': {'InputSwitchSettings':{}}}
        ])
        assert s.after(Action(name, None)).empty