import os
from isodate import parse_duration

def s3ToHttpPath(uri):
    if uri is None:
        return None
    path = uri.split('/')
    path.pop(0)
    path.pop(0)
    bucket = path.pop(0)
    key = '/'.join(path)
    # TODO pass in region code
    regionCode = os.environ['AWS_REGION']
    return f"https://{bucket}.s3.{regionCode}.amazonaws.com/{key}"

def motionGraphicsOverlayForItem(cc, item):
    duration = int(parse_duration(item['graphic_duration']).total_seconds() * 1000)
    start = item['start'].replace(":", "'")
    url = s3ToHttpPath(item['url'])
    print(cc.getSid(),f"in s3 url {item['url']} out https url {url}")
    action = {
        "ActionName": f"{start} {item['graphic_duration']} graphic",
        "ScheduleActionStartSettings": {
            'ImmediateModeScheduleActionStartSettings': {}
        },
        "ScheduleActionSettings": {
            "MotionGraphicsImageActivateSettings": {
                "Duration": duration,
                "Url": url,
            }
        }
    }
    print(cc.getSid(), action)
    return action

def fixedMotionGraphicsOverlayForItem(cc, item):
    duration = int(parse_duration(item['graphic_duration']).total_seconds() * 1000)
    start = item['start'].replace(":", "'")
    url = s3ToHttpPath(item['url'])
    print(cc.getSid(),f"in s3 url {item['url']} out https url {url}")
    fixedStart = item['start']
    action = {
        "ActionName": f"{start} {item['graphic_duration']} graphic",
        "ScheduleActionStartSettings": {
            'FixedModeScheduleActionStartSettings': {
                'Time': fixedStart
            }
        },
        "ScheduleActionSettings": {
            "MotionGraphicsImageActivateSettings": {
                "Duration": duration,
                "Url": url,
            }
        }
    }
    print(cc.getSid(), action)
    return action