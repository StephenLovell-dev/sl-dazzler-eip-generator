import re
from isodate import time_isoformat
from datetime import datetime, timezone

def retry(sid, now, action):
    log(sid, now, action, 'retry')

def asRun(sid, now, action):
    log(sid, now, action, 'asRun')
    #TODO Write asruns to asrun S3 Bucket

def log_with_datetime(*args):
    print(datetime.now(timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z'), *args)

def info(sid, *args):
    log_with_datetime(sid, *args)

def humanifyActionName(name):
    if name is not None: 
        nameParts = name.split(" ", 1)
        r = re.search(r"(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.(\d\d\d)Z (-?P[^ ]+)", name) 
        if r is not None:
            g = r.groups()
            dateString = "-".join(g[0:3])
            timeString = ":".join(g[3:6])
            startString = f"{dateString}T{timeString}.{g[6]}Z"
            return f"{startString} {nameParts[1]}"
        else:
            print("humanifyActionName regex failed: r is None") 
            return name 
    print("humanifyActionName failed: Name is None")

def log(sid, now, action, reason):
    delta = now - action.start()
    delta_seconds = int(delta.total_seconds())
    if delta_seconds < 0:
        m = '%ds early' % -delta_seconds
    elif delta_seconds > 0:
        m = '%ds late' % delta_seconds
    else:
        m = 'on time'
    log_with_datetime(sid, reason, humanifyActionName(action.name()), m, time_isoformat(now).replace('+00:00', 'Z'))