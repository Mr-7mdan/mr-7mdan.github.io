# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from threading import Thread
import re
import json
# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log
from resources.lib import imdb
from resources.lib.settings import log
from bs4 import BeautifulSoup
import re
import requests

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

# Import the common settings
from resources.lib.settings import log
#from resources.lib.core import HD TrailersCore
#from core import HD TrailersCore

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
                
def HDTrailer(Media):
        # Get the initial Source to use
        #IMDBID="tt0499549"
    wid = xbmcgui.getCurrentWindowId()
    # xbmcgui.Window(wid).clearProperty('HDTrailer')
    
    base_url = 'https://www.hd-trailers.net/movie/'
    search_url = base_url+Media.lower().replace(" ","-")+"/"
    r = requests.get(search_url)
    soup = BeautifulSoup(r.content,"html.parser") 
    log(soup)
    
    try:
        tbl = soup.find("tr",{"itemprop":"trailer"})
        matches = tbl.findAll("td",{"class":"bottomTableResolution"})
        log("HD Trailer matches %s" % matches)

        qualities = []
        urls = []

        for entry in matches:
            try:
                urls.append(entry.a["href"])
                qualities.append(entry.a.text)
                log('iiiiiiiiiiiiiiiiiii matches\n' + entry.a.text)
            except:
                pass

        
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (qualities[0], urls[0] , ADDON.getAddonInfo('icon')))
        xbmcgui.Window(wid).setProperty('HDTrailer', urls[0])
    except:
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Sorry', "No HD Trailer Found at HD Trailers" , ADDON.getAddonInfo('icon')))
        pass
        
    #xbmc.executebuiltin('XBMC.PlayMedia(https://movietrailers.apple.com/movies/fox/avatar-the-way-of-water/avatar-the-way-of-water-trailer-3_h1080p.mov)')
    
    # if len(tbl) not in [None,0]:
        # for entry in matches:
            # if entry.a not in [None,""]:
                # if '1080p' in entry.a["href"]:
                    # res = entry.a["href"]
                    # xbmcgui.Window(wid).setProperty('HDTrailer', res)
                    # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Quality : 1080p ', res , ADDON.getAddonInfo('icon')))
                    # #xbmc.executebuiltin('XBMC.PlayMedia(' + res +')')
                # else:
                    # pass

        # if res is None:
            # for entry in matches:
                # while i<=Max:
                    # if '720p' in matches[i].a["href"]:
                        # res = matches[i].a["href"]
                        # xbmcgui.Window(wid).setProperty('HDTrailer', res)
                        # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Quality : , Match ' + str(i), res , ADDON.getAddonInfo('icon')))
                # i = i +1
        # if res is None:
            # for entry in matches:
                # while i <= Max:
                    # if '480p' in matches[i].a["href"]:
                        # res = matches[i].a["href"]
                        # xbmcgui.Window(wid).setProperty('HDTrailer', res)
                        # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Quality : 480p, Match ' + str(i), res , ADDON.getAddonInfo('icon')))
                # i = i +1
        
    # else:
        # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Sorry', "No Trailer Found at HD Trailers" , ADDON.getAddonInfo('icon')))
        

    
def imdbtrailer(ID):
    wid = xbmcgui.getCurrentWindowId()
    xbmcgui.Window(wid).clearProperty('HDTrailer')
    
    #IMDBID = "vi2766453273"
    video_url = "https://www.imdb.com/video/"+ID
    print(video_url)
    # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Trailer URL', video_url , ADDON.getAddonInfo('icon')))
    r = requests.get(url=video_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    script =soup.find('script',{"type":"application/ld+json"})
    xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('script', script , ADDON.getAddonInfo('icon')))
    
    json_object = json.loads(script.string)
    print(json_object["props"]["pageProps"]["videoPlaybackData"]["video"]["playbackURLs"])
    displayList = []
    videos = json_object["props"]["pageProps"]["videoPlaybackData"]["video"]["playbackURLs"]
    # links video quality order auto,1080,720
    for video in videos[1:] :
        video_link = video["url"]
        displayList.append(video_link)
        print(video_link)  
        #break
    res = xbmcgui.Dialog().select(ADDON.getLocalizedString(32004), displayList)
    xbmcgui.Window(wid).setProperty('HDTrailer', res)
    xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Selected', res , ADDON.getAddonInfo('icon')))

def getMovieTrailerDetails(imdbID):
    headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }
    movie_url = "https://www.imdb.com/title/"+imdbID
    r = requests.get(url=movie_url, headers=headers)
    # Create a BeautifulSoup object
    soup = BeautifulSoup(r.text, 'html.parser')

    script =soup.find("script",{'type': 'application/json'})
    #print(script)
    json_object = json.loads(script.string)
    print(json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["name"]["value"])
    print(json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["thumbnail"]["url"])
    print(json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["description"]["value"])
    print(json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["playbackURLs"][0]["displayName"]["value"])
    print(json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["playbackURLs"][0]["url"])
    videos = json_object["props"]["pageProps"]["aboveTheFoldData"]["primaryVideos"]["edges"][0]["node"]["playbackURLs"]
    
#########################
# Main
#########################
if __name__ == '__main__':
    log("HD Trailers: Started")
    ID = None
    ID = xbmc.getInfoLabel("ListItem.IMDBNumber")
    
    videoName = None
    isTvShow = getIsTvShow()

    # First check to see if we have a TV Show of a Movie
    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")
        IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
        
    # If we do not have the title yet, get the default title
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
    
    #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (name, ID , ADDON.getAddonInfo('icon')))

    if videoName not in [None, ""]:
        log("HD Trailers: Video detected %s" % (videoName + " (" + ID + ")"))
        HDTrailer(videoName)

    else:
        log("HD Trailers: Failed to detect selected video")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("HD Trailers", "Failed to detect selected video" , ADDON.getAddonInfo('icon')))
        #xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32011))

    log("HD Trailers: Ended")

#########################
# Main
#########################
#class HD TrailersCore():
#    @staticmethod
