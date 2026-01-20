'''
    3rbi
    Copyright (C) 2026 3rbi
'''


convertdict = {}


def convertfav(backupdata):
    favorites = backupdata["data"]
    favoritesnew = []

    for favorite in favorites:
        if favorite['mode'] in convertdict:
            if favorite['mode'] == 518:
                favorite['url'] = '{0}$${1}'.format(favorite['name'], favorite['url'])
            if favorite['mode'] in (342, 382):
                url = favorite['url'].split('/')
                favorite['url'] = '/'.join([url[x] for x in [0, 1, 2, 4]])
            favorite['mode'] = convertdict[favorite['mode']]
            favoritesnew.append(favorite)

    backupdata['data'] = favoritesnew
    return backupdata
