import os
import boto3
import requests
import json
import requests
from botocore.exceptions import ClientError
from log.logtypes import info

def itemIsGraphic(item):
    return item['entityType'] == 'graphic'

def itemIsLive(cc, item):
    if 'live' in item:
        return item['live']
    if 'entityType' in item:
        return item['entityType'] == 'live'
    return False

def suitable(od):
    return od['broadcaster']['link']['sid'] == 'video_streaming_noprot_1732'

def getReplacementVersion(cc, pid, vpid):
    try:
        #assume role
        sts_client = boto3.client('sts')
        appw = cc.getAppwData()
        response = sts_client.assume_role(
            RoleArn=appw['RoleArn'],
            RoleSessionName=appw['RoleSessionName']
        )
        s3_client = boto3.client(
                's3',
                aws_access_key_id=response['Credentials']['AccessKeyId'],
                aws_secret_access_key=response['Credentials']['SecretAccessKey'],
                aws_session_token=response['Credentials']['SessionToken'],
            )
        response = s3_client.get_object(
            Bucket=appw['Bucket'],
            Key=f"{appw['Prefix']}/availability/clip/pid.{pid}"
        )['Body'].read().decode('utf-8')
        data = json.loads(response)
        for av in data['programme_availability']['available_versions']['available_version']:
            if av['version']['pid'] == vpid:
                continue
            for od in av['availabilities']['ondemand']:
                if suitable(od):
                    return av['version']['pid']
    except Exception as e:
        print('error in getReplacementVersion', e)
        return None

def checkMediaSelectorResult(r):
    if not 'media' in r:
        return False
    if len(r['media']) == 0:
        return False
    media = r['media'][0]
    if 'bitrate' not in media or int(media['bitrate']) < 800:
        return False
    if 'type' not in media or media['type'] < 'video/mp4':
        return False
    if 'width' not in media or int(media['width']) < 640:
        return False
    if 'connection' not in media or len(media['connection']) == 0:
        return False
    connection = media['connection'][0]
    if 'transferFormat' not in connection or connection['transferFormat'] != 'plain':
        return False
    return True

def checkMS6(cc, pid, vpid):
    url = cc.getMediaSelectorSelectURL()
    if url is None:
        return True
    input = requests.get(f'{url}{vpid}.mp4')
    if input.status_code >= 400:
        print(cc.getSid(), f"we don't have a video for {vpid}")
        replacement = getReplacementVersion(cc, pid, vpid)
        print(cc.getSid(), f"replacement version is {replacement}")
        if replacement is not None:
            return replacement
        else:
            return False
    else:
        r = checkMediaSelectorResult(input.json())
        if not r:
            print(cc.getSid(), f'clip with {vpid} is not suitable')
            return False
        return True

def dazzlerURI(cc, vpid):
    return f"s3://{cc.getPlayBucket()}/{vpid}.mp4"

def MediaServicesURI(cc, vpid):
    api_key = os.environ.get('MEDIA_SYNDICATION_API_KEY')
    url = f"https://media-syndication.api.bbci.co.uk/assets/pips-pid-{vpid}"
    try:
        r = requests.get(
            url,
            params = {'mediaset': 'ws-partner-download', 'api_key': api_key},
            cert=('cosmos/client.crt', 'cosmos/client.key')
        )
        assets = r.json()['media_assets']
        ma = [i['uri'] for i in assets if i['profile_id']=='pips-map_id-av_pv13_pa4']
        if len(ma)==0:
            ma = [i['uri'] for i in assets if i['profile_id']=='pips-map_id-av_pv10_pa4']
        if len(ma)==0:
            return None
        return ma[0]
    except Exception as e:
        print('error in MediaServicesURI', e)
        return None 

def checkInSomeBucket(cc, bucket, key, s3):
    try:
        s3.head_object(
            Bucket=bucket,
            Key=key,
        )
        return True
    except ClientError as e:
        return False

def checkS3Uri(cc, uri, s3):
    if uri is None:
        return None
    path = uri.split('/')
    path.pop(0)
    path.pop(0)
    bucket = path.pop(0)
    key = '/'.join(path)
    if checkInSomeBucket(cc, bucket, key, s3):
        return uri
    return None

def validClip(item, cc):
    if 'pid' in item and 'vpid' in item:
        itemStatus = False
        try:
            itemStatus = checkMS6(cc, item['pid'], item['vpid'])
        except Exception as e:
            print(cc.getSid(), 'checkMS6', e)
        if itemStatus == True:
            return True
        elif itemStatus:
            info(cc.getSid(), f"revoked item {item['vpid']} with replacement {itemStatus}")
            item['vpid'] = itemStatus
            return True
        else:
            info(cc.getSid(), f"unusable clip {item['pid']} {item['vpid']}")
            return False
    else:
        info(cc.getSid(), f"can't validate input for item {item}")
        return False
# {'origin': 'schedule', 'start': '2022-01-17T15:01:00Z', 'end': '2022-01-17T15:06:00Z', 'live': True, 'stream': 'abcde1', 'duration': 'PT5M'} 
def resolveItem(cc, item, s3):
    if item is None:
        return None
    if itemIsLive(cc, item):
        return item
    if itemIsGraphic(item):
        if 'url' in item and checkS3Uri(cc, item['url'], s3):
            info(cc.getSid(), f"good {item['entityType']} with url {item['url']}")
            return item
    if 'vpid' not in item or 'entityType' not in item or item['entityType'] not in ['clip', 'episode', 'graphic']:
        return None
    elif 'url' in item and checkS3Uri(cc, item['url'], s3):
            info(cc.getSid(), f"good {item['entityType']} with url {item['url']}")
            return item
    uri = dazzlerURI(cc, item['vpid'])
    info(cc.getSid(), f"trying {item['entityType']} with url {uri}")
    if checkS3Uri(cc, uri, s3):       
        item['url'] = uri
        info(cc.getSid(), f"good {item['entityType']} with url {item['url']}")
        return item
    uri = MediaServicesURI(cc, item['vpid'])
    info(cc.getSid(), f"trying {item['entityType']} with url {uri}")
    if checkS3Uri(cc, uri, s3):       
        item['url'] = uri
        info(cc.getSid(), f"good {item['entityType']} with url {item['url']}")
        return item
    if validClip(item, cc): # clip, or it might be clip to episode - try it as a clip
        if item['entityType'] == 'clip':
            info(cc.getSid(), f"good clip with vpid {item['vpid']}")
        elif item['entityType'] == 'episode':
            info(cc.getSid(), f"clip labelled episode with vpid {item['vpid']}")
            item['entityType'] = 'clip'
        item['url'] = f"{cc.getMediaSelectorRedirectURL()}{item['vpid']}.mp4"
        info(cc.getSid(), f"good {item['entityType']} with url {item['url']}")
        return item
    info(cc.getSid(), f"cannot resolve {item['entityType']} with vpid {item['vpid']}")
    return None
