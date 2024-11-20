from unittest.mock import MagicMock, patch
from dazzler.main import main

class TestMain:

    def test_main_event_long_duration_item(self):
          tableName = 'Dazzler-test'
          event = {
            "version": "0",
            "id": "d3dc8161-82ba-572a-5918-d103e0bac96d",
            "detail-type": "MediaLive Channel Input Change",
            "source": "aws.medialive",
            "account": "576677253489",
            "time": "2024-11-20T14:48:40Z",
            "region": "eu-west-1",
            "resources": [
                "arn:aws:medialive:eu-west-1:576677253489:channel:332295"
            ],
            "detail": {
                "pipeline": "0",
                "channel_arn": "arn:aws:medialive:eu-west-1:576677253489:channel:332295",
                "message": "Input switch event on pipeline",
                "active_input_attachment_name": "steve_sid dynamic",
                "active_input_switch_action_name": "20241120T144840.240Z PT10M sched m001kyv1"
            }
            }
          assert main(event, tableName) is not None

    def test_main_event_short_duration_item(self):
          tableName = 'Dazzler-test'
          event = {
            "version": "0",
            "id": "d3dc8161-82ba-572a-5918-d103e0bac96d",
            "detail-type": "MediaLive Channel Input Change",
            "source": "aws.medialive",
            "account": "576677253489",
            "time": "2024-11-20T14:48:40Z",
            "region": "eu-west-1",
            "resources": [
                "arn:aws:medialive:eu-west-1:576677253489:channel:332295"
            ],
            "detail": {
                "pipeline": "0",
                "channel_arn": "arn:aws:medialive:eu-west-1:576677253489:channel:332295",
                "message": "Input switch event on pipeline",
                "active_input_attachment_name": "steve_sid dynamic",
                "active_input_switch_action_name": "20241120T144840.240Z PT6M sched m001kyv1"
            }
            }
          res = main(event, tableName)
          assert res['statusCode'] == 203
    
    def test_main_event_item_not_parsed(self):
          tableName = 'Dazzler-test'
          event = {
            "version": "0",
            "id": "d3dc8161-82ba-572a-5918-d103e0bac96d",
            "detail-type": "MediaLive Channel Input Change",
            "source": "aws.medialive",
            "account": "576677253489",
            "time": "2024-11-20T14:48:40Z",
            "region": "eu-west-1",
            "resources": [
                "arn:aws:medialive:eu-west-1:576677253489:channel:332295"
            ],
            "detail": {
                "pipeline": "0",
                "channel_arn": "arn:aws:medialive:eu-west-1:576677253489:channel:332295",
                "message": "Input switch event on pipeline",
                "active_input_attachment_name": "steve_sid dynamic",
                "active_input_switch_action_name": "Initial Channel Input"
            }
            }
          res = main(event, tableName)
          assert res['statusCode'] == 203  
        
