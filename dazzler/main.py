import boto3
import json
from datetime import timedelta
from dazzler.channelconfiguration import ChannelConfiguration
from medialivehelpers.action import startAndDurationFromActionName
from medialivehelpers.schedule import Schedule as MediaLiveSchedule

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
            if 'account' in event:
                account = event['account']
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
                    msg = 'We need to generate an upcoming!'
                    return {
                        'statusCode': 203,
                        'body': json.dumps(msg)
                    } 
                            
    return cantProcess(msg)