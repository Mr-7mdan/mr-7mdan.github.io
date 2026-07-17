# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import traceback
import json
from threading import Thread
from datetime import datetime, timedelta
from resources.lib import imdb
import re
from resources.lib.settings import log
# # from apis import tmdb_api, imdb_api
# import metadata
# from windows import BaseDialog
# # from indexers import dialogs, people
# # from indexers.images import Images
# # from modules import settings
# from modules.meta_lists import networks
# # from modules.utils import get_datetime
# from modules.kodi_utils import translate_path, close_all_dialog, hide_busy_dialog, ok_dialog, local_string as ls
# # from modules.settings_reader import get_setting

# # Import the common settings
# # from settings import log

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")
# log("Viewer opened")

# reviews_id, trivia_id, blunders_id, parentsguide_id = 2052, 2053, 2054, 2055
# imdb_list_ids = (reviews_id, trivia_id, blunders_id, parentsguide_id)
# parentsguide_levels = {'mild': ls(32996), 'moderate': ls(32997), 'severe': ls(32998)}
# parentsguide_inputs = {'Sex & Nudity': (ls(32990), 'adult.png'), 'Violence & Gore': (ls(32991), 'genre_war.png'), 'Profanity': (ls(32992), 'bad_language.png'),
						# 'Alcohol, Drugs & Smoking': (ls(32993), 'drugs_alcohol.png'), 'Frightening & Intense Scenes': (ls(32994), 'genre_horror.png')}
# info_action = xbmcgui.ACTION_SHOW_INFO
# closing_actions = (xbmcgui.ACTION_PARENT_DIR, xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_STOP, xbmcgui.ACTION_NAV_BACK)
# selection_actions = (xbmcgui.ACTION_SELECT_ITEM, xbmcgui.ACTION_MOUSE_START)
# context_actions = (xbmcgui.ACTION_CONTEXT_MENU, xbmcgui.ACTION_MOUSE_RIGHT_CLICK, xbmcgui.ACTION_MOUSE_LONG_CLICK)
# left_action, right_action = xbmcgui.ACTION_MOVE_LEFT, xbmcgui.ACTION_MOVE_RIGHT
# up_action, down_action = xbmcgui.ACTION_MOVE_UP, xbmcgui.ACTION_MOVE_DOWN

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
        #labelControl = self.getControl(ParentalGuideViewer.TITLE_LABEL_ID)
        #labelControl.setLabel(self.title)
        # labelControl = self.getControl(ParentalGuideViewer.TEXT2_BOX_ID)
        # labelControl.setLabel("TexctBox onLit")
        
        # Set the label on the switch button
        # switchButton = self.getControl(ParentalGuideViewer.SWITCH_BUTTON)
        # if self.switchText in [None, ""]:
            # switchButton.setVisible(False)
        # else:
            # switchButton.setVisible(True)
            # switchButton.setLabel(ADDON.getLocalizedString(self.switchText))
        
        xbmcgui.WindowXMLDialog.onInit(self)
            
    # def onClick(self, controlID):
        # Play button has been clicked
        # if controlID == ParentalGuideViewer.CLOSE_BUTTON:
            # log("ParentalGuideViewer: Close click action received: %d" % controlID)
            # self.close()
        # elif controlID == ParentalGuideViewer.SWITCH_BUTTON:
            # log("ParentalGuideViewer: Switch click action received: %d" % controlID)
            # self.isSwitchFlag = True
            # self.close()
        # elif controlID == ParentalGuideViewer.VIEWER_CHANGE_BUTTON:
            # log("ParentalGuideViewer: Change click action received: %d" % controlID)
            # self.isChangeViewerFlag = True
            # self.close()
        # elif controlID == ParentalGuideViewer.MORE_BUTTON:
            # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "More has been clicked", ADDON.getAddonInfo('icon')))
            # cat = xbmcgui.Window(10000).getProperty("SelectedCat") 
            # # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Selected: " + str(item) , ADDON.getAddonInfo('icon')))
            # DescProperty = ("ParentalGuide.Desc.%s") % cat
            # SecProperty = ("ParentalGuide.Section.%s") % cat
            # FinalPiece = xbmcgui.Window(10000).getProperty(DescProperty)
            # FinalSection = xbmcgui.Window(10000).getProperty(SecProperty)
            # xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.Summary', str(FinalPiece))
            # xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.section', str(FinalSection))
            # #Load Window
            # Snippit = xbmcgui.WindowXMLDialog('Custom_1333_Plot.xml', CWD, text=cat)
            # Snippit.doModal()
            # Snippit.close()
            # xbmcgui.Window(10000).clearProperty("SelectedCat")
