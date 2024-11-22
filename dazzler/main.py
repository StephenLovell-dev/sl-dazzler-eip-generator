import array
import boto3
import json
import os
from datetime import timedelta
from dazzler.channelconfiguration import ChannelConfiguration
from medialivehelpers.action import startAndDurationFromActionName
from medialivehelpers.schedule import Schedule as MediaLiveSchedule
from dazzler.api import createUpcoming

def writeUpcomingFile(sid, data):
    client = boto3.client('s3')
    parts = os.environ["CHANNEL_FILES_DESTINATION"].replace('s3://','').split('/')
    bucket = parts[0]
    key = os.environ["CHANNEL_FILES_DESTINATION"].replace(f"s3://{parts[0]}/",'') + f"{sid}.json"
    print(bucket, key)
    client.put_object(Body=json.dumps(data), Bucket=bucket, Key=key)

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
                        writeUpcomingFile(sid, result)
                        return {
                            'statusCode': 200,
                            'body': json.dumps(result)
                        } 
                    msg = result['status']
                            
    return cantProcess(msg)

if __name__ == '__main__':
    # Local testing
    # ES_HOST
    # test: search-test-pws-es-exozet-hyouszlg2ugjrx2qe4djugyqtu.eu-west-1.es.amazonaws.com
    # live: vpc-live-pws-es-nkhq5ogzg2xgystvbp2drojivi.eu-west-1.es.amazonaws.com
    # CHANNEL_FILES_DESTINATION
    # test: s3://ws-dazzler-assets-test/steve_sid/
    os.environ["ES_HOST"]='search-test-pws-es-exozet-hyouszlg2ugjrx2qe4djugyqtu.eu-west-1.es.amazonaws.com'
    os.environ["CHANNEL_FILES_DESTINATION"]='s3://ws-dazzler-assets-test/steve_sid/'
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