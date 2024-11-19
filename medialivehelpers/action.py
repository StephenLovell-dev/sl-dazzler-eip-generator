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
    aname = item['start'].replace(":", "'")
    if 'start' in item and 'end' in item:
        duration = duration_isoformat(parse_datetime(item['end']) - parse_datetime(item['start']))
        aname = aname + ' ' + duration
    elif 'duration' in item:
        aname = aname + ' ' + duration_isoformat(parse_duration(item['duration']))
    if 'stream' in item:
        aname = aname + ' ' + truncate_middle(item['stream'], 10)
    elif 'origin' in item:
        aname = aname + ' ' + truncated_origin(item)
    if 'vpid' in item:
        aname = aname + ' ' + truncate_middle(item['vpid'].replace(' ', '_').replace('The ', ''), 10)
    if 'rating' in item:
        aname = aname + ' ' + addGraphicsOverlay(item)
    return aname

def startAndDurationFromActionName(name):
    print('startAndDurationFromActionName', name)
    start = None
    duration = None
    if name is not None:
        r = re.search(r"(\d\d\d\d)(\d\d)(\d\d)T(\d\d)(\d\d)(\d\d)\.(\d\d\d)Z (-?P[^ ]+)", name)
        if r is None: # accept old names during upgrade
            print("startAndDurationFromAction: Trying old regex...", name)
            r = re.search(r"\d+-\d+-\d+T\d\d'\d\d'\d\d(.\d\d\d)?Z P", name)
            if r is not None:
                parts = name.split(' ')
                start = parse_datetime(parts[0].replace("'", ':'))
                duration = parse_duration(parts[1])
                print('start', parts[0], start)
                return start, duration
        if r is not None:
            g = r.groups()
            dateString = "-".join(g[0:3])
            timeString = ":".join(g[3:6])
            startString = f"{dateString}T{timeString}.{g[6]}Z"
            start = parse_datetime(startString)
            duration = parse_duration(g[-1])
        else:
            print("regex failed: r is None")            
    return start, duration

class Action:

    def __init__(self, name, date):
        self._name = name
        parts = name.split(' ')
        if name == 'Initial Channel Input':
            self._start = date
            self._duration = "PT0S"
        elif 'T' in name:
            self._start = parse_datetime(parts[0].replace("'", ':'))
            if len(parts)>1:
                self._duration = parts[1]
        else:
            self._start = date
            self._duration = 'PT0S'
        if parts[-1].endswith('i'):
            graphics = parts[-1]
            gp = graphics.split(',')
            self._rating = ratings_table[int(gp[0], 16)]
            profile_index = int(gp[1][:-1], 16)
            p = [p for p in profile_map if profile_map[p]['index']==profile_index]
            self._profile = p[0]
        else:
            self._rating = None
            self._profile = None

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
