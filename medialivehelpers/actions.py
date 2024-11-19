from medialivehelpers.action import actionName

def findInput(item, channelDescription):
    if channelDescription is None:
        return None
    if 'InputAttachments' not in channelDescription:
        return None
    if 'stream' in item:
        for ia in channelDescription['InputAttachments']:
            n = ia['InputAttachmentName']
            if item['stream'] in n:
                return n
    elif 'url' in item:
        for ia in channelDescription['InputAttachments']:
            n = ia['InputAttachmentName']
            if 'dynamic' in n:
                return n
    else:
        for ia in channelDescription['InputAttachments']:
            n = ia['InputAttachmentName']
            if 'slate' in n:
                return n

def someAction(item, cd):
    print('someAction')
    an = actionName(item)
    print(cd['Name'], 'after actionName')
    r = {
            "ActionName": an,
            "ScheduleActionSettings": {
                'InputSwitchSettings': {
                }
            },
            'ScheduleActionStartSettings': {}
    }
    ian = findInput(item, cd)
    print(cd['Name'], 'after findInput', ian)
    if ian is not None:
        r['ScheduleActionSettings']['InputSwitchSettings']['InputAttachmentNameReference'] = ian
    if 'url' in item:
        r['ScheduleActionSettings']['InputSwitchSettings']['UrlPath'] = [item['url']]
    return r

def fixedAction(item, cd):
    start = item['start']
    r = someAction(item, cd)
    r['ScheduleActionStartSettings'] = {
        'FixedModeScheduleActionStartSettings': {
            'Time': start
        }
    }
    return r

def immediateAction(item, cd):
    print('immediateAction')
    r = someAction(item, cd)
    r['ScheduleActionStartSettings'] = {
        'ImmediateModeScheduleActionStartSettings': {}
    }
    return r

def followAction(item, cd, ref):
    r = someAction(item, cd)
    r['ScheduleActionStartSettings'] = {
                'FollowModeScheduleActionStartSettings': {
                    'FollowPoint': 'END',
                'ReferenceActionName': ref,
            }
    }
    return r