#############################################################            
        #TextViwer button
        # elif controlID == ParentalGuideViewer.TEXTVIEWER_BTN:
            # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "TEXTVIEWER_BTN was clicked", ADDON.getAddonInfo('icon')))
            # Snippit = xbmcgui.WindowXMLDialog('Custom_1333_Plot.xml', xbmcaddon.Addon().getAddonInfo('path'), 'default', '1080i')
            # #Snippit = xbmcgui.WindowXMLDialog('summary.xml', xbmcaddon.Addon().getAddonInfo('path'), 'default', '1080i')
            # Snippit.doModal()
            # self.close()
        
        # listitem = snippit.getControl(4500).getSelectedItem()  # get the listitem
        # action = listitem.getProperty('label')  # get the action of the listitem
        # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Property: " + action + "was selected", ADDON.getAddonInfo('icon')))
            # #xbmc.executebuiltin(action)  # execute the action
            
    # def onAction(self, action):
        # #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (action,'', ADDON.getAddonInfo('icon')))
        # closing_actions = (xbmcgui.ACTION_PARENT_DIR, xbmcgui.ACTION_PREVIOUS_MENU, xbmcgui.ACTION_STOP, xbmcgui.ACTION_NAV_BACK)
        # if action in closing_actions: self.close()
        # # if controlID == 4500:
            # # listings = json.loads(chosen_var)
            # # if not listings: return
            # # chosen_var = '\n\n'.join(['%02d. %s' % (count, i) for count, i in enumerate(listings, 1)])
        # j=0
        # for row in self.details:
            # if details[j]['name'] == controlID.getLabel():
                # k = i+1
                # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('k', str(k), ADDON.getAddonInfo('icon')))
            # else:
                # pass
        # j = j+1    
            
            # #self.open_window(('windows.extras', 'ShowTextMedia'), 'textviewer_media.xml', text=chosen_var, poster=self.poster)    
        # Snippit = xbmcgui.WindowXMLDialog('Custom_1333_Plot.xml', CWD, 'default', '1080i')
        # Snippit.doModal()

        
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

    # @staticmethod
    # def createSummaryViewer(switchText, title, details):
        # return SummaryViewer("script-ParentalGuide-summary.xml", CWD, switchText=switchText, title=title, details=details)


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
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "onfocus: " + str(controlID) + "-" + str(item) + "-" + str(cid), ADDON.getAddonInfo('icon')))
        

        
    #def onClick(self, controlID):
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Clicked: " + str(controlID), ADDON.getAddonInfo('icon')))
    # Set all the values to display on the property screen
    def _setProperties(self, details):
        i = 0
        for entry in details:
            if i < 9:
                    y = i + 1
                    sectionTag = "ParentalGuide.%s.Section" % y
                    ratingTag = "ParentalGuide.%s.Rating" % y
                    
                    xbmcgui.Window(10000).setProperty(sectionTag, str(details[i]['name']))
                                 
                    cattag = 'ParentalGuide.Cat.Name.%s' % y
                    xbmcgui.Window(10000).setProperty(cattag , str(details[i]['cat']))
                    
                    Description = ''
                    
                    Description = details[i]['description']
                    
                    if i>0:
                        PreviousDesc = details[i-1]['description']
                        Description = Description.replace(PreviousDesc,"")
                    BoldKeywords = ["bare breasts", "nipples ", "penis ", "Penis ", "dick ", "intercourse ", "making love", "sucking ", "blowjob ", "anal", "Blowjob ", "Anal", "sex scene", "buttock ", "rape ", "raping", "raped ", "sex scenes", "having sex", "nudity ", "nude", "naked", "boob", "breast"]                 
                    for word in BoldKeywords:
                        Description = Description.replace(word,"[B]" + word + "[/B]")
                                        
                    DescProperty = "ParentalGuide.Desc.%s" % y
                    xbmcgui.Window(10000).setProperty(DescProperty, str(Description))
                    
                    DescSumProperty = "ParentalGuide.Desc.Summary"
                    xbmcgui.Window(10000).setProperty(DescSumProperty, str(details[0]['description']))
                    
                    #self.setProperty(DescProperty, details[i]['description'])
                    
                    SectionVotesProperty = "ParentalGuide.Votes.%s" % y
                    xbmcgui.Window(10000).setProperty(SectionVotesProperty, str(details[i]['votes']))
                    #self.setProperty(DescProperty, details[i]['description'])
                    
                    try:
                        MainVotes = [int(s) for s in re.findall(r'\b\d+\b', details[i]['votes'])]
                        MainVotesProperty = ("ParentalGuide.MVotes.%s") % y
                        xbmcgui.Window(10000).setProperty(MainVotesProperty, (str(MainVotes[0]) + "/" + str(MainVotes[1])) )
                    except:
                        pass
                        
                    CatRating = ("ParentalGuide.Cat.%s") % y
                    xbmcgui.Window(10000).setProperty(CatRating, "tags/" + str(details[i]['cat']) + ".png")
                    
                    # xbmcgui.Window(10000).listitem.setProperty('action', 'RunScript(script.ShowInfo)')
                    # listitem.setProperty('action', 'RunScript(script.ShowInfo)')
                    
                    # if "Sex" in details[i]['name']:
                        # xbmcgui.Window(10000).setProperty("Nvotes", (str(MainVotes[0]) + "/" + str(MainVotes[1])))
                        # xbmcgui.Window(10000).setProperty("Nicon", "tags/" + str(details[i]['cat']) + ".png")
                    
                    
            i = i + 1
        xbmcgui.Window(10000).setProperty("ParentalGuide.title", 'Summary Title')
        #xbmcgui.Window(10000).setProperty("ParentalGuide.provider", details[0]['provider'])
    
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

