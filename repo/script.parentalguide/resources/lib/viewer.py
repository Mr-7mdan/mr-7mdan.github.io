# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import traceback
import json
from threading import Thread
from datetime import datetime, timedelta
import re
from resources.lib.settings import log
import html


ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")

class ParentalGuideViewer(xbmcgui.WindowXMLDialog):
    TITLE_LABEL_ID = 201
    #VIEWER_CHANGE_BUTTON = 3102
    VIEWER_CHANGE_BUTTON = 301
    CLOSE_BUTTON = 302
    #SWITCH_BUTTON = 3101
    SWITCH_BUTTON = 303
    LIST_BOX_ID = 203
    LIST2_BOX_ID = 2055
    TEXT2_BOX_ID = 202
    LABEL2_BOX_ID = 2011
    MORE_BUTTON = 6600
    TEXTVIEWER_BTN = 4510
    List = 4500
    def __init__(self, *args, **kwargs):
        self.isSwitchFlag = False
        self.isChangeViewerFlag = False
        self.switchText = kwargs.get('switchText', '')
        self.title = kwargs.get('title', '').replace("b'","").replace("'","")
        xbmcgui.WindowXMLDialog.__init__(self, *args, **kwargs)

    # Called when setting up the window
    def onInit(self):
        # Update the dialog to show the correct data
        xbmcgui.Window(10000).setProperty("ParentalGuide.WindowOpen", "true") 
        xbmcgui.Window(10000).clearProperty("SelectedCat") 
        xbmcgui.WindowXMLDialog.onInit(self)
            
    def close(self):
        log("ParentalGuideViewer: Closing window")
        xbmcgui.Window(10000).clearProperty("ParentalGuide.WindowOpen") 
        xbmcgui.WindowXMLDialog.close(self)

    def isSwitch(self):
        return self.isSwitchFlag

    def isChangeViewer(self):
        return self.isChangeViewerFlag


