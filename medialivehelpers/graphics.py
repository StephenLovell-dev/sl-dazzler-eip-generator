
profile_map = {
    'av_pv10_pa4': { 'index': 0, 'width': 960, 'height': 540  },
    'av_pv13_pa4': { 'index': 1, 'width': 960, 'height': 540 },
    'av_pv14_pa4': { 'index': 2, 'width': 1280, 'height': 720 },
    'av_pv42_pa4': { 'index': 3, 'width': 720, 'height': 576 },
    'av_pv43_pa4': { 'index': 4, 'width': 1920, 'height': 1080 },
    'av_pv44_pa4': { 'index': 5, 'width': 1920, 'height': 1080 },
}

# new table
ratings_table = [
    'NR',
    'PG',
    'TV-14',
    'TV-G',
    'TV-MA',
    'TV-PG',
    'M - Coarse Language, Mature Themes, Violence',
    'M - Coarse Language, Mature Themes',
    'M - Coarse Language, Sex Scenes, Mature Themes',
    'M - Coarse Language, Sexual References, Mature Themes',
    'M - Coarse Language, Violence',
    'M - Coarse Language',
    'M - Drug Use, Coarse Language',
    'M - Mature Themes, Violence',
    'M - Mature Themes',
    'MA - Coarse Language, Mature Themes',
    'MA - Coarse Language',
]

def graphicAction(cc, rating, profile, start):
    pb = cc.getPlayBucket()
    authorisation = cc.getAuthorisation()
    imageDimensions = cc.getAgeratingImageDimensions()
    uri = f's3://{pb}/graphics/{authorisation}/{rating}.png'
    if profile is None:
        height = profile_map['av_pv43_pa4']['height']
        width = profile_map['av_pv43_pa4']['width']
    else:
        height = profile_map[profile]['height']
        width = profile_map[profile]['width']
    h = int(imageDimensions['height']*height/1080)
    w = int(imageDimensions['width']*width/1920)
    x = int(imageDimensions['left']*width/1920)
    y = int(imageDimensions['top']*height/1080)
    print(cc.getSid(), 'image', x,y,w,h)
    aname = start.replace(":", "'") + ' PT25S graphic'
    startSettings = {
        'ImmediateModeScheduleActionStartSettings': {}
    }
    return {
        "ActionName": aname,
        "ScheduleActionStartSettings": startSettings,
        "ScheduleActionSettings": {
            "StaticImageActivateSettings": {
            "Image": {
                "Uri": uri
            },
            "Layer": 7,
            "ImageX": x,
            "ImageY": y,
            "Width": w,
            "Height": h,
            "Duration": 22000,
            "FadeOut": 3000
            }
        }
    }

def graphicsOverlayForItem(cc, item):
    if 'rating' in item:
        rating = item['rating']
        profile = item['profile']        
        action = graphicAction(cc, rating, profile, item['start'])
        print(cc.getSid(), action)
        return action
