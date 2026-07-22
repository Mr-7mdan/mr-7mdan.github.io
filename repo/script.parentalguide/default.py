# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from threading import Thread
import re
import requests

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.viewer import SummaryViewer
from resources.lib.settings import log
from resources.lib.utils import logger
from NudityCheck import getData, getIMDBID, API_BASE_URL

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')

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
    logger.info("ParentalGuideCore: Video Name = %s" % videoName)
    
    # Cache-first: reuse whatever the background service (service_monitor/NudityCheck)
    # already prepared for this item, and inherit its 3-retry logic on a real miss.
    # This fixes the tvOS "No Parental Review Found": the old code re-fetched live with a
    # single 10s no-retry call and ignored the cache, so on a slow device it lost the race
    # against data-prep even though the service had already cached it.
    # Provider names match service_monitor's so cache keys line up (key = id_provider.lower()),
    # and calling getData refreshes each provider's -Status property the dialog's list reads.
    session = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    # Respect the per-provider enable settings (same setting ids service_monitor uses),
    # ordered data-rich first so the dialog opens on the first hit without extra calls.
    provider_settings = [
        ("IMDBProvider", "IMDB"),
        ("CSMProvider", "CSM"),
        ("DoveFoundationProvider", "DoveFoundation"),
        ("CringMDBProvider", "cring"),
        ("ParentPreviewsProvider", "ParentPreviews"),
        ("movieGuideOrgProvider", "MovieGuide"),
        ("kidsInMindProvider", "KidsInMind"),
        ("RaisingChildrenProvider", "RaisingChildren"),
    ]
    providers = [name for setting_id, name in provider_settings if ADDON.getSetting(setting_id) == "true"]
    logger.info(f"ParentalGuide: enabled providers = {providers}")
    details = None

    for provider in providers:
        try:
            info = getData(videoName, IMDBID, session, wid, provider, 0)
            if info and info.get('review-items') and len(info['review-items']) > 0:
                details = info
                logger.info(f"Found data from provider: {provider}")
                break
        except Exception as e:
            logger.error(f"Error fetching from {provider}: {str(e)}")
            continue
    
    try:
        if details and 'review-items' in details and details['review-items'] and len(details['review-items']) > 0:
            for entry in details['review-items']:
                if "Sex" in entry['name']:
                    votes_str = "N/A"
                    if entry.get('votes') and entry['votes']:
                        xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                        if len(xMainVotes) >= 2:
                            votes_str = f"{xMainVotes[0]}/{xMainVotes[1]}"
                        elif len(xMainVotes) == 1:
                            votes_str = f"{xMainVotes[0]}"
                    xbmcgui.Window(10000).setProperty(IMDBID + '-NVotes', votes_str)
                    xbmcgui.Window(10000).setProperty(IMDBID + '-NIcon', f"tags/{entry['cat']}.png")
            
            try:
                # Get movie info for dialog display
                movie_title = xbmc.getInfoLabel("ListItem.Title")
                movie_year = xbmc.getInfoLabel("ListItem.Year")
                movie_mpaa = xbmc.getInfoLabel("ListItem.MPAA")
                
                viewer = SummaryViewer("summary.xml", CWD, title=videoName, details=details, imdb_id=IMDBID, video_name=videoName, movie_title=movie_title, movie_year=movie_year, movie_mpaa=movie_mpaa)
                viewer.doModal()
                del viewer
            except Exception as dialog_error:
                logger.error(f"Error opening dialog: {str(dialog_error)}")
                import traceback
                logger.error(traceback.format_exc())
                xbmc.executebuiltin('Notification(%s,%s,5000,%s)' % ("ParentalGuide", "Error opening dialog", ADDON.getAddonInfo('icon')))
        else:
            logger.info("No review items found in response")
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Review Found", ADDON.getAddonInfo('icon')))
    except requests.RequestException as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Error fetching data", ADDON.getAddonInfo('icon')))
    except Exception as e:
        logger.error(f"Unexpected error in runForVideo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        xbmc.executebuiltin('Notification(%s,%s,5000,%s)' % ("ParentalGuide", "Unexpected error occurred", ADDON.getAddonInfo('icon')))

def runforimdb(IMDBID):
    wid = xbmcgui.getCurrentWindowId()
    
    params = {
        "imdb_id": IMDBID,
        "provider": "imdb"
    }
    
    try:
        response = requests.get(API_BASE_URL, params=params)
        response.raise_for_status()
        details = response.json()
        
        if details and 'review-items' in details:
            for entry in details['review-items']:
                if "Sex" in entry['name']:
                    xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                    if len(xMainVotes) >= 2:
                        votes_str = f"{xMainVotes[0]}/{xMainVotes[1]}"
                    elif len(xMainVotes) == 1:
                        votes_str = f"{xMainVotes[0]}"
                    else:
                        votes_str = "N/A"
                    xbmcgui.Window(wid).setProperty(IMDBID + '-NVotes', votes_str)
                    xbmcgui.Window(wid).setProperty(IMDBID + '-NIcon', f"special://home/addons/script.parentalguide/resources/skins/Default/media/tags/{entry['cat']}.png")
                    xbmc.executebuiltin('Notification(%s,%s,5000,%s)' % (f"Nudity : {entry['cat']}", f"{votes_str} Votes", xbmcgui.Window(wid).getProperty(IMDBID + '-NIcon')))
        else:
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Guide Rating Found", ADDON.getAddonInfo('icon')))
    except requests.RequestException as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Error fetching data", ADDON.getAddonInfo('icon')))
    except Exception as e:
        logger.error(f"Unexpected error in runforimdb: {str(e)}")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Unexpected error occurred", ADDON.getAddonInfo('icon')))

#########################
# Main
#########################
if __name__ == '__main__':
    logger.info("ParentalGuide: Started")
    IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
    year = xbmc.getInfoLabel("ListItem.Year")
    logger.info("ParentalGuide: Year " + year)
    
    # Get movie info for dialog display
    movie_title = xbmc.getInfoLabel("ListItem.Title")
    movie_year = xbmc.getInfoLabel("ListItem.Year")
    movie_mpaa = xbmc.getInfoLabel("ListItem.MPAA")
    logger.info(f"ParentalGuide: Movie info - Title: '{movie_title}', Year: '{movie_year}', MPAA: '{movie_mpaa}'")
    
    videoName = None
    isTvShow = getIsTvShow()

    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")
        logger.info("ParentalGuide: TV Show detected %s" % videoName)
    
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
        logger.info("ParentalGuide: Movie detected %s" % videoName)
    
    if IMDBID in [None, ""]:
        logger.info("ParentalGuide: Video ID not found for %s, trying to load it from OMDB" % videoName)
        IMDBID = getIMDBID(videoName, year)

    if videoName in [None, ""]:
        keyboard = xbmc.Keyboard('', ADDON.getLocalizedString(32032), False)
        keyboard.doModal()
        if keyboard.isConfirmed():
            try:
                videoName = keyboard.getText().decode("utf-8")
            except:
                videoName = keyboard.getText()

    if IMDBID not in [None, ""]:
        provider = xbmcgui.Window(10000).getProperty("SelectedProvider")
        runForVideo(videoName, IMDBID, isTvShow)
    else:
        logger.info("ParentalGuide: Failed to detect media")
        xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32011))

    logger.info("ParentalGuide: Ended")
