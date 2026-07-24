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
from NudityCheck import getCachedData, getIMDBID, API_BASE_URL

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

    # Enabled providers from settings (same ids service_monitor uses), data-rich first.
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

    # Cache-ONLY read (no network) so the dialog opens instantly. The dialog itself fetches
    # any missing provider in a background thread after it is shown (see viewer.py). We never
    # gate the dialog on the shared global {provider}-Status props (that raced with the service
    # on slow tvOS); the dialog renders from providers_data below.
    providers_data = {}
    pending = []
    details = None
    for provider in providers:
        info, found = getCachedData(videoName, IMDBID, provider)
        providers_data[provider] = info
        if not found:
            pending.append(provider)          # never fetched -> background fetch
        if details is None and info and info.get('review-items'):
            details = info
            logger.info(f"Cache hit, first provider with data: {provider}")

    logger.info(f"ParentalGuide: cached data ready; pending fetch = {pending}")

    # Nothing cached AND nothing left to fetch (every provider is a cached blank) -> truly no data.
    if details is None and not pending:
        logger.info("No parental data for any provider (all cached blank)")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "No Parental Review Found", ADDON.getAddonInfo('icon')))
        return

    # Summary nudity ribbon property if we already have data in hand.
    if details and details.get('review-items'):
        for entry in details['review-items']:
            if "Sex" in entry.get('name', ''):
                try:
                    votes_str = "N/A"
                    if entry.get('votes'):
                        v = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                        if len(v) >= 2:
                            votes_str = f"{v[0]}/{v[1]}"
                        elif len(v) == 1:
                            votes_str = f"{v[0]}"
                    xbmcgui.Window(10000).setProperty(IMDBID + '-NVotes', votes_str)
                    xbmcgui.Window(10000).setProperty(IMDBID + '-NIcon', f"tags/{entry['cat']}.png")
                except Exception:
                    pass
                break

    # Open the dialog immediately; it renders from providers_data and fetches `pending` in bg.
    try:
        movie_title = xbmc.getInfoLabel("ListItem.Title")
        movie_year = xbmc.getInfoLabel("ListItem.Year")
        movie_mpaa = xbmc.getInfoLabel("ListItem.MPAA")

        viewer = SummaryViewer("summary.xml", CWD, title=videoName, details=details,
                               imdb_id=IMDBID, video_name=videoName,
                               providers_data=providers_data, pending_providers=pending,
                               movie_title=movie_title, movie_year=movie_year, movie_mpaa=movie_mpaa)
        viewer.doModal()
        del viewer
    except Exception as dialog_error:
        logger.error(f"Error opening dialog: {str(dialog_error)}")
        import traceback
        logger.error(traceback.format_exc())
        xbmc.executebuiltin('Notification(%s,%s,5000,%s)' % ("ParentalGuide", "Error opening dialog", ADDON.getAddonInfo('icon')))

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
