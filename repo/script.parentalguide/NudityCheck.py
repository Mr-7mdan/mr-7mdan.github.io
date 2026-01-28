# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from threading import Thread
import re
from concurrent.futures import ThreadPoolExecutor, wait
import threading
import queue

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log
from resources.lib.SQLiteCache import SqliteCache
from resources.lib.settings import log
from resources.lib.utils import logger
import requests
from bs4 import BeautifulSoup
import time
import datetime

db = SqliteCache()

import json

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')

# Add the API base URL
API_BASE_URL = "https://pg-2.vercel.app/get_data"

# Add db_lock for thread-safe database operations
db_lock = threading.Lock()

# Retry queue for failed API requests
# Format: (timestamp, videoName, ID, Provider, wid, order)
retry_queue = queue.Queue()
RETRY_DELAY_SECONDS = 60  # 1 minute delay for retries

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

def setProperty(PropertyName, PropertyVal, WindowID):
    # Force 10000 (Home) for global properties
    xbmcgui.Window(10000).setProperty(PropertyName, PropertyVal)
    # logger.debug(PropertyName + " was set sucessfully")
    
def Notify(title, msg):
    xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (title, msg , ADDON.getAddonInfo('icon')))

def CleanStr(txt):
    newtxt = txt.replace("<p>","").replace("</p>","").replace(";",".").replace("^","").replace("►\xa0","-").strip()
    return newtxt

def getData(videoName, ID, Session, wid, Provider, order):
    try:
        RYear = int(xbmc.getInfoLabel("ListItem.Year"))
    except:
        RYear = 0 
        
    today = datetime.date.today()
    year = today.year
    
    # Read cache duration settings from addon settings
    try:
        cache_current_year = int(ADDON.getSetting("cacheCurrentYear")) * 24 * 60 * 60
    except:
        cache_current_year = 7 * 24 * 60 * 60  # Default 7 days
    
    try:
        cache_recent_items = int(ADDON.getSetting("cacheRecentItems")) * 24 * 60 * 60
    except:
        cache_recent_items = 210 * 24 * 60 * 60  # Default 210 days (30 weeks)
    
    try:
        cache_older_items = int(ADDON.getSetting("cacheOlderItems")) * 24 * 60 * 60
    except:
        cache_older_items = 0  # Default permanent (0 = no expiry)
    
    try:
        cache_missing_ratings = int(ADDON.getSetting("cacheMissingRatings")) * 24 * 60 * 60
    except:
        cache_missing_ratings = 3 * 24 * 60 * 60  # Default 3 days
    
    try:
        if ID is not None:
            key = ID + "_" + Provider.lower()
        else:
            key = videoName.replace(":","").replace("-","_").replace(" ","_").lower()+ "_" + Provider.lower()
            
        show_info = db.get(key)
    except:
        # logger.debug("Failed to fetch from cache or cache not found")
        show_info = None
                
    if show_info is None: ##if not in cache
        # logger.debug('Loading from scratch, no cache found for [%s][%s]' % (videoName, Provider))
        
        # Check if there's a pending retry for this item
        current_time = time.time()
        retry_entry = check_retry_queue(key, current_time)
        
        if retry_entry:
            # Still within retry delay, skip for now
            # logger.debug(f"Retry scheduled for {videoName} [{Provider}] at {retry_entry['retry_time']}")
            AddFurnitureProperties(None, Provider, wid, ID)
            return None
        
        show_info, should_retry = callParentalGuideAPI(videoName, ID, Provider)   
        
        if show_info is None:
            if should_retry:
                # Schedule retry in 1 minute
                schedule_retry(key, videoName, ID, Provider, wid, order, current_time)
                # logger.debug(f"Scheduled retry for {videoName} [{Provider}] in {RETRY_DELAY_SECONDS} seconds due to failure/timeout")
            else:
                # No data available, cache empty result
                # logger.info("No Results found for this movie (" + videoName + ") on [" + Provider + "]")
                Xshow_info = {
                            "id": ID,
                            "title": videoName,
                            "provider": Provider,
                            "recommended-age": None,
                            "review-items": None,
                            "review-link": None
                            }
                # logger.debug("Trying to save blank data for this movie (" + videoName + ") on [" + Provider + "]")
                # Use cache_missing_ratings setting for items without ratings
                safe_db_set(Xshow_info, cache_missing_ratings)
            
            AddFurnitureProperties(None, Provider, wid, ID)
        else:
            # logger.debug('Finished loading new data for [%s][%s]' % (videoName, Provider))
            AddXMLProperties(show_info,wid)
            AddFurnitureProperties(show_info, Provider, wid, ID)
            
            # Conditional caching based on release year using settings
            if year == RYear:
                exp = cache_current_year  # Current year items
            elif year - RYear > 2:
                exp = cache_older_items  # Older items (>2 years)
            else:
                exp = cache_recent_items  # Recent items (1-2 years)
                
            safe_db_set(show_info, exp)
            # logger.debug("Added New Data for "+videoName + "[" + Provider +"] to cache with expiry: " + str(exp) + " seconds" )
    else:
        # logger.debug("Loading from cache for " +videoName + "[" + Provider +"]")
        AddXMLProperties(show_info,wid)
        AddFurnitureProperties(show_info, Provider, wid, ID)
    return show_info

