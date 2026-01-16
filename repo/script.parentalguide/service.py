# -*- coding: utf-8 -*-
import xbmcgui

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.settings import log

# Import the background monitor
import service_monitor


###################################
# Main of the ParentalGuide Service
###################################
if __name__ == '__main__':
    log("ParentalGuide: Starting service")

    # Record if the Context menu should be displayed
    if not Settings.showOnContextMenu():
        log("ParentalGuide: Hiding context menu")
        xbmcgui.Window(10025).setProperty("ParentalGuideHideContextMenu", "true")
    else:
        log("ParentalGuide: Showing context menu")
        xbmcgui.Window(10025).clearProperty("ParentalGuideHideContextMenu")

    xbmcgui.Window(10025).setProperty("ParentalGuideTestContextMenu", "true")
    
    # Start the background monitor for automatic parental guide updates
    log("ParentalGuide: Starting background monitor")
    service_monitor.start_monitor()