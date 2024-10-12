# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
import requests

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.viewer import DetailViewer
from resources.lib.viewer import SummaryViewer
from resources.lib.settings import log
from NudityCheck import getData, getIMDBID, API_BASE_URL

if sys.version_info >= (2, 7):
    import json
else:
    import simplejson as json

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")
log("Viewer opened")


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

def runForVideo(videoName, isTvShow=False):
    log("ParentalGuideCore: Video Name = %s" % videoName)
    # Get the initial Source to use
    searchSource = Settings.getDefaultSource()
    selectedViewer = Settings.getDefaultViewer()

    while searchSource is not None:
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        try:
            params = {
                "video_name": videoName,
                "provider": searchSource.lower()
            }
            response = requests.get(API_BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data and 'review-items' in data:
                selectedItem = {
                    'name': data.get('title', videoName),
                    'link': data.get('review-link', '')
                }
                details = {
                    'review-items': data['review-items'],
                    'recommended-age': None,  # API doesn't provide this
                    'review-link': data.get('review-link')
                }
            else:
                selectedItem = None
                details = None

        except requests.RequestException as e:
            log("runForVideo: Failed to fetch data from API: %s" % str(e), xbmc.LOGERROR)
            xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (ADDON.getLocalizedString(32001).encode('utf-8'), ADDON.getLocalizedString(32037).encode('utf-8'), ADDON.getAddonInfo('icon')))
            selectedItem = None
            details = None

        xbmc.executebuiltin("Dialog.Close(busydialog)")

        # Work out what provider we would switch to if the user wants to switch
        switchSource = Settings.getNextSource(searchSource)

        if selectedItem is None:
            # Offer searching by the other provider if there is one
            if switchSource is not None:
                msg1 = "%s %s" % (ADDON.getLocalizedString(32005), videoName)
                msg2 = "%s %s" % (ADDON.getLocalizedString(32010), ADDON.getLocalizedString(switchSource))
                switchSearch = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32001), msg1, msg2)
                # If the user wants to switch the search then tidy up then loop again
                if switchSearch:
                    searchSource = switchSource
                else:
                    searchSource = None
            else:
                searchSource = None
        else:
            displayTitle = "%s: %s" % (ADDON.getLocalizedString(searchSource), selectedItem['name'])
            log("ParentalGuide: Found content with name: %s" % selectedItem['name'])

            if details is not None:
                # Allow TvTunes to continue playing
                xbmcgui.Window(12000).setProperty("TvTunesContinuePlaying", "True")

                changingViewer = True
                while changingViewer:
                    viewer = None
                    # Create the type of viewer we need
                    if selectedViewer == Settings.VIEWER_DETAILED:
                        viewer = DetailViewer.createDetailViewer(switchSource, displayTitle, details)
                    else:
                        viewer = SummaryViewer.createSummaryViewer(switchSource, displayTitle, details["review-items"])

                    # Display the viewer
                    viewer.doModal()

                    # Dialog has been exited, check if we need to reload with a different view
                    changingViewer = viewer.isChangeViewer()
                    if changingViewer:
                        if selectedViewer == Settings.VIEWER_DETAILED:
                            selectedViewer = Settings.VIEWER_SUMMARY
                        else:
                            selectedViewer = Settings.VIEWER_DETAILED
                    else:
                        # Check if the user wants to just switch providers
                        if viewer.isSwitch():
                            searchSource = switchSource
                        else:
                            searchSource = None
                    del viewer

                # No need to force TvTunes now we have closed the dialog
                xbmcgui.Window(12000).clearProperty("TvTunesContinuePlaying")
            else:
                searchSource = None

#########################
# Main
#########################
if __name__ == '__main__':
    log("ParentalGuide: Started")

    videoName = None
    isTvShow = getIsTvShow()

    # First check to see if we have a TV Show of a Movie
    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")

    # If we do not have the title yet, get the default title
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
         
    dialog = xbmcgui.WindowXMLDialog("Summary.xml", xbmcaddon.Addon(id='script.parentalguide').getAddonInfo('path'), 'default', '1080i')
    dialog.doModal()
    del dialog
