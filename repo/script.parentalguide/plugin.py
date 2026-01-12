import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import sys
import requests
from bs4 import BeautifulSoup
from NudityCheck import getData
import xbmcgui
from resources.lib.settings import Settings
from resources.lib.utils import logger
from threading import Thread
from urllib.parse import parse_qsl, urlencode
import time
#import datetime
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='script.parentalguide')

def get_parental_guide(imdb_id,videoName):
    logger.info("ParentalGuide: Started for " + imdb_id)
    starttime = time.time()
    s = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    order = -1
    ProvidersList, Threads, Results = [] , [], []
        
    if imdb_id not in [None, ""]:
        logger.info("ParentalGuide: Video ID detected %s" % imdb_id)
        
        if ADDON.getSetting("IMDBProvider")== "true":
            order = order + 1 
            ProvidersList.append("IMDB")
            Results = Thread(target = getData(videoName, imdb_id, s, wid,"IMDB", order)).start()

        logger.info("ParentalGuide Finished in {s}s".format(s=time.time()-starttime))
        logger.info("InfoLabel: " + xbmc.getInfoLabel("ListItem.ParentalGuide"))
    else:
        Results = []
        logger.info("ParentalGuide: Failed to detect selected video")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Failed to detect a video" , ADDON.getAddonInfo('icon')))

    logger.info("ParentalGuide: Ended")
    return Results
    
def set_window_property(imdb_id):
    parental_guide = get_parental_guide(imdb_id)

def build_url(query):
    return addon.getAddonInfo('id') + '://' + addon.getAddonInfo('id') + '/?' + urlencode(query)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'get_parental_guide':
            imdb_id = params['imdb_id']
            videoName = params['videoName']
            logger.info("Received from API Router, imdb_id:" + imdb_id + " for action:" + params['action'])
            s = requests.Session()
            wid = xbmcgui.getCurrentWindowId()
            res = get_parental_guide(imdb_id,videoName)
            xbmcgui.Window(10000).setProperty('IMDB-NVotes', res)
            return res 
    # else:
    #     url = build_url({'action': 'get_parental_guide', 'imdb_id': 'tt1375666'})

if __name__ == '__main__':
    router(sys.argv[2][1:])