def callParentalGuideAPI(videoName, ID, Provider, timeout=15):
    """
    Call the Parental Guide API and handle responses.
    Returns: tuple (show_info, should_retry)
        - show_info: dict with parental guide data or None
        - should_retry: bool indicating if request should be retried later
    """
    params = {
        "video_name": videoName,
        "imdb_id": ID,
        "provider": Provider.lower()
    }
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.get(API_BASE_URL, params=params, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            
            # Check for failed status from API
            status = data.get("status", "")
            if status == "Failed":
                # logger.error(f"API returned Failed status for {Provider} - {videoName}: {data}")
                # Return None and indicate retry should be attempted
                return (None, True)
            
            # Handle null values from API - convert None to empty array
            review_items = data.get("review-items")
            if review_items is None:
                review_items = []
            
            # Check if we got actual data (not empty)
            if not review_items and not data.get("recommended-age"):
                # logger.debug(f"API returned no data for {Provider} - {videoName}")
                return (None, False)  # No data, don't retry
            
            show_info = {
                "id": data.get("id") or ID,
                "title": data.get("title") or videoName,
                "provider": Provider,
                "recommended-age": data.get("recommended-age"),
                "review-items": review_items,
                "review-link": data.get("review-link")
            }
            return (show_info, False)  # Success, no retry needed
            
        except requests.Timeout as e:
            # logger.error(f"Timeout calling ParentalGuide API for {Provider} (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return (None, True)  # Timeout, should retry later
            time.sleep(1)
            
        except requests.RequestException as e:
            # logger.error(f"Error calling ParentalGuide API for {Provider} (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt == max_retries - 1:
                return (None, True)  # Network error, should retry later
            time.sleep(1)

def getIMDBID(name,year):
    k = "da6c8b4d"
    url = "http://www.omdbapi.com/?t=" + name.strip() +"&y=" + year + "&apikey=" + k +"&plot=full&r=json"
    # logger.debug(url)
    res = requests.get(url).content
    json_object = json.loads(res)

    if json_object["Response"] != 'False':
        result = json_object["imdbID"]
    else:
        print("Couldn't find IMDB ID")
        result = None
    return result

def AddXMLProperties(review, WindowID):    
    i = 0
    
    WID = xbmcgui.Window(WindowID)
    # if review['review-items'] is not None:
        # for item in review['review-items']:
            # y = i + 1
            # WID.setProperty("ParentalGuide.%s.Section" %y, review['review-items'][i]['name'])
            # WID.setProperty("ParentalGuide.%s.Desc" %y, review['review-items'][i]['description'])
            # WID.setProperty("ParentalGuide.%s.Score" %y, str(review['review-items'][i]['score']))
            # WID.setProperty("ParentalGuide.%s.Votes" %y, review['review-items'][i]['votes'])
            # WID.setProperty("ParentalGuide.%s.Cat" %y, review['review-items'][i]['cat'])
            # i = i+1
        #WID.setProperty("PG.Age".format(i), review['recommended-age'])
        #WID.setProperty("PG.URL".format(i), review['review-link'])
        #WID.setProperty("PG.Provider".format(i), review['provider'])

def AddFurnitureProperties(review, provider, WindowID, imdb_id=None):
    """
    Set parental guide properties with unique keys per movie ID to prevent race conditions.
    Provider icons are global, but severity data is unique per movie.
    
    Args:
        review: Review data from API or cache
        provider: Provider name (IMDB, KidsInMind, etc.)
        WindowID: Window ID (not used, keeping for compatibility)
        imdb_id: IMDB ID for unique property keys
    """
    Suffix = provider
    WID = xbmcgui.Window(10000) # Force Home window for furniture properties
    
    logger.debug(f"=== AddFurnitureProperties called for {provider} (IMDB: {imdb_id}) ===")
    logger.debug(f"Review data: {review}")
    
    # Always set the provider icon (global - never changes)
    WID.setProperty(f"{Suffix}-Icon", f"special://home/addons/script.parentalguide/resources/skins/Default/media/providers/{Suffix}.png")
    
    # If no IMDB ID, fall back to global properties (backward compatibility)
    if not imdb_id or imdb_id == '':
        property_prefix = Suffix
    else:
        property_prefix = f"{imdb_id}-{Suffix}"
    
    if review in [None, "", " "] or 'review-items' not in review or not review['review-items']:
        # Don't set NA properties - just clear them so visibility conditions hide the indicators
        WID.clearProperty(f"{property_prefix}-NRate")
        WID.clearProperty(f"{property_prefix}-NVotes")
        WID.clearProperty(f"{property_prefix}-Age")
        WID.clearProperty(f"{property_prefix}-NIcon")
        WID.setProperty(f"{property_prefix}-Status", 'false')
    else:
        WID.setProperty(f"{property_prefix}-Status", 'true')
        
        # Set recommended age if available (for CSM and similar providers)
        if review.get('recommended-age'):
            WID.setProperty(f"{property_prefix}-Age", review['recommended-age'])
        else:
            WID.clearProperty(f"{property_prefix}-Age")
        
        found_nudity = False
        for entry in review['review-items']:
            if entry['name'] in ["Sex & Nudity", "Nudity"]:
                found_nudity = True
                WID.setProperty(f"{property_prefix}-toggle", "true")
                
                # Build the icon path
                icon_path = f"special://home/addons/script.parentalguide/resources/skins/Default/media/providers/ribbon_mono/{Suffix}_{entry['cat']}.png"
                
                # DEBUG: Use xbmc.log to ensure it shows up
                xbmc.log(f"PG_DEBUG: Setting icon for {Suffix}: cat={entry['cat']}, path={icon_path}", xbmc.LOGINFO)
                
                # Set NRate (movie-specific and global)
                WID.setProperty(f"{property_prefix}-NRate", f" {entry['cat']}")
                WID.setProperty(f"{Suffix}-NRate", f" {entry['cat']}")
                
                # Set NIcon (movie-specific and global)
                WID.setProperty(f"{property_prefix}-NIcon", icon_path)
                WID.setProperty(f"{Suffix}-NIcon", icon_path)
                
                xbmc.log(f"PG_DEBUG: Set {Suffix}-NIcon property to: {icon_path}", xbmc.LOGINFO)
                
                # Show notification to verify on screen
                xbmc.executebuiltin(f'Notification(PG Debug,{Suffix} icon: {entry["cat"]},3000)')
                
                try:
                    if entry.get('votes'):
                        xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                        if len(xMainVotes) >= 2:
                            votesProp = f" {entry['cat']} ({xMainVotes[0]}/{xMainVotes[1]})"
                        elif len(xMainVotes) == 1:
                            votesProp = f" {entry['cat']} ({xMainVotes[0]})"
                        else:
                            votesProp = f" {entry['cat']} ({entry['votes']})"
                    else:
                        votesProp = f" {entry['cat']} (No votes)"
                    
                    # Set NVotes (movie-specific and global)
                    WID.setProperty(f"{property_prefix}-NVotes", votesProp)
                    WID.setProperty(f"{Suffix}-NVotes", votesProp)
                except Exception as e:
                    # logger.error(f"Error setting votes for {Suffix}: {str(e)}")
                    WID.setProperty(f"{property_prefix}-NVotes", f" {entry['cat']} (Error parsing votes)")
                
                break
        
        # If no nudity section found, clear nudity-specific properties but keep Age
        if not found_nudity:
            WID.clearProperty(f"{property_prefix}-NRate")
            WID.clearProperty(f"{property_prefix}-NVotes")
            WID.clearProperty(f"{property_prefix}-NIcon")
    
    # logger.debug(f"AddFurnitureProperties: Finished for provider {Suffix} with IMDB ID {imdb_id}")

def ClearGlobalProperties(providers):
    """
    Clear all global parental guide properties for all providers.
    Called when item changes to prevent stale data from showing.
    
    Args:
        providers: List of provider names to clear properties for
    """
    WID = xbmcgui.Window(10000)
    
    properties_to_clear = ['NRate', 'NVotes', 'Age', 'NIcon', 'Status', 'toggle']
    
    for provider in providers:
        for prop in properties_to_clear:
            global_prop_name = f"{provider}-{prop}"
            WID.clearProperty(global_prop_name)
    
    # logger.debug(f"ClearGlobalProperties: Cleared properties for {len(providers)} providers")

def CopyPropertiesToGlobal(imdb_id, providers):
    """
    Copy unique properties for a specific movie to global properties.
    This allows the skin to read global properties while avoiding race conditions.
    
    Args:
        imdb_id: IMDB ID of the focused movie
        providers: List of provider names to copy properties for
    """
    WID = xbmcgui.Window(10000)
    
    for provider in providers:
        if not imdb_id or imdb_id == '':
            # No IMDB ID, properties are already global
            continue
            
        property_prefix = f"{imdb_id}-{provider}"
        
        # Copy unique properties to global properties
        # Provider icon is already global, so skip it
        properties_to_copy = ['NRate', 'NVotes', 'Age', 'NIcon', 'Status', 'toggle']
        
        for prop in properties_to_copy:
            unique_prop_name = f"{property_prefix}-{prop}"
            global_prop_name = f"{provider}-{prop}"
            
            value = WID.getProperty(unique_prop_name)
            if value:
                WID.setProperty(global_prop_name, value)
            else:
                # Clear global property if unique property is empty
                WID.clearProperty(global_prop_name)
        
        # logger.debug(f"CopyPropertiesToGlobal: Copied properties for {provider} (IMDB: {imdb_id})")

# Replace the existing db.set() calls with:
def safe_db_set(show_info, timeout):
    with db_lock:
        db.set(show_info, timeout)

# Retry queue management
retry_dict = {}  # key -> {retry_time, videoName, ID, Provider, wid, order}
retry_dict_lock = threading.Lock()

def schedule_retry(key, videoName, ID, Provider, wid, order, current_time):
    """Schedule a retry for a failed API request after RETRY_DELAY_SECONDS."""
    with retry_dict_lock:
        retry_dict[key] = {
            'retry_time': current_time + RETRY_DELAY_SECONDS,
            'videoName': videoName,
            'ID': ID,
            'Provider': Provider,
            'wid': wid,
            'order': order
        }
    # logger.debug(f"Scheduled retry for {key} at {retry_dict[key]['retry_time']}")

def check_retry_queue(key, current_time):
    """Check if an item is in the retry queue and if retry time has passed."""
    with retry_dict_lock:
        if key in retry_dict:
            retry_entry = retry_dict[key]
            if current_time < retry_entry['retry_time']:
                # Still waiting for retry time
                return retry_entry
            else:
                # Retry time has passed, remove from queue and allow retry
                del retry_dict[key]
                # logger.debug(f"Retry time reached for {key}, attempting fetch")
    return None

def clean_old_retries(current_time, max_age=300):
    """Remove retry entries older than max_age seconds to prevent memory leaks."""
    with retry_dict_lock:
        keys_to_remove = []
        for key, entry in retry_dict.items():
            if current_time - entry['retry_time'] > max_age:
                keys_to_remove.append(key)
        for key in keys_to_remove:
            del retry_dict[key]
            # logger.debug(f"Cleaned old retry entry for {key}")

def process_retries():
    """Background thread to process retry queue."""
    while True:
        current_time = time.time()
        clean_old_retries(current_time)
        
        # Check for items ready to retry
        with retry_dict_lock:
            items_to_retry = []
            for key, entry in list(retry_dict.items()):
                if current_time >= entry['retry_time']:
                    items_to_retry.append((key, entry))
            
            # Remove from queue
            for key, _ in items_to_retry:
                if key in retry_dict:
                    del retry_dict[key]
        
        # Process retries
        for key, entry in items_to_retry:
            # logger.debug(f"Processing retry for {entry['videoName']} [{entry['Provider']}]")
            try:
                # Create a thread for the retry
                retry_thread = Thread(
                    target=getData,
                    args=(entry['videoName'], entry['ID'], None, entry['wid'], entry['Provider'], entry['order'])
                )
                retry_thread.daemon = True
                retry_thread.start()
            except Exception as e:
                logger.error(f"Error processing retry for {key}: {str(e)}")
        
        time.sleep(5)  # Check every 5 seconds

#########################
# Main
#########################
if __name__ == '__main__':
    logger.info("ParentalGuide: Started")
    starttime = time.time()
    
    # Start background retry processor
    retry_processor = Thread(target=process_retries)
    retry_processor.daemon = True
    retry_processor.start()
    
    IMDBID = None
    IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
    year = xbmc.getInfoLabel("ListItem.Year")
    videoName = None
    isTvShow = getIsTvShow()
    s = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    order = -1
    ProvidersList, Threads, Results = [] , [], []

    # First check to see if we have a TV Show of a Movie
    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")

    # If we do not have the title yet, get the default title
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
        # logger.info("ParentalGuide: Video Name detected %s" % videoName)
    
    if IMDBID in [None, ""]:
        # logger.info("ParentalGuide: Video ID not found for %s, trying to loaded it from OMDB" % videoName)
        IMDBID = getIMDBID(videoName,year)
        
    if IMDBID not in [None, ""]:
        # logger.info("ParentalGuide: Video ID detected %s" % IMDBID)
        
        if ADDON.getSetting("IMDBProvider")== "true":
            order = order + 1 
            ProvidersList.append("IMDB")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "IMDB", order)))
            Threads[order].start()
        
    if videoName not in [None, ""]:

        if ADDON.getSetting("kidsInMindProvider")== "true":
            order = order + 1 
            ProvidersList.append("KidsInMind")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "KidsInMind", order)))
            Threads[order].start()
        if ADDON.getSetting("movieGuideOrgProvider")== "true":
            order = order +1 
            ProvidersList.append("MovieGuide")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "MovieGuide", order)))
            Threads[order].start()
        if ADDON.getSetting("DoveFoundationProvider")== "true":
            order = order +1 
            ProvidersList.append("DoveFoundation")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "DoveFoundation", order)))
            Threads[order].start()
        if ADDON.getSetting("ParentPreviewsProvider")== "true":
            order = order +1 
            ProvidersList.append("ParentPeviews")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "ParentPeviews", order)))
            Threads[order].start()
        if ADDON.getSetting("CringMDBProvider")== "true":
            order = order +1 
            ProvidersList.append("cring")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "cring", order)))
            Threads[order].start()
        if ADDON.getSetting("RaisingChildrenProvider")== "true":
            order = order +1 
            ProvidersList.append("RaisingChildren")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "RaisingChildren", order)))
            Threads[order].start()
        if ADDON.getSetting("CSMProvider")== "true":
            order = order +1 
            ProvidersList.append("CSM")
            Threads.append(Thread(target=getData, args=(videoName, IMDBID, s, wid, "CSM", order)))
            Threads[order].start()

            
        for i in range(0,len(Threads)):
            Threads[i].join()
            #logger.info(Threads[i].result)
            
        
        #logger.info(Results)
        
        # Copy unique properties to global properties for the dialog
        # This ensures the skin can display the parental guide indicators
        if IMDBID and ProvidersList:
            CopyPropertiesToGlobal(IMDBID, ProvidersList)
            # logger.debug("ParentalGuide: Copied properties to global for dialog display")
        
        # Clean old retry entries
        clean_old_retries(time.time())
        
        # logger.info("ParentalGuide: Finished in {s:.2f}s".format(s=time.time()-starttime))
    else:
        # log("ParentalGuide: Failed to detect selected video")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Failed to detect a video" , ADDON.getAddonInfo('icon')))

    # log("ParentalGuide: Ended")