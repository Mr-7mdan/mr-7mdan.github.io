# -*- coding: utf-8 -*-
#import sys
#import xbmc
import xbmcgui

#########################
# Main
#########################
if __name__ == '__main__':
    wid = xbmcgui.getCurrentWindowId()
    
    Properties = ["NVotes","NIcon","NRate","Age","Icon","Status"]
    ProvidersList = ["IMDB","KidsInMind","RaisingChildren","CSM","MovieGuide","DoveFoundation","ParentPreviews"]
    
    for provider in ProvidersList:
        for prop in Properties:
            xbmcgui.Window(wid).clearProperty(provider+"-"+prop)
    
