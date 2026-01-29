# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import time
import threading
from threading import Thread
import requests

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log
from resources.lib.SQLiteCache import SqliteCache
from resources.lib.utils import logger

# Import functions from NudityCheck
import NudityCheck

ADDON = xbmcaddon.Addon(id='script.parentalguide')

def sync_settings_to_properties():
    """
    Sync addon settings to Window properties so the skin can read them.
    This should be called on startup and when settings change.
    """
    # Reload addon to get fresh settings
    addon = xbmcaddon.Addon(id='script.parentalguide')
    window = xbmcgui.Window(10000)
    
    # Sync provider settings
    providers = [
        'IMDBProvider',
        'kidsInMindProvider',
        'movieGuideOrgProvider',
        'DoveFoundationProvider',
        'ParentPreviewsProvider',
        'CSMProvider',
        'RaisingChildrenProvider',
        'CringMDBProvider'
    ]
    
    for provider in providers:
        setting_value = addon.getSetting(provider)
        property_name = f"script.parentalguide.{provider}"
        window.setProperty(property_name, setting_value)
        logger.info(f"ParentalGuideMonitor: Set {property_name} = {setting_value}")
    
    # Sync loading indicator setting
    show_loading = ADDON.getSetting('showLoadingIndicator')
    window.setProperty('script.parentalguide.showLoadingIndicator', show_loading)
    logger.info(f"ParentalGuideMonitor: Set showLoadingIndicator = {show_loading}")
    
    logger.info("ParentalGuideMonitor: Settings synced to Window properties")

