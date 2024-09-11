import os
# import boto3
from isodate import parse_datetime, parse_duration
from log.logtypes import info
from datetime import datetime, timezone, timedelta
nownext_api = os.environ.get('NOWNEXT_API', 'live')
urls = {
  'test': 'https://jfayiszondlcqngo5vavioz6bq0ibxen.lambda-url.eu-west-1.on.aws/',
  'live': 'https://ypdjc6zbc5cnvth24lk3mm45sm0qtgps.lambda-url.eu-west-1.on.aws'
}
nownext_url = urls[nownext_api]
print(nownext_api, nownext_url)

def processEvent(invokeTime, event, account):
    # TODO get region name from event if possible!
    region_name = 'eu-west-1'
    eventTime = parse_datetime(event['time'])
    detail = event['detail']
    chanId = detail['channel_arn'].split(':')[-1]
    sid = detail["active_input_attachment_name"].split(' ')[0]
    action_name = detail['active_input_switch_action_name']

    info(sid, f"onswitchevent region_name {region_name} account {account} channel Id {chanId}")

    if 'pipeline' in detail and detail['pipeline'] != '0':
        info(sid, f'processEvent - message not from pipeline 0, ignoring')
        return        

    # response = table.get_item(Key={"sid": sid})
    # if 'Item' not in response:
    #     info(sid, f'channel is not defined in our configuration table, ignoring')
    #     return

    ml = cc.getML(region_name, account)
    try:
        cd = ml.describe_channel(ChannelId = chanId)
    except Exception as e:
        info(sid, f'onswitchevent - medialive client does not have permission to access channel {str(e)} in {region_name} in {account}')
        return

    if not cd['Name'].startswith('DazzlerV4 '):
        print(cd['Name'], 'is not a DazzlerV4 channel')
        return
    if not cd['Name'].startswith(f'DazzlerV4 {sid} '):
        info(sid, f"onswitchevent sid from event {sid} does not match channel name in Media live {cd['Name']}")
        return
    
    if ' sched ' in action_name or ' loop ' in action_name:
        print(f'We shall generate a new interstial file for this channel ')

def main(event, account):
    print(f'Message from account: {account}')
    invokeTime = parse_datetime(datetime.now(timezone.utc).isoformat())
    if 'detail-type' in event:
        if event['detail-type'] == 'MediaLive Channel Input Change':      
            processEvent(invokeTime, event, account)
    else:
        return None