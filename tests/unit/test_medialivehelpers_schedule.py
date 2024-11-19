from botocore.exceptions import ClientError
from unittest.mock import MagicMock
from medialivehelpers.schedule import Schedule

def describe_results(**kwargs):
    if 'NextToken' in kwargs:
        return {'ScheduleActions': []}
    else:
        return {'ScheduleActions': [], 'NextToken': 'atoken'}

class TestMain:

    def test_add(self):
        client = MagicMock()
        s = Schedule('asid', 'achannelid', client)
        assert s.add([])

    def test_add_catch(self):
        error = {
            'Error': {
                'Code':'UnprocessableEntityException', 
                'Message': "\"actionName: 2021-10-04T14'30'58Z PT31M world...05 error: Cannot schedule actionName=2021-10-04T14:30:58Z PT31M world...05 with action time=2021-10-04T14:30:58Z, missed deadline of 15 seconds\""
            }
        }
        client = MagicMock()
        client.batch_update_schedule = MagicMock(side_effect = ClientError(error, 'batch_update_schedule'))
        s = Schedule('asid', 'achannelid', client) 
        assert not s.add([])

    def test_add_throw(self):
        client = MagicMock()
        client.batch_update_schedule = MagicMock(side_effect = ClientError({'Error':{'Code':'OtherException'}}, 'batch_update_schedule'))
        try:
            s = Schedule('asid', 'achannelid', client) 
            s.add([])
        except:
            pass

    def test_replace(self):
        client = MagicMock()
        client.batch_update_schedule = MagicMock()
        s = Schedule('asid', 'achannelid', client)
        assert s.replace([], [])
        client.batch_update_schedule.assert_called_once_with(
            ChannelId='achannelid',
            Creates={ 'ScheduleActions': [] },
            Deletes={
                'ActionNames': []
            }
        )

    def test_replace_catch(self):
        error = {
            'Error': {
                'Code':'UnprocessableEntityException', 
                'Message': "\"actionName: 2021-10-04T14'30'58Z PT31M world...05 error: Cannot schedule actionName=2021-10-04T14:30:58Z PT31M world...05 with action time=2021-10-04T14:30:58Z, missed deadline of 15 seconds\""
            }
        }
        client = MagicMock()
        client.batch_update_schedule = MagicMock(side_effect = ClientError(error, 'batch_update_schedule'))
        s = Schedule('asid', 'achannelid', client) 
        assert not s.replace([], [])

    def test_replace_throw(self):
        client = MagicMock()
        client.batch_update_schedule = MagicMock(side_effect = ClientError({'Error':{'Code':'OtherException'}}, 'batch_update_schedule'))
        try:
            s = Schedule('asid', 'achannelid', client) 
            s.replace([], [])
        except:
            pass

    def test_delete_items(self):
        client = MagicMock()
        s = Schedule('asid', 'achannelid', client)
        assert s.delete_items([]) is None

    def test_delete_items_throw(self):
        client = MagicMock()
        client.batch_update_schedule = MagicMock(side_effect = ClientError(MagicMock(), 'batch_update_schedule'))
        s = Schedule('asid', 'achannelid', client)
        assert s.delete_items([]) is None

    def test_describe(self):
        client = MagicMock()
        client.describe_schedule = MagicMock(side_effect = describe_results)
        s = Schedule('asid', 'achannelid', client)
        assert s.describe() is not None

    def test_describe_throw(self):
        client = MagicMock()
        client.describe_schedule = MagicMock(side_effect = ClientError(MagicMock(), 'batch_update_schedule'))
        s = Schedule('asid', 'achannelid', client)
        assert s.describe() is None
