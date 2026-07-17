# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import traceback
# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log
from resources.lib.NudityCheck import getData
import requests
from resources.lib.viewer import SummaryViewer

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")
log("Viewer opened")

###################################
# Main of the ParentalGuide Service
###################################

ADDON = xbmcaddon.Addon(id='script.parentalguide')

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

def _setProperties(details):
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
                
                if Description not in [None,""," "]:
                    if i>0:
                        PreviousDesc = details[i-1]['description']
                        
                        if PreviousDesc not in [None,""," "]: 
                            Description = Description.replace(PreviousDesc,"")
                        else:
                            Description = ""
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


def _clearProperties():
    i = 0
    for i in [0,20]:
        if i < 20:
                y = i + 1
                sectionTag = "ParentalGuide.%s.Section" % y
                ratingTag = "ParentalGuide.%s.Rating" % y
                
                xbmcgui.Window(10000).clearProperty(sectionTag)
                             
                cattag = 'ParentalGuide.Cat.Name.%s' % y
                xbmcgui.Window(10000).clearProperty(cattag)
                
                Description = ''
                
                DescProperty = "ParentalGuide.Desc.%s" % y
                xbmcgui.Window(10000).setProperty(DescProperty, "")
                
                DescSumProperty = "ParentalGuide.Desc.Summary"
                xbmcgui.Window(10000).clearProperty(DescSumProperty)
                              
                SectionVotesProperty = "ParentalGuide.Votes.%s" % y
                xbmcgui.Window(10000).clearProperty(SectionVotesProperty)

                MainVotesProperty = ("ParentalGuide.MVotes.%s") % y
                xbmcgui.Window(10000).clearProperty(MainVotesProperty)
                    
                CatRating = ("ParentalGuide.Cat.%s") % y
                xbmcgui.Window(10000).clearProperty(CatRating)

        i = i + 1
  
  
if __name__ == '__main__':
    xbmcgui.Window(10025).setProperty("ParentalGuideTestContextMenu", "true")

    # First check to see if we have a TV Show of a Movie
    IMDBID = videoName = xbmcgui.Window(10000).getProperty("CurrentId")
    #IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
    videoName = xbmcgui.Window(10000).getProperty("CurrentItem")
    
        
# wid = xbmcgui.getCurrentWindowId()
# win = xbmcgui.Window(wid)
# cid = win.getFocusId()
# control = cid.getFocus()
# item = control.getSelectedItem() #.getProperty("SelectedCat") #.getSelectedPosition
# Pos = xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocus().getSelectedPosition
# Item = self.listitem.getProperty('SelectedCat')

xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.section") 
xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.Summary") 
        
provider = xbmcgui.Window(10000).getProperty("SelectedProvider")
cont = xbmcgui.Window(10000).getProperty("SelectedContainer")

if cont == "ProviderCont":
    _clearProperties()
        
    s = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    newdata = getData(videoName, IMDBID, s, wid, provider, 1)
    xbmcgui.Window(10000).close()
    
    if newdata['review-items'] not in [None,""," "]:
        #_setProperties(newdata['review-items'])
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Selected: " + provider , ADDON.getAddonInfo('icon')))
        viewer = SummaryViewer("summary.xml", CWD, title=videoName, details=newdata)
        viewer.doModal()
        del viewer

cat = xbmcgui.Window(10000).getProperty("SelectedCat") 
#xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Hi', "Selected: " + provider , ADDON.getAddonInfo('icon')))

DescProperty = ("ParentalGuide.Desc.%s") % cat
SecProperty = ("ParentalGuide.%s.Section") % cat 
CatIcon = ("ParentalGuide.Cat.%s") % cat
CatProperty = ("ParentalGuide.Cat.Name.%s") % cat
FinalPiece = xbmcgui.Window(10000).getProperty(DescProperty)
FinalSection = xbmcgui.Window(10000).getProperty(SecProperty)
FinalCat = xbmcgui.Window(10000).getProperty(CatProperty)
FinalIcon = xbmcgui.Window(10000).getProperty(CatIcon)

xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.Summary', str(FinalPiece))
xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.section', str(FinalSection))
xbmcgui.Window(10000).setProperty('ParentalGuide.Sec.Cat', str(FinalCat))
xbmcgui.Window(10000).setProperty('ParentalGuide.Sec.Cat.Icon', str(FinalIcon))

VotesProperty = ("ParentalGuide.Votes.%s") % cat
FinalVotes = xbmcgui.Window(10000).getProperty(VotesProperty)
xbmcgui.Window(10000).setProperty('ParentalGuide.Votes.section', str(FinalVotes))


        

#Load Window
# Snippit = xbmcgui.WindowXMLDialog('Custom_1333_Plot.xml', CWD, text=cat)
# Snippit.doModal()