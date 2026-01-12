# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import html
import re
import requests
from resources.lib.settings import Settings, log
from NudityCheck import getData
from resources.lib.viewer import SummaryViewer

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')

def _setProperties(details):
    w = xbmcgui.Window(10000)
    log(f"ParentalGuide: Setting properties for {len(details)} items")
    for i, entry in enumerate(details):
        if i >= 10: break
        y = i + 1
        w.setProperty(f"ParentalGuide.{y}.Section", str(entry.get('name', '')))
        w.setProperty(f"ParentalGuide.Cat.Name.{y}", str(entry.get('cat', 'N/A')))
        
        desc = html.unescape(str(entry.get('description', 'No description available.')))
        w.setProperty(f"ParentalGuide.Desc.{y}", desc)
        
        votes_str = str(entry.get('votes', ''))
        w.setProperty(f"ParentalGuide.Votes.{y}", votes_str)
        try:
            nums = [int(s) for s in re.findall(r'\b\d+\b', votes_str)]
            val = f"{nums[0]}/{nums[1]}" if len(nums) >= 2 else (f"{nums[0]}" if len(nums) == 1 else "N/A")
            w.setProperty(f"ParentalGuide.MVotes.{y}", val)
        except:
            w.setProperty(f"ParentalGuide.MVotes.{y}", "N/A")
        
        w.setProperty(f"ParentalGuide.Cat.{y}", f"special://home/addons/script.parentalguide/resources/skins/Default/media/tags/{str(entry.get('cat', 'NA'))}.png")
    
    # Set default summary to first item
    if details:
        summary = html.unescape(str(details[0].get('description', 'No description available.')))
        w.setProperty("ParentalGuide.Desc.Summary", summary)

def _clearProperties():
    w = xbmcgui.Window(10000)
    log("ParentalGuide: Clearing item properties")
    for i in range(1, 11):
        w.clearProperty(f"ParentalGuide.{i}.Section")
        w.clearProperty(f"ParentalGuide.Cat.Name.{i}")
        w.setProperty(f"ParentalGuide.Desc.{i}", "")
        w.clearProperty(f"ParentalGuide.Votes.{i}")
        w.clearProperty(f"ParentalGuide.MVotes.{i}")
        w.clearProperty(f"ParentalGuide.Cat.{i}")
    w.setProperty("ParentalGuide.Desc.Summary", "")

if __name__ == '__main__':
    w = xbmcgui.Window(10000)
    
    # Check if we are already running for this exact request
    current_provider = w.getProperty("SelectedProvider")
    last_processed = w.getProperty("ParentalGuide.LastProcessedProvider")
    
    container = w.getProperty("SelectedContainer")
    cat_index = w.getProperty("SelectedCat")
    
    imdb_id = w.getProperty("CurrentId")
    video_name = w.getProperty("CurrentItem")
    
    window_open = w.getProperty("ParentalGuide.WindowOpen")
    
    log(f"ParentalGuide Script: Start (WindowOpen={window_open}, Provider={current_provider}, Container={container}, Cat={cat_index}, ID={imdb_id}, Name={video_name})")
    
    # Safety check: Don't run if CurrentId and CurrentItem are not set (dialog not open yet)
    if not imdb_id or not video_name:
        log("ParentalGuide Script: CurrentId or CurrentItem not set, skipping (dialog not open yet)")
        sys.exit(0)

    if container == "ProviderCont":
        if current_provider == last_processed and window_open == "true":
            log("ParentalGuide: Provider hasn't changed, skipping update")
        else:
            log(f"ParentalGuide: Updating to provider {current_provider}")
            w.setProperty("ParentalGuide.LastProcessedProvider", current_provider)
            _clearProperties()
            session = requests.Session()
            data = getData(video_name, imdb_id, session, 10000, current_provider, 1)
            
            if data and 'review-items' in data and data['review-items']:
                _setProperties(data['review-items'])
                if window_open == "true":
                    log("ParentalGuide: Refreshing container 4500 and setting focus")
                    w.setProperty("SelectedCat", "1")
                    # Signal the viewer to refresh by setting a flag
                    w.setProperty("ParentalGuide.ProviderChanged", str(xbmc.getInfoLabel("System.Time")))
                else:
                    log("ParentalGuide: Launching SummaryViewer")
                    viewer = SummaryViewer("summary.xml", CWD, title=video_name, details=data)
                    viewer.doModal()
                    del viewer
            else:
                log(f"ParentalGuide: No data found for {current_provider}")
                xbmc.executebuiltin(f'Notification(Parental Guide, No data for {current_provider}, 3000)')
            
    elif cat_index:
        log(f"ParentalGuide: Cat focused {cat_index}")
        desc = w.getProperty(f"ParentalGuide.Desc.{cat_index}")
        if desc:
            w.setProperty("ParentalGuide.Desc.Summary", desc)
            log(f"ParentalGuide: Updated summary to cat {cat_index}")
            # Signal viewer to update by toggling a refresh flag
            w.setProperty("ParentalGuide.RefreshTextbox", str(xbmc.getInfoLabel("System.Time")))
        else:
            log(f"ParentalGuide: No desc for cat {cat_index}")
            
    # Cleanup only if window is closing
    if window_open != "true":
        log("ParentalGuide: Cleaning up session properties")
        w.clearProperty("SelectedContainer")
        w.clearProperty("SelectedProvider")
        w.clearProperty("SelectedCat")
        w.clearProperty("ParentalGuide.LastProcessedProvider")