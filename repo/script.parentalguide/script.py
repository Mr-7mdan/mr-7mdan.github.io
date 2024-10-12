# -*- coding: utf-8 -*-
import xbmcgui
import xbmcaddon
import sys
import xbmc
import traceback
from resources.lib.settings import Settings
from resources.lib.settings import log
from NudityCheck import getData
import requests
from resources.lib.viewer import SummaryViewer

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')
log("Viewer opened")

def _setProperties(details):
    for i, entry in enumerate(details):
        if i < 9:
            y = i + 1
            xbmcgui.Window(10000).setProperty(f"ParentalGuide.{y}.Section", str(entry['name']))
            xbmcgui.Window(10000).setProperty(f"ParentalGuide.Cat.Name.{y}", str(entry['cat']))
            
            Description = entry['description']
            if Description not in [None, "", " "]:
                if i > 0:
                    PreviousDesc = details[i-1]['description']
                    if PreviousDesc not in [None, "", " "]:
                        Description = Description.replace(PreviousDesc, "")
                    else:
                        Description = ""
                BoldKeywords = ["bare breasts", "nipples ", "penis ", "Penis ", "dick ", "intercourse ", "making love", "sucking ", "blowjob ", "anal", "Blowjob ", "Anal", "sex scene", "buttock ", "rape ", "raping", "raped ", "sex scenes", "having sex", "nudity ", "nude", "naked", "boob", "breast"]
                for word in BoldKeywords:
                    Description = Description.replace(word, f"[B]{word}[/B]")
            
            xbmcgui.Window(10000).setProperty(f"ParentalGuide.Desc.{y}", str(Description))
            xbmcgui.Window(10000).setProperty(f"ParentalGuide.Votes.{y}", str(entry['votes']))
            
            try:
                MainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                xbmcgui.Window(10000).setProperty(f"ParentalGuide.MVotes.{y}", f"{MainVotes[0]}/{MainVotes[1]}")
            except:
                pass
            
            xbmcgui.Window(10000).setProperty(f"ParentalGuide.Cat.{y}", f"tags/{str(entry['cat'])}.png")
    
    xbmcgui.Window(10000).setProperty("ParentalGuide.Desc.Summary", str(details[0]['description']))
    xbmcgui.Window(10000).setProperty("ParentalGuide.title", 'Summary Title')

def _clearProperties():
    for i in range(1, 21):
        xbmcgui.Window(10000).clearProperty(f"ParentalGuide.{i}.Section")
        xbmcgui.Window(10000).clearProperty(f"ParentalGuide.Cat.Name.{i}")
        xbmcgui.Window(10000).setProperty(f"ParentalGuide.Desc.{i}", "")
        xbmcgui.Window(10000).clearProperty(f"ParentalGuide.Votes.{i}")
        xbmcgui.Window(10000).clearProperty(f"ParentalGuide.MVotes.{i}")
        xbmcgui.Window(10000).clearProperty(f"ParentalGuide.Cat.{i}")
    
    xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.Summary")

if __name__ == '__main__':
    xbmcgui.Window(10025).setProperty("ParentalGuideTestContextMenu", "true")

    IMDBID = xbmcgui.Window(10000).getProperty("CurrentId")
    videoName = xbmcgui.Window(10000).getProperty("CurrentItem")

    xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.section") 
    xbmcgui.Window(10000).clearProperty("ParentalGuide.Desc.Summary") 
        
    provider = xbmcgui.Window(10000).getProperty("SelectedProvider")
    cont = xbmcgui.Window(10000).getProperty("SelectedContainer")

    if cont == "ProviderCont":
        _clearProperties()
            
        s = requests.Session()
        wid = xbmcgui.getCurrentWindowId()
        newdata = getData(videoName, IMDBID, s, wid, provider, 1)
        
        if newdata is not None and 'review-items' in newdata and newdata['review-items'] not in [None, "", " "]:
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('ParentalGuide', f"Selected: {provider}", ADDON.getAddonInfo('icon')))
            _setProperties(newdata['review-items'])
            viewer = SummaryViewer("summary.xml", CWD, title=videoName, details=newdata)
            viewer.doModal()
            del viewer
        else:
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('ParentalGuide', f"No data found for {provider}", ADDON.getAddonInfo('icon')))
    else:
        cat = xbmcgui.Window(10000).getProperty("SelectedCat") 
        if cat:
            DescProperty = f"ParentalGuide.Desc.{cat}"
            SecProperty = f"ParentalGuide.{cat}.Section"
            CatIcon = f"ParentalGuide.Cat.{cat}"
            CatProperty = f"ParentalGuide.Cat.Name.{cat}"
            VotesProperty = f"ParentalGuide.Votes.{cat}"

            FinalPiece = xbmcgui.Window(10000).getProperty(DescProperty)
            FinalSection = xbmcgui.Window(10000).getProperty(SecProperty)
            FinalCat = xbmcgui.Window(10000).getProperty(CatProperty)
            FinalIcon = xbmcgui.Window(10000).getProperty(CatIcon)
            FinalVotes = xbmcgui.Window(10000).getProperty(VotesProperty)

            xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.Summary', str(FinalPiece))
            xbmcgui.Window(10000).setProperty('ParentalGuide.Desc.section', str(FinalSection))
            xbmcgui.Window(10000).setProperty('ParentalGuide.Sec.Cat', str(FinalCat))
            xbmcgui.Window(10000).setProperty('ParentalGuide.Sec.Cat.Icon', str(FinalIcon))
            xbmcgui.Window(10000).setProperty('ParentalGuide.Votes.section', str(FinalVotes))

            # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('ParentalGuide', f"Showing details for {FinalSection}", ADDON.getAddonInfo('icon')))

    xbmcgui.Window(10000).clearProperty("SelectedContainer")
    xbmcgui.Window(10000).clearProperty("SelectedProvider")
    xbmcgui.Window(10000).clearProperty("SelectedCat")