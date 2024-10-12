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
        xbmcgui.WindowXMLDialog.__init__(self)

    # Called when setting up the window
    def onInit(self):
        # Update the dialog to show the correct data
        xbmcgui.Window(10000).clearProperty("SelectedCat") 
        xbmcgui.WindowXMLDialog.onInit(self)
            
    def close(self):
        log("ParentalGuideViewer: Closing window")
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
        if self.details not in [None, ""]:
            self._setProperties(self.details['review-items'])

        ParentalGuideViewer.__init__(self, *args, **kwargs)

    @staticmethod
    def createSummaryViewer(title, details):
        return SummaryViewer("summary.xml", CWD, title=title, details=details)

    def close(self):
        log("ParentalGuideViewer: Closing window")
        # Clear all the properties that were previously set
        i = 1
        while i < 9:
            xbmcgui.Window(10000).clearProperty("ParentalGuide.%s.Section" % i)
            xbmcgui.Window(10000).clearProperty("ParentalGuide.%s.Rating" % i)
            xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.%s" % i)
            i = i + 1
        xbmcgui.Window(10000).clearProperty("SelectedCat") 
        xbmcgui.Window(10000).clearProperty("SelectedProvider")
        xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.section") 
        xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.Summary") 
        ParentalGuideViewer.close(self)
        
    def onInit(self):
        # #Fill in the text for the details
        # item_list = self.details
        # self.win = self.getControl(self.window_id)
        # self.win.addItems(self.item_list)
        # self.getControl(4500).addItems(item_list)
        # make_parentsguide(self.details)
        ParentalGuideViewer.onInit(self)
       
    
    def onFocus(self, controlID):
        #if controlID ==4500:
        wid = xbmcgui.getCurrentWindowId()
        win = xbmcgui.Window(wid)
        cid = win.getFocusId()
        control = win.getFocus()
        item = control.getSelectedPosition() #getSelectedItem()

    # Set all the values to display on the property screen
    def _setProperties(self, details):
        for i, entry in enumerate(details, 1):
            if i > 9:
                break
            
            sectionTag = f"ParentalGuide.{i}.Section"
            cattag = f'ParentalGuide.Cat.Name.{i}'
            DescProperty = f"ParentalGuide.Desc.{i}"
            SectionVotesProperty = f"ParentalGuide.Votes.{i}"
            MainVotesProperty = f"ParentalGuide.MVotes.{i}"
            CatRating = f"ParentalGuide.Cat.{i}"
            
            xbmcgui.Window(10000).setProperty(sectionTag, str(entry.get('name', '')))
            xbmcgui.Window(10000).setProperty(cattag, str(entry.get('cat', 'N/A')))
            
            Description = entry.get('description', '')
            if Description is not None:
                BoldKeywords = ["bare breasts", "nipples ", "penis ", "Penis ", "dick ", "intercourse ", "making love", "sucking ", "blowjob ", "anal", "Blowjob ", "Anal", "sex scene", "buttock ", "rape ", "raping", "raped ", "sex scenes", "having sex", "nudity ", "nude", "naked", "boob", "breast"]
                for word in BoldKeywords:
                    Description = Description.replace(word, f"[B]{word}[/B]")
            else:
                Description = "No description available."
            
            xbmcgui.Window(10000).setProperty(DescProperty, str(Description))
            xbmcgui.Window(10000).setProperty(SectionVotesProperty, str(entry.get('votes', '')))
            
            try:
                MainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry.get('votes', ''))]
                xbmcgui.Window(10000).setProperty(MainVotesProperty, f"{MainVotes[0]}/{MainVotes[1]}")
            except:
                xbmcgui.Window(10000).setProperty(MainVotesProperty, "N/A")
            
            xbmcgui.Window(10000).setProperty(CatRating, f"tags/{str(entry.get('cat', 'NA'))}.png")
        
        xbmcgui.Window(10000).setProperty("ParentalGuide.Desc.Summary", str(details[0].get('description', 'No description available.')))
        xbmcgui.Window(10000).setProperty("ParentalGuide.title", 'Summary Title')
    
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
