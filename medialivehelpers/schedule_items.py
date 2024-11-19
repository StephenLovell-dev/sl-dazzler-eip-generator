from isodate import parse_datetime
from datetime import timedelta

class ScheduleItems:

    def __init__(self, items):
        if items is None:
            self.items = []
            self.switchItems = []
        else:
            self.items = items            
            self.switchItems = [item for item in self.items if "InputSwitchSettings" in item["ScheduleActionSettings"]]

    def completelyEmpty(self):
        return len(self.items) == 0

    def lastAny(self):
        if self.completelyEmpty():
            return None
        return self.items[-1]

    def empty(self):
        return len(self.switchItems) == 0

    def lastSwitch(self):
        if self.empty():
            return None
        return self.switchItems[-1]

    def noRecentFixedEvent(self, time):
        prev = self.newestFixedEvent()
        if prev is None:
            return True
        prevStart = parse_datetime(prev['ScheduleActionStartSettings']['FixedModeScheduleActionStartSettings']['Time'])
        return (time - prevStart) > timedelta(minutes=60)

    def newestFixedEvent(self):
        # step backwards looking for a fixed event
        for item in reversed(self.items):
            if 'FixedModeScheduleActionStartSettings' in item['ScheduleActionStartSettings']:
                return item
        return None

    def oldItemNames(self, time):
        index = None
        for x, action in enumerate(self.items):
            ss = action['ScheduleActionStartSettings']
            if 'FixedModeScheduleActionStartSettings' not in ss:
                continue
            t = parse_datetime(ss['FixedModeScheduleActionStartSettings']['Time'])
            if time > t:
                index = x
        if index is not None:
            old = []
            for x in range(index):
                old.append(self.items[x]['ActionName'])
            return old
        else:
            return None

    def after(self, action):
        for i in range(len(self.items)):
            if action.name() == self.items[i]['ActionName']:
                return ScheduleItems(self.items[i+1:])
        return ScheduleItems([])

    def itemNames(self):
        return [item['ActionName'] for item in self.items]  

    def len(self):
        return len(self.items)

    def actionStarts(self):
        return list(map(lambda n: n['ActionName'].split(' ')[0].replace("'", ":"), self.items))

