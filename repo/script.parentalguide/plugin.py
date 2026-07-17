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
from urllib.parse import parse_qsl
import time
#import datetime
addon = xbmcaddon.Addon()
addon_handle = int(sys.argv[1])
ADDON = xbmcaddon.Addon(id='script.parentalguide')

def get_parental_guide(imdb_id,videoName):
    logger.info("ParentalGuide: Started for " + imdb_id)
    starttime = time.time()
    
    #imdb_id = None
    #videoName = None
    
    s = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    order = -1
    ProvidersList, Threads, Results = [] , [], []

    # If we do not have the title yet, get the default title
    # if videoName in [None, ""]:
        # videoName = xbmc.getInfoLabel("ListItem.Title")
        # logger.info("ParentalGuide: Video Name detected %s" % videoName)
    
    # if imdb_id in [None, ""]:
        # logger.info("ParentalGuide: Video ID not found for %s, trying to loaded it from OMDB" % videoName)
        # imdb_id = getimdb_id(videoName)
        
    if imdb_id not in [None, ""]:
        logger.info("ParentalGuide: Video ID detected %s" % imdb_id)
        
        if ADDON.getSetting("IMDBProvider")== "true":
            order = order + 1 
            ProvidersList.append("IMDB")
            Results = Thread(target = getData(videoName, imdb_id, s, wid,"IMDB", order)).start()
            
        
    # if videoName not in [None, ""]:

        # if ADDON.getSetting("kidsInMindProvider")== "true":
            # order = order + 1 
            # ProvidersList.append("KidsInMind")
            # Threads.append(Thread(target = getData(videoName, imdb_id, s, wid, "KidsInMind", order)))
            # Threads[order].start()
        # if ADDON.getSetting("movieGuideOrgProvider")== "true":
            # order = order +1 
            # ProvidersList.append("MovieGuide")
            # Threads.append(Thread(target = getData(videoName, imdb_id, s, wid, "MovieGuide", order)))
            # Threads[order].start()
        # if ADDON.getSetting("DoveFoundationProvider")== "true":
            # order = order +1 
            # ProvidersList.append("DoveFoundation")
            # Threads.append(Thread(target = getData(videoName, imdb_id, s, wid, "DoveFoundation", order)))
            # Threads[order].start()
        # if ADDON.getSetting("RaisingChildrenProvider")== "true":
            # order = order +1 
            # ProvidersList.append("RaisingChildren")
            # Threads.append(Thread(target = getData(videoName, imdb_id, s, wid, "RaisingChildren", order)))
            # Threads[order].start()
        # if ADDON.getSetting("CSMProvider")== "true":
            # order = order +1 
            # ProvidersList.append("CSM")
            # Threads.append(Thread(target = getData(videoName, imdb_id, s, wid, "CSM", order)))
            # Threads[order].start()
                    
        # for i in range(0,len(Threads)):
            # Threads[i].join()
            # #logger.info(Threads[i].result)
            
        
        #logger.info(Results)
            
        
        # with ThreadPoolExecutor(max_workers=100) as p:
            # p.map(getData, [videoName]*(order-1), [imdb_id]*(order-1), [s]*(order-1), [wid]*(order-1), ProvidersList , [0,1,2,3,4,5,6])

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
    # for key, value in parental_guide.items():
        # xbmcgui.Window(10000).setProperty(f"parentalguide.{key}", value)

def build_url(query):
    return addon.getAddonInfo('id') + '://' + addon.getAddonInfo('id') + '/?' + urllib.urlencode(query)

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
            #xbmcplugin.setResolvedUrl(addon_handle, True, xbmcgui.ListItem())
    else:
        url = build_url({'action': 'get_parental_guide', 'imdb_id': 'tt1375666'})
        #li = xbmcgui.ListItem(label='Get Parental Guide')
        #xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
        #xbmcplugin.endOfDirectory(addon_handle)


if __name__ == '__main__':
    router(sys.argv[2][1:])


# This code adds a router function that handles incoming requests to the addon. You can call the get_parental_guideaction with an imdb_id parameter to get the parental guide data for a specific movie.
# For example, you can create a custom home screen widget that calls this URL to get the parental guide data for Inception (2010):
# plugin://script.parentalguide2/?action=get_parental_guide&imdb_id=tt1375666&videoName=Inception
# Copy
# Make sure to replace your.addon.id with the actual ID of your addon.
# I hope this helps! Let me know if you have any questions or need further assistance.
# ——————

# The code I provided should be placed in the main script of your Kodi addon. The main script is the entry point of your addon and is specified in the addon.xml file of your addon.
# Here’s an example addon.xml file that specifies the main script of an addon:
# <?xml version="1.0" encoding="UTF-8"?>
# <addon id="your.addon.id" name="Your Addon" version="1.0.0" provider-name="Your Name">
    # <requires>
        # <import addon="xbmc.python" version="3.0.0"/>
    # </requires>
    # <extension point="xbmc.python.pluginsource" library="main.py">
        # <provides>executable</provides>
    # </extension>
# </addon>
# Copy
# In this example, the library attribute of the extension element specifies that the main script of the addon is main.py. This means that you should name the script containing the code I provided main.pyand place it in the root directory of your addon.
# When you call the URL of your addon from a home screen widget or another addon, Kodi will automatically run the main script of your addon and pass the URL parameters to the script. The routerfunction in the code I provided will then handle the incoming request and call the appropriate function based on the actionparameter.
# I hope this helps! Let me know if you have any questions or need further assistance.