class ParentalGuideMonitor(xbmc.Monitor):
    """
    Background service that monitors ListItem focus changes and automatically
    fetches parental guide data for movies and TV shows on the main screen.
    """
    
    def __init__(self):
        super(ParentalGuideMonitor, self).__init__()
        self.previous_item_key = None
        self.fetch_thread = None
        self.fetch_lock = threading.Lock()
        self.last_fetch_time = 0
        # Read debounce delay from addon settings
        try:
            self.debounce_delay = float(ADDON.getSetting("debounceDelay"))
        except:
            self.debounce_delay = 0.2  # Default fallback
        # Sync settings to Window properties on startup
        sync_settings_to_properties()
        # logger.info(f"ParentalGuideMonitor: Initialized with debounce delay: {self.debounce_delay}s")
    
    def onSettingsChanged(self):
        """
        Called when addon settings are changed.
        Sync the new settings to Window properties.
        """
        # Update debounce delay
        try:
            self.debounce_delay = float(ADDON.getSetting("debounceDelay"))
        except:
            self.debounce_delay = 0.2
        
        # Sync all settings to Window properties
        sync_settings_to_properties()
    
    def get_current_item_info(self):
        """
        Get current focused item information from Kodi InfoLabels.
        Returns: tuple (imdb_id, title, year, dbtype) or None if no valid item
        """
        try:
            # Check if we're in a valid container context
            dbtype = xbmc.getInfoLabel("ListItem.DBType").lower()
            
            # Only process movies, tvshows, seasons, and episodes
            if dbtype not in ['movie', 'tvshow', 'season', 'episode']:
                return None
            
            imdb_id = xbmc.getInfoLabel("ListItem.IMDBNumber")
            title = xbmc.getInfoLabel("ListItem.Title")
            year = xbmc.getInfoLabel("ListItem.Year")
            
            # For TV shows, get the show title
            if dbtype in ['season', 'episode']:
                tvshow_title = xbmc.getInfoLabel("ListItem.TVShowTitle")
                if tvshow_title:
                    title = tvshow_title
            
            # Need at least a title to proceed
            if not title:
                return None
            
            # Create a unique key for this item
            item_key = f"{imdb_id}_{title}_{year}_{dbtype}"
            
            return {
                'key': item_key,
                'imdb_id': imdb_id if imdb_id else None,
                'title': title,
                'year': year if year else '',
                'dbtype': dbtype
            }
            
        except Exception as e:
            logger.error(f"ParentalGuideMonitor: Error getting item info: {str(e)}")
            return None
    
    def should_fetch_data(self, item_info):
        """
        Determine if we should fetch data for this item.
        Returns: bool
        """
        if not item_info:
            return False
        
        # Check if item changed
        if item_info['key'] == self.previous_item_key:
            return False
        
        # Check debounce timing
        current_time = time.time()
        if current_time - self.last_fetch_time < self.debounce_delay:
            return False
        
        return True
    
    def fetch_provider_data_and_update(self, title, imdb_id, session, wid, provider, order):
        """
        Wrapper to fetch data for a single provider and immediately copy to global properties.
        This allows indicators to appear as soon as each provider completes.
        """
        try:
            # Fetch data for this provider
            NudityCheck.getData(title, imdb_id, session, wid, provider, order)
            
            # Immediately copy this provider's properties to global for display
            NudityCheck.CopyPropertiesToGlobal(imdb_id, [provider])
            
            # logger.info(f"ParentalGuideMonitor: Provider {provider} completed and properties updated")
        except Exception as e:
            logger.error(f"ParentalGuideMonitor: Error fetching {provider}: {str(e)}")
    
    def fetch_parental_guide_data(self, item_info):
        """
        Fetch parental guide data for the given item using existing NudityCheck functions.
        Each provider updates properties immediately upon completion for progressive display.
        """
        try:
            # logger.info(f"ParentalGuideMonitor: Fetching data for {item_info['title']}")
            
            imdb_id = item_info['imdb_id']
            title = item_info['title']
            year = item_info['year']
            
            # If no IMDB ID, try to fetch it
            if not imdb_id or imdb_id == '':
                logger.info(f"ParentalGuideMonitor: No IMDB ID, attempting to fetch from OMDB")
                imdb_id = NudityCheck.getIMDBID(title, year)
            
            # Create a session for requests
            session = requests.Session()
            wid = 10000  # Use Home window for properties
            
            # Get list of enabled providers from settings
            providers = []
            if ADDON.getSetting("IMDBProvider") == "true":
                providers.append("IMDB")
            if ADDON.getSetting("kidsInMindProvider") == "true":
                providers.append("KidsInMind")
            if ADDON.getSetting("movieGuideOrgProvider") == "true":
                providers.append("MovieGuide")
            if ADDON.getSetting("DoveFoundationProvider") == "true":
                providers.append("DoveFoundation")
            if ADDON.getSetting("ParentPreviewsProvider") == "true":
                providers.append("ParentPreviews")
            if ADDON.getSetting("CringMDBProvider") == "true":
                providers.append("cring")
            if ADDON.getSetting("RaisingChildrenProvider") == "true":
                providers.append("RaisingChildren")
            if ADDON.getSetting("CSMProvider") == "true":
                providers.append("CSM")
            
            if not providers:
                logger.info("ParentalGuideMonitor: No providers enabled")
                # Clear loading indicator
                xbmcgui.Window(10000).clearProperty("ParentalGuide-Loading")
                return
            
            # Fetch data from each provider in parallel threads
            # Each thread will update properties immediately upon completion
            threads = []
            for i, provider in enumerate(providers):
                thread = Thread(
                    target=self.fetch_provider_data_and_update,
                    args=(title, imdb_id, session, wid, provider, i)
                )
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete (with timeout)
            for thread in threads:
                thread.join(timeout=10)
            
            # Clear loading indicator after all providers complete
            xbmcgui.Window(10000).clearProperty("ParentalGuide-Loading")
            
            # logger.info(f"ParentalGuideMonitor: Finished fetching data for {title}")
            
        except Exception as e:
            logger.error(f"ParentalGuideMonitor: Error fetching data: {str(e)}")
            # Clear loading indicator on error
            xbmcgui.Window(10000).clearProperty("ParentalGuide-Loading")
    
    def run(self):
        """
        Main monitoring loop that runs continuously in the background.
        """
        # logger.info("ParentalGuideMonitor: Service started")
        
        while not self.abortRequested():
            try:
                # Get current focused item info
                item_info = self.get_current_item_info()
                
                # Check if we should fetch data
                if self.should_fetch_data(item_info):
                    # Cancel any existing fetch thread
                    if self.fetch_thread and self.fetch_thread.is_alive():
                        logger.info("ParentalGuideMonitor: Previous fetch still running, skipping")
                    else:
                        # Get list of enabled providers
                        providers = []
                        if ADDON.getSetting("IMDBProvider") == "true":
                            providers.append("IMDB")
                        if ADDON.getSetting("kidsInMindProvider") == "true":
                            providers.append("KidsInMind")
                        if ADDON.getSetting("movieGuideOrgProvider") == "true":
                            providers.append("MovieGuide")
                        if ADDON.getSetting("DoveFoundationProvider") == "true":
                            providers.append("DoveFoundation")
                        if ADDON.getSetting("ParentPreviewsProvider") == "true":
                            providers.append("ParentPreviews")
                        if ADDON.getSetting("CringMDBProvider") == "true":
                            providers.append("cring")
                        if ADDON.getSetting("RaisingChildrenProvider") == "true":
                            providers.append("RaisingChildren")
                        if ADDON.getSetting("CSMProvider") == "true":
                            providers.append("CSM")
                        
                        # Clear properties immediately to prevent stale data during fetch
                        NudityCheck.ClearGlobalProperties(providers)
                        
                        # Set loading indicator
                        xbmcgui.Window(10000).setProperty("ParentalGuide-Loading", "true")
                        
                        # Update tracking variables
                        self.previous_item_key = item_info['key']
                        self.last_fetch_time = time.time()
                        
                        # Start new fetch thread (non-blocking)
                        self.fetch_thread = Thread(
                            target=self.fetch_parental_guide_data,
                            args=(item_info,)
                        )
                        self.fetch_thread.daemon = True
                        self.fetch_thread.start()
                
                # Check for abort every 300ms (responsive but not too frequent)
                if self.waitForAbort(0.3):
                    break
                    
            except Exception as e:
                logger.error(f"ParentalGuideMonitor: Error in main loop: {str(e)}")
                # Wait a bit before retrying to avoid rapid error loops
                if self.waitForAbort(1):
                    break
        
        # logger.info("ParentalGuideMonitor: Service stopped")


def start_monitor():
    """
    Entry point for the service. Creates and runs the monitor.
    """
    try:
        monitor = ParentalGuideMonitor()
        monitor.run()
    except Exception as e:
        logger.error(f"ParentalGuideMonitor: Fatal error: {str(e)}")