# ##############
# class Extras(BaseDialog):
	# def __init__(self, *args, **kwargs):
		# BaseDialog.__init__(self, args)
		# self.control_id = None
		# #self.set_starting_constants(kwargs)
		# #self.set_properties()

	# def onInit(self):
		 # tasks = (self.make_parentsguide, self.make_reviews, self.make_trivia, self.make_blunders)
        # # tasks = (self.make_parentsguide, self.make_reviews, self.make_trivia, self.make_blunders)
		 # [Thread(target=i).start() for i in tasks]
		# # for i in ('posters', 'backdrops'): Thread(target=self.make_artwork, args=(i,)).start()
		# # if self.media_type == 'movie': Thread(target=self.make_collection).start()
		# # else: self.setProperty('parental.guide.make.collection', 'false')

	# def run(self):
		# self.doModal()
		# self.clearProperties()
		# hide_busy_dialog()
		# if self.selected: self.execute_code(self.selected)
        
	# def make_parentsguide(self, imdbid):
		# # if not parentsguide_id in self.enabled_lists: return
		# def builder():
			# for item in data:
				# try:
					# listitem = self.make_listitem()
					# name = parentsguide_inputs[item['title']][0]
					# ranking = parentsguide_levels[item['ranking'].lower()].upper()
					# if item['listings']:
						# ranking += ' (x%02d)' % len(item['listings'])
					# icon = translate_path('special://home/addons/script.ezart/resources/media/%s' % parentsguide_inputs[item['title']][1])
					# listitem.setProperty('parental.guide.name', name)
					# listitem.setProperty('parental.guide.ranking', ranking)
					# listitem.setProperty('parental.guide.thumbnail', icon)
					# listitem.setProperty('parental.guide.listings', json.dumps(item['listings']))
					# #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (name, ranking, ADDON.getAddonInfo('icon')))
					# yield listitem
				# except: pass
		# try:
			# data = imdb_parentsguide(self.imdbid)
			# item_list = list(builder())
			# self.setProperty('parental.guide.imdb_parentsguide.number', '(x%02d)' % len(item_list))
			# #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (len(item_list), "", ADDON.getAddonInfo('icon')))
			# self.item_action_dict[parentsguide_id] = 'parental.guide.listings'
			# self.add_items(parentsguide_id, item_list)
		# except: pass


	# def make_reviews(self):
		# # if not reviews_id in self.enabled_lists: return
		# def builder():
			# for count, item in enumerate(data, 1):
				# try:
					# listitem = self.make_listitem()
					# if item['spoiler']: content = '[B][COLOR red][%s][/COLOR][CR]%02d. [I]%s - %s - %s[/I][/B]\n\n%s' \
													# % (spoiler, count, item['rating'], item['date'], item['title'], item['content'])
					# else: content = '[B]%02d. [I]%s - %s - %s[/I][/B]\n\n%s' % (count, item['rating'], item['date'], item['title'], item['content'])
					# listitem.setProperty('parental.guide.text', content)
					# yield listitem
				# except: pass
		# try:
			# spoiler = ls(32985).upper()
			# data = imdb_reviews(self.imdb_id)
			# item_list = list(builder())
			# self.setProperty('parental.guide.imdb_reviews.number', '(x%02d)' % len(item_list))
			# self.item_action_dict[reviews_id] = 'parental.guide.text'
			# self.add_items(reviews_id, item_list)
		# except: pass

	# def make_trivia(self):
		# # if not trivia_id in self.enabled_lists: return
		# def builder():
			# for count, item in enumerate(data, 1):
				# try:
					# listitem = self.make_listitem()
					# listitem.setProperty('parental.guide.text', '[B]%s %02d.[/B][CR][CR]%s' % (trivia, count, item))
					# yield listitem
				# except: pass
		# try:
			# trivia = ls(32984).upper()
			# data = imdb_trivia(self.imdb_id)
			# item_list = list(builder())
			# self.setProperty('parental.guide.imdb_trivia.number', '(x%02d)' % len(item_list))
			# self.item_action_dict[trivia_id] = 'parental.guide.text'
			# self.add_items(trivia_id, item_list)
		# except: pass

	# def make_blunders(self):
		# # if not blunders_id in self.enabled_lists: return
		# def builder():
			# for count, item in enumerate(data, 1):
				# try:
					# listitem = self.make_listitem()
					# listitem.setProperty('parental.guide.text', '[B]%s %02d.[/B][CR][CR]%s' % (blunders, count, item))
					# yield listitem
				# except: pass
		# try:
			# blunders = ls(32986).upper()
			# data = imdb_blunders(self.imdb_id)
			# item_list = list(builder())
			# self.setProperty('parental.guide.imdb_blunders.number', '(x%02d)' % len(item_list))
			# self.item_action_dict[blunders_id] = 'parental.guide.text'
			# self.add_items(blunders_id, item_list)
		# except: pass



	# def listitem_check(self):
		# return self.get_infolabel('ListItem.Title') == self.meta['title']

	# def add_items(self,_id, items):
		# self.getControl(_id).addItems(items)
        

	# # def set_properties(self):
		# # self.setProperty('parental.guide.media_type', self.media_type)
		# # self.setProperty('parental.guide.fanart', self.fanart)
		# # self.setProperty('parental.guide.clearlogo', self.clearlogo)
		# # self.setProperty('parental.guide.title', self.title)
		# # self.setProperty('parental.guide.plot', self.plot)
		# # self.setProperty('parental.guide.year', self.year)
		# # self.setProperty('parental.guide.rating', self.rating)
		# # self.setProperty('parental.guide.mpaa', self.mpaa)
		# # self.setProperty('parental.guide.status', self.status)
		# # self.setProperty('parental.guide.genre', self.genre)
		# # self.setProperty('parental.guide.network', self.network)
		# # self.setProperty('parental.guide.duration', self.duration)
		# # self.setProperty('parental.guide.progress', self.progress)
		# # self.setProperty('parental.guide.finish_watching', self.finish_watching)
		# # self.setProperty('parental.guide.last_aired_episode', self.last_aired_episode)
		# # self.setProperty('parental.guide.next_aired_episode', self.next_aired_episode)
		# # self.setProperty('parental.guide.next_episode', self.next_episode)
		# # self.setProperty('parental.guide.enable_scrollbars', self.enable_scrollbars)
		# # self.setProperty('parental.guide.highlight',self.highlight)
# #