######################################
# Details listing screen
######################################
class SummaryViewer(ParentalGuideViewer):
    # TEXT2_BOX_ID = 202
    # LABEL2_BOX_ID = 2011
    # LIST_BOX_ID = 203
    
    def __init__(self, *args, **kwargs):
        self.details = kwargs.get('details', '')
        self.imdb_id = kwargs.get('imdb_id', '')
        self.video_name = kwargs.get('video_name', '')
        if self.details not in [None, ""]:
            self._setProperties(self.details['review-items'])

        ParentalGuideViewer.__init__(self, *args, **kwargs)

    @staticmethod
    def createSummaryViewer(title, details):
        return SummaryViewer("summary.xml", CWD, title=title, details=details)

    def close(self):
        log("ParentalGuideViewer: Closing window")
        # Stop monitoring thread
        if hasattr(self, '_monitor_active'):
            self._monitor_active = False
        # Clear all the properties that were previously set
        w = xbmcgui.Window(10000)
        i = 1
        while i < 9:
            w.clearProperty("ParentalGuide.%s.Section" % i)
            w.clearProperty("ParentalGuide.%s.Rating" % i)
            w.clearProperty("ParentalGuide.Desc.%s" % i)
            i = i + 1
        w.clearProperty("SelectedCat") 
        w.clearProperty("SelectedProvider")
        w.clearProperty("ParentalGuide.Desc.section") 
        w.clearProperty("ParentalGuide.Desc.Summary")
        w.clearProperty("ParentalGuide.RefreshTextbox")
        w.clearProperty("ParentalGuide.ProviderChanged")
        w.clearProperty("CurrentId")
        w.clearProperty("CurrentItem")
        ParentalGuideViewer.close(self)
        
    def onInit(self):
        w = xbmcgui.Window(10000)
        
        # Debug: Check if movie info properties are set
        title = w.getProperty("ParentalGuide.Dialog.Title")
        year = w.getProperty("ParentalGuide.Dialog.Year")
        mpaa = w.getProperty("ParentalGuide.Dialog.MPAA")
        log(f"SummaryViewer: onInit - Movie properties: Title='{title}', Year='{year}', MPAA='{mpaa}'")
        
        # Set CurrentId and CurrentItem for provider switching FIRST
        if self.imdb_id:
            w.setProperty("CurrentId", self.imdb_id)
        if self.video_name:
            w.setProperty("CurrentItem", self.video_name)
        
        log(f"SummaryViewer: onInit called, CurrentId={self.imdb_id}, CurrentItem={self.video_name}")
        
        # Rebuild lists BEFORE calling parent onInit so controls are populated when focus is set
        self._rebuildProviderList()
        self._rebuildCategoryList()
        self._updateTextbox()
        
        # Now call parent onInit which will set WindowOpen property
        ParentalGuideViewer.onInit(self)
        
        log(f"SummaryViewer: Lists populated, WindowOpen={w.getProperty('ParentalGuide.WindowOpen')}")
        
        # Start monitoring thread
        self._last_refresh = ""
        self._last_provider_flag = w.getProperty("ParentalGuide.ProviderChanged") or ""
        self._monitor_active = True
        log(f"SummaryViewer: Initial provider flag: '{self._last_provider_flag}'")
        self._monitor_thread = Thread(target=self._monitorProviderChange)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
    
    def _rebuildProviderList(self):
        """Rebuild the provider list with greyed out styling for providers without data"""
        try:
            try:
                provider_list = self.getControl(4400)
            except Exception as e:
                log(f"SummaryViewer: Cannot get provider list control yet: {str(e)}")
                return
            
            w = xbmcgui.Window(10000)
            
            # Clear existing items
            provider_list.reset()
            
            # Define all providers in order
            providers = [
                ("IMDB", "IMDB"),
                ("Kids In Mind", "KidsInMind"),
                ("Movie Guide Org", "MovieGuide"),
                ("Dove Foundation", "DoveFoundation"),
                ("Common Sense Media", "CSM"),
                ("Raising Children", "RaisingChildren")
            ]
            
            for label, provider_key in providers:
                icon = w.getProperty(f"{provider_key}-Icon")
                status = w.getProperty(f"{provider_key}-Status")
                has_data = (status == "true")
                
                listitem = xbmcgui.ListItem(label=label)
                listitem.setArt({'icon': icon, 'thumb': icon})
                listitem.setProperty('provider_key', provider_key)
                listitem.setProperty('has_data', str(has_data))
                
                provider_list.addItem(listitem)
            
            # Set focus to first item with data, or just first item
            if provider_list.size() > 0:
                provider_list.selectItem(0)
            
            log(f"SummaryViewer: Provider list rebuilt with {provider_list.size()} items")
        except Exception as e:
            log(f"SummaryViewer: Error rebuilding provider list: {str(e)}")
    
    def _updateTextbox(self):
        """Update the textbox with current description"""
        try:
            textbox = self.getControl(5)
            w = xbmcgui.Window(10000)
            desc = w.getProperty("ParentalGuide.Desc.Summary")
            if desc:
                textbox.setText(desc)
                log(f"SummaryViewer: Textbox updated")
        except Exception as e:
            log(f"SummaryViewer: Error updating textbox: {str(e)}")
    
    def _monitorProviderChange(self):
        """Background thread to monitor for provider focus changes and category selection"""
        import time
        w = xbmcgui.Window(10000)
        last_category_pos = -1
        last_provider_pos = -1
        check_count = 0
        
        log("SummaryViewer: Monitoring thread started")
        
        while self._monitor_active:
            try:
                check_count += 1
                
                # Check for provider focus changes
                try:
                    provider_list = self.getControl(4400)
                    current_provider_pos = provider_list.getSelectedPosition()
                    
                    if current_provider_pos != last_provider_pos and current_provider_pos >= 0:
                        last_provider_pos = current_provider_pos
                        selected_item = provider_list.getSelectedItem()
                        
                        if selected_item:
                            provider_key = selected_item.getProperty('provider_key')
                            has_data = selected_item.getProperty('has_data')
                            
                            log(f"SummaryViewer: Provider focus changed to {provider_key} (has_data={has_data})")
                            
                            # Clear description first
                            w.clearProperty("ParentalGuide.Desc.Summary")
                            textbox = self.getControl(5)
                            textbox.setText("")
                            
                            # Clear categories
                            category_list = self.getControl(4500)
                            category_list.reset()
                            
                            # Rebuild if provider has data
                            if has_data == "True":
                                self._rebuildCategoryListForProvider(provider_key)
                            else:
                                log(f"SummaryViewer: Provider {provider_key} has no data")
                            
                            # Reset category position tracking
                            last_category_pos = -1
                except Exception as e:
                    if "Non-Existent Control" not in str(e):
                        log(f"SummaryViewer: Error checking provider position: {str(e)}")
                
                # Check for category selection changes
                try:
                    category_list = self.getControl(4500)
                    current_category_pos = category_list.getSelectedPosition()
                    
                    if current_category_pos != last_category_pos and current_category_pos >= 0:
                        last_category_pos = current_category_pos
                        selected_item = category_list.getSelectedItem()
                        
                        # Always clear first
                        w.clearProperty("ParentalGuide.Desc.Summary")
                        textbox = self.getControl(5)
                        textbox.setText("")
                        
                        if selected_item:
                            # Get description directly from ListItem property
                            desc = selected_item.getProperty('description')
                            if desc and desc.strip():
                                import html
                                desc = html.unescape(str(desc))
                                w.setProperty("ParentalGuide.Desc.Summary", desc)
                                textbox.setText(desc)
                                log(f"SummaryViewer: Category at position {current_category_pos} selected with description")
                            else:
                                log(f"SummaryViewer: Category at position {current_category_pos} has no description")
                except Exception as e:
                    if "Non-Existent Control" not in str(e):
                        log(f"SummaryViewer: Error checking category position: {str(e)}")
                
                time.sleep(0.15)  # Check every 150ms for responsive UI
            except Exception as e:
                log(f"SummaryViewer: Monitoring thread error: {str(e)}")
                import traceback
                log(traceback.format_exc())
                break
        
        log("SummaryViewer: Monitoring thread stopped")
    
    def onAction(self, action):
        """Monitor for property changes and update textbox"""
        # Check if refresh flag changed (set by script.py)
        w = xbmcgui.Window(10000)
        refresh_flag = w.getProperty("ParentalGuide.RefreshTextbox")
        
        if refresh_flag and refresh_flag != self._last_refresh:
            self._last_refresh = refresh_flag
            self._updateTextbox()
        
        # Call parent onAction
        ParentalGuideViewer.onAction(self, action)
    
    def _rebuildCategoryList(self):
        """Rebuild the category list with current data"""
        try:
            category_list = self.getControl(4500)
            w = xbmcgui.Window(10000)
            
            # Clear existing items
            category_list.reset()
            
            # Add items based on current properties
            for i in range(1, 9):
                section = w.getProperty(f"ParentalGuide.{i}.Section")
                if section:
                    cat_name = w.getProperty(f"ParentalGuide.Cat.Name.{i}")
                    votes = w.getProperty(f"ParentalGuide.MVotes.{i}")
                    icon = w.getProperty(f"ParentalGuide.Cat.{i}")
                    desc = w.getProperty(f"ParentalGuide.Desc.{i}")
                    
                    listitem = xbmcgui.ListItem(label=f"{section} - {cat_name} ({votes})")
                    listitem.setArt({'icon': icon, 'thumb': icon})
                    listitem.setProperty('cat_index', str(i))
                    listitem.setProperty('description', desc)  # Store description in ListItem
                    category_list.addItem(listitem)
            
            # Set focus to first item
            if category_list.size() > 0:
                category_list.selectItem(0)
                # Update description for first category
                first_item = category_list.getSelectedItem()
                if first_item:
                    desc = first_item.getProperty('description')
                    if desc:
                        w.setProperty("ParentalGuide.Desc.Summary", desc)
                        textbox = self.getControl(5)
                        textbox.setText(desc)
            
            log(f"SummaryViewer: Category list rebuilt with {category_list.size()} items")
        except Exception as e:
            log(f"SummaryViewer: Error rebuilding category list: {str(e)}")
    
    def _rebuildCategoryListForProvider(self, provider_key):
        """Rebuild category list using data from a specific provider (already fetched by NudityCheck.py)"""
        try:
            category_list = self.getControl(4500)
            w = xbmcgui.Window(10000)
            
            # Clear existing items
            category_list.reset()
            
            # Get the cached data for this provider from the database
            from NudityCheck import db
            
            # Build cache key
            video_name = self.video_name
            imdb_id = self.imdb_id
            if imdb_id:
                key = f"{imdb_id}_{provider_key.lower()}"
            else:
                key = f"{video_name.replace(':', '').replace('-', '_').replace(' ', '_').lower()}_{provider_key.lower()}"
            
            # Get data from cache
            show_info = db.get(key)
            
            if show_info and show_info.get('review-items'):
                log(f"SummaryViewer: Found cached data for {provider_key}, building category list")
                
                # Build category list from this provider's data
                for i, entry in enumerate(show_info['review-items']):
                    if i >= 8:  # Max 8 categories
                        break
                    
                    section = entry.get('name', '')
                    cat_name = entry.get('cat', 'N/A')
                    
                    # Format votes - only show if available
                    votes_str = entry.get('votes', '')
                    label_parts = [section, cat_name]
                    
                    if votes_str:
                        import re
                        nums = [int(s) for s in re.findall(r'\b\d+\b', str(votes_str))]
                        if len(nums) >= 2:
                            label_parts.append(f"({nums[0]}/{nums[1]})")
                        elif len(nums) == 1:
                            label_parts.append(f"({nums[0]})")
                    
                    label = " - ".join(label_parts)
                    
                    icon = f"special://home/addons/script.parentalguide/resources/skins/Default/media/tags/{cat_name}.png"
                    
                    listitem = xbmcgui.ListItem(label=label)
                    listitem.setArt({'icon': icon, 'thumb': icon})
                    listitem.setProperty('cat_index', str(i + 1))
                    
                    # Store description, but handle empty/None cases
                    desc = entry.get('description', '')
                    if desc and desc.strip() and desc.lower() not in ['none', 'n/a']:
                        listitem.setProperty('description', desc)
                    else:
                        listitem.setProperty('description', '')  # Empty description
                    
                    category_list.addItem(listitem)
                
                # Set focus to first item and update description
                if category_list.size() > 0:
                    category_list.selectItem(0)
                    first_item = category_list.getSelectedItem()
                    if first_item:
                        desc = first_item.getProperty('description')
                        if desc:
                            import html
                            desc = html.unescape(str(desc))
                            w.setProperty("ParentalGuide.Desc.Summary", desc)
                            textbox = self.getControl(5)
                            textbox.setText(desc)
                
                log(f"SummaryViewer: Category list rebuilt for {provider_key} with {category_list.size()} items")
            else:
                log(f"SummaryViewer: No cached data found for {provider_key}")
                # Show empty message
                w.setProperty("ParentalGuide.Desc.Summary", f"No parental guide data available from {provider_key}")
                textbox = self.getControl(5)
                textbox.setText(f"No parental guide data available from {provider_key}")
                
        except Exception as e:
            log(f"SummaryViewer: Error rebuilding category list for {provider_key}: {str(e)}")
            import traceback
            log(traceback.format_exc())
    
    def onClick(self, controlID):
        """Handle click events on controls"""
        if controlID == 4400:  # Provider list clicked
            try:
                provider_list = self.getControl(4400)
                selected_item = provider_list.getSelectedItem()
                provider_key = selected_item.getProperty('provider_key')
                if provider_key:
                    w = xbmcgui.Window(10000)
                    
                    log(f"SummaryViewer: Provider {provider_key} clicked, switching to display its data")
                    
                    # Just switch which provider's data we're displaying (data already fetched by NudityCheck.py)
                    w.setProperty("SelectedProvider", provider_key)
                    
                    # Rebuild category list with this provider's data
                    self._rebuildCategoryListForProvider(provider_key)
                    
                    # Update textbox with first category's description
                    self._updateTextbox()
                    
                    log(f"SummaryViewer: Switched to provider {provider_key}")
            except Exception as e:
                log(f"SummaryViewer: Error handling provider click: {str(e)}")
        elif controlID == 4500:  # Category list clicked
            try:
                category_list = self.getControl(4500)
                selected_item = category_list.getSelectedItem()
                cat_index = selected_item.getProperty('cat_index')
                if cat_index:
                    w = xbmcgui.Window(10000)
                    w.setProperty("SelectedCat", cat_index)
                    desc = w.getProperty(f"ParentalGuide.Desc.{cat_index}")
                    if desc:
                        w.setProperty("ParentalGuide.Desc.Summary", desc)
                        w.setProperty("ParentalGuide.RefreshTextbox", str(xbmc.getInfoLabel("System.Time")))
                        log(f"SummaryViewer: Category {cat_index} selected")
            except Exception as e:
                log(f"SummaryViewer: Error handling category click: {str(e)}")
    
    def onFocus(self, controlID):
        """Handle focus events on controls"""
        if controlID == 4400:  # Provider list focused
            # Update categories when provider focus changes
            try:
                provider_list = self.getControl(4400)
                selected_item = provider_list.getSelectedItem()
                if not selected_item:
                    return
                    
                provider_key = selected_item.getProperty('provider_key')
                has_data = selected_item.getProperty('has_data')
                
                if provider_key:
                    w = xbmcgui.Window(10000)
                    w.setProperty("SelectedProvider", provider_key)
                    
                    log(f"SummaryViewer: Provider {provider_key} focused (has_data={has_data}), updating categories")
                    
                    # Always clear previous data first
                    w.clearProperty("ParentalGuide.Desc.Summary")
                    textbox = self.getControl(5)
                    textbox.setText("")
                    
                    category_list = self.getControl(4500)
                    category_list.reset()
                    
                    # Rebuild category list with this provider's data only if has data
                    if has_data == "True":
                        self._rebuildCategoryListForProvider(provider_key)
                    else:
                        log(f"SummaryViewer: Provider {provider_key} has no data, categories cleared")
            except Exception as e:
                log(f"SummaryViewer: Error in provider onFocus: {str(e)}")
                import traceback
                log(traceback.format_exc())
        
        elif controlID == 4500:  # Category list focused
            # Update textbox when category focus changes
            try:
                category_list = self.getControl(4500)
                selected_item = category_list.getSelectedItem()
                w = xbmcgui.Window(10000)
                textbox = self.getControl(5)
                
                if selected_item:
                    cat_index = selected_item.getProperty('cat_index')
                    desc = selected_item.getProperty('description')
                    
                    # Clear first, then set if we have data
                    w.clearProperty("ParentalGuide.Desc.Summary")
                    textbox.setText("")
                    
                    if desc and desc.strip():
                        import html
                        desc = html.unescape(str(desc))
                        w.setProperty("ParentalGuide.Desc.Summary", desc)
                        textbox.setText(desc)
                        log(f"SummaryViewer: Category at index {cat_index} focused, textbox updated")
                    else:
                        log(f"SummaryViewer: Category at index {cat_index} has no description, cleared")
                else:
                    # No item selected, clear everything
                    w.clearProperty("ParentalGuide.Desc.Summary")
                    textbox.setText("")
            except Exception as e:
                log(f"SummaryViewer: Error in category onFocus: {str(e)}")
                import traceback
                log(traceback.format_exc())

    # Set all the values to display on the property screen
    def _setProperties(self, details):
        w = xbmcgui.Window(10000)
        for i, entry in enumerate(details):
            y = i + 1
            w.setProperty(f"ParentalGuide.{y}.Section", str(entry.get('name', '')))
            w.setProperty(f"ParentalGuide.Cat.Name.{y}", str(entry.get('cat', 'N/A')))
            
            Description = entry.get('description', 'No description available.')
            if Description:
                Description = html.unescape(str(Description))
            
            w.setProperty(f"ParentalGuide.Desc.{y}", Description)
            w.setProperty(f"ParentalGuide.Votes.{y}", str(entry.get('votes', '')))
            
            try:
                votes_str = str(entry.get('votes', ''))
                MainVotes = [int(s) for s in re.findall(r'\b\d+\b', votes_str)]
                if len(MainVotes) >= 2:
                    w.setProperty(f"ParentalGuide.MVotes.{y}", f"{MainVotes[0]}/{MainVotes[1]}")
                elif len(MainVotes) == 1:
                    w.setProperty(f"ParentalGuide.MVotes.{y}", f"{MainVotes[0]}")
                else:
                    w.setProperty(f"ParentalGuide.MVotes.{y}", "N/A")
            except:
                w.setProperty(f"ParentalGuide.MVotes.{y}", "N/A")
            
            w.setProperty(f"ParentalGuide.Cat.{y}", f"special://home/addons/script.parentalguide/resources/skins/Default/media/tags/{str(entry.get('cat', 'NA'))}.png")
        
        summary_desc = details[0].get('description', 'No description available.')
        w.setProperty("ParentalGuide.Desc.Summary", html.unescape(str(summary_desc)))
        w.setProperty("ParentalGuide.title", 'Summary Title')
    
    def _updateProperties(self, item, val): 
                xbmcgui.Window(10000).setProperty(item, val)
                
    def add_items(self,_id, items):
        self.getControl(_id).addItems(items)
    
    def make_parentsguide(self, details):
        #if not 4500 in self.enabled_lists: return
        def builder():
            for item in details:
                try:
                    listitem = self.make_listitem()
                    name = item['name']
                    ranking = item['cat']
                    # if item['listings']:
                        # ranking += ' (x%02d)' % len(item['listings'])
                    icon = "tags/" + item['cat']+ ".png"
                    listitem.setProperty('parental.guide.name', name)
                    listitem.setProperty('parental.guide.ranking', ranking)
                    listitem.setProperty('parental.guide.thumb', icon)
                    listitem.setProperty('parental.guide.description', item['description'])
                    yield listitem
                except: pass
        try:
            item_list = list(builder())
            self.setProperty('parental.guide.imdb_parentsguide.number', '(x%02d)' % len(item_list))
            # self.item_action_dict[parentsguide_id] = 'parental.guide.listings'
            self.add_items(4500, item_list)
        except: pass
	
    def makebold(string, keyword):
        return string.replace(keyword,("[B]" + keyword + "[/B]"))
        
    def make_listitem():
        return xbmcgui.ListItem(offscreen=True)
######################################
# Details listing screen
######################################
class DetailViewer(ParentalGuideViewer):
    # TEXT_BOX_ID = 202
    TEXT_BOX_ID = 5

    def __init__(self, *args, **kwargs):
        self.content = kwargs.get('content', '')
        ParentalGuideViewer.__init__(self, *args, **kwargs)

    @staticmethod
    def createDetailViewer(switchText, title, content):
        return DetailViewer("DialogTextViewer", CWD, switchText=switchText, title=title, content=content)

    # Called when setting up the window
    def onInit(self):
        # Fill in the text for the details
        textControl = self.getControl(DetailViewer.TEXT_BOX_ID)
        textControl.setText(self.content)
        ParentalGuideViewer.onInit(self)
