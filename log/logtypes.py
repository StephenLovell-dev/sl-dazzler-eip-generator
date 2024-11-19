from isodate import time_isoformat

def retry(sid, now, action):
    log(sid, now, action, 'retry')

def asRun(sid, now, action):
    log(sid, now, action, 'asRun')
    #TODO Write asruns to asrun S3 Bucket

def info(sid, text):
    print(sid, text)

def log(sid, now, action, reason):
    delta = now - action.start()
    delta_seconds = int(delta.total_seconds())
    if delta_seconds < 0:
        m = '%ds early' % -delta_seconds
    elif delta_seconds > 0:
        m = '%ds late' % delta_seconds
    else:
        m = 'on time'
    print(sid, reason, action.name(), m, time_isoformat(now).replace('+00:00', 'Z'))