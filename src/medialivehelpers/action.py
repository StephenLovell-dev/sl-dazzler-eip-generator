from dazzler.schedule import datetime_isoformat
from isodate import parse_duration, parse_datetime, duration_isoformat
import re
from medialivehelpers.graphics import profile_map, ratings_table

def truncate_middle(s, n):
    if len(s) <= n:
        # string is already short-enough
        return s
    # half of the size, minus the 3 .'s
    n_2 = int((n-3) / 2)
    return f'{s[:n_2]}...{s[-n_2:]}'
    
def truncated_origin(item):
    if item['origin'] == 'slate':
        return 'slate'
    if item['origin'] == 'loop':
        return 'loop'
    if item['origin'] == 'schedule':
        return 'sched'
    return item['origin'][:4]

def addGraphicsOverlay(item):
    rating = item['rating']
    try:
        ri = ratings_table.index(rating)
    except ValueError:
        ri = 0 # PG
    if 'profile' in item:
        profile = item['profile']
        if profile in profile_map:
            pi = profile_map[profile]['index']
        else:
            # print(cc.getSid(), f"rating {rating} profile {profile} missing from profile map")
            pi = 5 # full HD
    else:
        # print(cc.getSid(), f"profile missing from schedule item")
        pi = 5 # full HD
    # N.B. i is not a valid character in a pid
    return f"{hex(ri)[2:]},{hex(pi)[2:]}i"

def actionName(item):
    if item is None:
        return ''
    startdt = parse_datetime(item['start'])
    start = datetime_isoformat(startdt)
    aname = start.replace(":", "").replace("-", "")
    if 'duration' in item:
        aname = aname + ' ' + duration_isoformat(parse_duration(item['duration']))
    elif 'start' in item and 'end' in item:
        duration = duration_isoformat(parse_datetime(item['end']) - startdt)
        aname = aname + ' ' + duration 
    if 'stream' in item:
        aname = aname + ' ' + truncate_middle(item['stream'], 10)
    elif 'origin' in item:
        aname = aname + ' ' + truncated_origin(item)
    if 'vpid' in item:
        aname = aname + ' ' + truncate_middle(item['vpid'].replace(' ', '_').replace('The ', ''), 10)
    if 'rating' in item:
        aname = aname + ' ' + addGraphicsOverlay(item)
    return aname

def startAndDurationStringsFromActionName(name):
    print('startAndDurationStringsFromActionName', name)
    r = re.search(r"(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.(\d\d\d)Z (-?P[^ ]+)", name)
    if r is None:
        print("regex failed: r is None")
        return None, None        
    g = r.groups()
    dateString = "-".join(g[0:3])
    timeString = ":".join(g[3:6])
    startString = f"{dateString}T{timeString}.{g[6]}Z"
    return startString, g[-1]

def graphicsRatingAndProfileFromActionName(name):
    parts = name.split(' ')
    if not parts[-1].endswith('i'):
        return None, None
    graphics = parts[-1]
    gp = graphics.split(',')
    rating = ratings_table[int(gp[0], 16)]
    profile_index = int(gp[1][:-1], 16)
    p = [p for p in profile_map if profile_map[p]['index']==profile_index]
    profile = p[0]
    return rating, profile

def startAndDurationFromAction(action):
    if action is None or 'ActionName' not in action:
        print(f'Error: no ActionName in {action}')
        return None, None
    name = action['ActionName']
    if name is None:
        return None, None
    ss, ds = startAndDurationStringsFromActionName(name)
    if ss is None:
        return None, None
    start = parse_datetime(ss)
    duration = parse_duration(ds)
    return start, duration

def startFromAction(action):
    if 'ActionName' not in action:
        print(f'Error: no ActionName in {action}')
        return None
    ss, ds = startAndDurationStringsFromActionName(action['ActionName'])
    if ss is None:
        return None
    return parse_datetime(ss)

class Action:

    def __init__(self, name, date=None):
        self._name = name
        self._rating = None
        self._profile = None
        if name == 'Initial Channel Input':
            self._start = date
            self._duration = "PT30S"
            return
        ss, ds = startAndDurationStringsFromActionName(name)
        if ss is None or ds is None:
            self._start = date
            self._duration = "PT0S"
            return
        self._start = parse_datetime(ss)
        self._duration = ds
        self._rating, self._profile = graphicsRatingAndProfileFromActionName(name)

    def __eq__(self, obj):
        if obj.start() != self._start:
            return False 
        if obj.duration() != self._duration:
            return False   
        if obj.name() != self._name:
            return False
        return True

    def name(self):
        return self._name

    def start(self):
        return self._start

    def duration(self):
        return self._duration

    def end(self):
        return self._start + parse_duration(self._duration)

    def rating(self):
        return self._rating

    def profile(self):
        return self._profile
