# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from threading import Thread
import re
#import requests

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.scraper import KidsInMindScraper
from resources.lib.scraper import IMDBScraper
from resources.lib.scraper import DoveFoundationScraper
from resources.lib.scraper import MovieGuideOrgScraper
from resources.lib.viewer import DetailViewer
from resources.lib.viewer import SummaryViewer
from resources.lib.settings import log
from resources.lib import imdb
from resources.lib.settings import log
from resources.lib.NudityCheck import getData

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from resources.lib.settings import log
#from resources.lib.core import ParentalGuideCore
#from core import ParentalGuideCore

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")

def getIsTvShow():
    if xbmc.getCondVisibility("Container.Content(tvshows)"):
        return True
    if xbmc.getCondVisibility("Container.Content(Seasons)"):
        return True
    if xbmc.getCondVisibility("Container.Content(Episodes)"):
        return True
    if xbmc.getInfoLabel("container.folderpath") == "videodb://tvshows/titles/":
        return True  # TvShowTitles

    return False

def runForVideo(videoName, IMDBID, isTvShow=False):
    log("ParentalGuideCore: Video Name = %s" % videoName)
    # Get the initial Source to use
    #searchSource = Settings.getDefaultSource()

    
    
    details = IMDBScraper.parentsguide(IMDBID, videoName)

    i = 0

    
    if len(details)>0:
        if details not in [None,""]:
            for entry in details['review-items']:
                if i < 9:
                    if "Sex" in details['review-items'][i]['name']:
                        xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', details['review-items'][i]['votes'])]
                        xbmcgui.Window(10000).setProperty(IMDBID + '-NVotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                        xbmcgui.Window(10000).setProperty(IMDBID + '-NIcon', "tags/" + str(details['review-items'][i]['cat']) + ".png")
            #selectedViewer = Settings.getDefaultViewer()                
            viewer = SummaryViewer("summary.xml", CWD, title=videoName, details=details)
            
            viewer.doModal()
            del viewer
        else:
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Review Found" , ADDON.getAddonInfo('icon')))
    else:
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Review Found" , ADDON.getAddonInfo('icon')))


def runforimdb(IMDBID):
    # Get the initial Source to use
    #IMDBID="tt0499549"
    dataScraper = IMDBScraper.parentsguide(IMDBID,videoName)
    details = dataScraper
    i = 0
    wid = xbmcgui.getCurrentWindowId()
    #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Selected: " + str(wid) , ADDON.getAddonInfo('icon')))
    if details not in [None,""]:    
        for entry in details['review-items']:
            if i < 9:
                if "Sex" in details['review-items'][i]['name']:
                    xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', details['review-items'][i]['votes'])]
                    # xbmcgui.Window(10000).setProperty(IMDBID + '-Nvotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                    # xbmcgui.Window(10000).setProperty(IMDBID + '-Nicon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + str(details['review-items'][i]['Cat']) + ".png")
                    xbmcgui.Window(wid).setProperty(IMDBID + '-NVotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                    xbmcgui.Window(wid).setProperty(IMDBID + '-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + str(details['review-items'][i]['cat']) + ".png")
                    #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('icon', str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nicon')) , ADDON.getAddonInfo('icon')))  
                    #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('votes', str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nvotes')) , ADDON.getAddonInfo('icon'))) 
                    xbmc.executebuiltin('Notification(%s,%s,5000,%s)' % ('Nudity : ' + str(details['review-items'][i]['cat']), str(xbmcgui.Window(wid).getProperty(IMDBID + '-NVotes') + " Votes") , str(xbmcgui.Window(wid).getProperty(IMDBID + '-NIcon')))) 
                    # dialog = xbmcgui.Dialog()
                    # dialog.notification('Nudity : ' + str(details[i]['Cat']), str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nvotes') + " Votes"), xbmcgui.NOTIFICATION_INFO, 5000)
                    # li = xbmcgui.ListItem()
                    # li.setProperty(IMDBID + '-Nvotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                    # li.setProperty(IMDBID + '-Nicon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + str(details[i]['Cat']) + ".png")
                    # li.setProperty('Nvotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                    # li.setProperty('Nicon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + str(details[i]['Cat']) + ".png")
                    # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Property for ' + IMDBID, str(li.getProperty('Nvotes')) , str(li.getProperty('Nicon'))))
                    # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('property name ', str(li.getProperty(IMDBID + '-Nvotes')) , str(li.getProperty(IMDBID + '-Nicon'))))
                # if "Sex" not in details[0]['name']:
                    # xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', details[i]['Votes'])]
                    # xbmcgui.Window(10000).setProperty(IMDBID + '-Nvotes', "NA")
                    # xbmcgui.Window(10000).setProperty(IMDBID + '-Nicon', "tags/" + "Clean.png")
                    # xbmcgui.Window(wid).setProperty(IMDBID + '-Nvotes', "NA")
                    # xbmcgui.Window(wid).setProperty(IMDBID + '-Nicon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + "Clean.png")
                    # #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('icon', str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nicon')) , ADDON.getAddonInfo('icon')))  
                    # #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('votes', str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nvotes')) , ADDON.getAddonInfo('icon'))) 
                    # # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Property', str(xbmcgui.Window(10000).getProperty(IMDBID + '-Nvotes')) , str(xbmcgui.Window(wid).getProperty(IMDBID + '-Nicon')))) 
                    # li = xbmcgui.ListItem()
                    # li.setProperty(IMDBID + '-Nvotes', (str(xMainVotes[0]) + "/" + str(xMainVotes[1])))
                    # li.setProperty(IMDBID + '-Nicon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/" + str(details[i]['Cat']) + ".png")
                    # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Property for ' + IMDBID, str(li.getProperty(IMDBID + '-Nvotes')) , str(li.getProperty(IMDBID + '-Nicon'))))
    else:
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Guide Rating Found" , ADDON.getAddonInfo('icon')))
#########################
# Main
#########################
if __name__ == '__main__':
    log("ParentalGuide: Started")

    videoName = None
    isTvShow = getIsTvShow()

    # First check to see if we have a TV Show of a Movie
    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")
        IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
        
    # If we do not have the title yet, get the default title
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
        IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
        print("ListItem.Title")
        print("ListItem.IMDBNumber")

    # If there is no video name available prompt for it
    if videoName in [None, ""]:
        # Prompt the user for the new name
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(32032), False)
        keyboard.doModal()

        if keyboard.isConfirmed():
            try:
                videoName = keyboard.getText().decode("utf-8")
            except:
                videoName = keyboard.getText()

    if IMDBID not in [None, ""]:
        provider = xbmcgui.Window(10000).getProperty("SelectedProvider")
    
        log("ParentalGuide: Video detected %s" % videoName)
        
        runForVideo(videoName, IMDBID, isTvShow)
        #runforimdb(IMDBID)
        print("ListItem.Title")
        print("ListItem.IMDBNumber")
    else:
        log("ParentalGuide: Failed to detect media")
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32011))

    log("ParentalGuide: Ended")

#########################
# Main
#########################
#class ParentalGuideCore():
#    @staticmethod
