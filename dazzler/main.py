import boto3
import json
from datetime import timedelta
from dazzler.channelconfiguration import ChannelConfiguration
from medialivehelpers.action import startAndDurationFromActionName
from medialivehelpers.schedule import Schedule as MediaLiveSchedule
from dazzler.api import createUpcoming


def extractChannelSidFromInputName(inputName):
    elements=inputName.split(' ')
    if len(elements) > 0:
        return elements[0]
    return None

def extractChannelIdFromArn(channelArn):
    elements = channelArn.split(':')
    if len(elements) > 0:
        return elements[len(elements) -1]
    return None

def cantProcess(msg):
    print(msg)
    return {
        'statusCode': 203,
        'body': json.dumps(msg)
    }   

def main(event, tableName):
    msg = 'not enough info to process!'
    if 'detail' in event:
        detail = event['detail']
        if 'active_input_switch_action_name' in detail:
            action = detail['active_input_switch_action_name']
            start, duration = startAndDurationFromActionName(action)
            if start == None or duration == None:
                return cantProcess(f'Start and duration not found exiting! {action}')
            if duration <= timedelta(minutes=6):
                return cantProcess(f'Item duration less than min duration, exiting! {action}')
            if 'region' in event:
                region_name = event['region']
            if 'channel_arn' in detail:
                channelId = extractChannelIdFromArn(detail['channel_arn'])
            if 'active_input_attachment_name' in detail:
                sid = extractChannelSidFromInputName(detail['active_input_attachment_name'])  
            if len(sid) > 0 and len(region_name) > 0:
                dynamodb = boto3.resource('dynamodb', region_name=region_name)
                table = dynamodb.Table(tableName)
                cc = ChannelConfiguration(sid, table)
                if cc.getShouldGenerateUpcoming():
                    cc.setChannelId(channelId)
                    msg = 'We need to generate an upcoming!'
                    result = createUpcoming(cc, action, region_name)
                    if 'next' in result:
                        print(sid, result)
                        return {
                            'statusCode': 200,
                            'body': json.dumps(result)
                        } 
                    msg = result['status']
                            
    return cantProcess(msg)

if __name__ == '__main__':
    # Local testing
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
                "arn:aws:medialive:eu-west-1:576677253489:channel:4789478"
            ],
            "detail": {
                "pipeline": "0",
                "channel_arn": "arn:aws:medialive:eu-west-1:576677253489:channel:4789478",
                "message": "Input switch event on pipeline",
                "active_input_attachment_name": "steve_sid dynamic",
                "active_input_switch_action_name": "20241121T155840.240Z PT10M sched m001kyv1"
            }
            }
    main(event, tableName)