# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import traceback
# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")
log("Viewer opened")

###################################
# Main of the ParentalGuide Service
###################################

ADDON = xbmcaddon.Addon(id='script.parentalguide')

if __name__ == '__main__':
    xbmcgui.Window(10025).setProperty("ParentalGuideTestContextMenu", "true")

# wid = xbmcgui.getCurrentWindowId()
# win = xbmcgui.Window(wid)
# cid = win.getFocusId()
# control = cid.getFocus()
# item = control.getSelectedItem() #.getProperty("SelectedCat") #.getSelectedPosition
# Pos = xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocus().getSelectedPosition
# Item = self.listitem.getProperty('SelectedCat')

xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.section") 
xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.Summary") 
        
cat = xbmcgui.Window(10000).getProperty("SelectedCat") 
# xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Selected: " + str(item) , ADDON.getAddonInfo('icon')))
DescProperty = ("ParentalGuide.Desc.%s") % cat
SecProperty = ("ParentalGuide.%s.Section") % cat 
FinalPiece = xbmcgui.Window(10000).getProperty(DescProperty)
FinalSection = xbmcgui.Window(10000).getProperty(SecProperty)
xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.Summary', str(FinalPiece))
xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.section', str(FinalSection))


VotesProperty = ("ParentalGuide.Votes.%s") % cat
FinalVotes = xbmcgui.Window(10000).getProperty(VotesProperty)
xbmcgui.Window(10000).setProperty('ParentalGuide.Votes.section', str(FinalVotes))
#Load Window
Snippit = xbmcgui.WindowXMLDialog('Custom_1333_Plot.xml', CWD, text=cat)
Snippit.doModal()