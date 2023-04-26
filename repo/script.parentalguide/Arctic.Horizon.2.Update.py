# -*- coding: utf-8 -*-
import traceback
import xbmc
import xbmcaddon
import xbmcvfs
import xbmcgui
import datetime

# Import the common settings
from resources.lib.settings import log
from resources.lib.settings import os_path_join

ADDON = xbmcaddon.Addon(id='script.parentalguide')


# Ideally we would use an XML parser to do this like ElementTree
# However they all end up re-ordering the attributes, so doing a diff
# between changed files is very hard, so for this reason we do it
# all manually without the aid of an XML parser
class Horizon2Update():
    def __init__(self):
        # Find out where the Horizon2 skin files are located
        skinAddon = xbmcaddon.Addon(id='skin.arctic.horizon.2')
        self.horizon2path = xbmc.translatePath(skinAddon.getAddonInfo('path'))
        self.horizon2path = os_path_join(self.horizon2path, '1080i')
        self.backupPath = xbmc.translatePath(ADDON.getAddonInfo('path'))
        self.backupPath = os_path_join(self.backupPath, 'Arctic.Horizon.2')
        log("Horizon2 Location: %s" % self.horizon2path)
        log("backup Location: %s" % self.backupPath)
        # Create the timestamp centrally, as we want all files changed for a single
        # run to have the same backup timestamp so it can be easily undone if the
        # user wishes to switch it back
        #self.bak_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.errorToLog = False

    # Method to update all of the required Horizon2 files
    def updateSkin(self):
        # Update the files one at a time
        self._updateDialogVideoInfo()
        self._updateIncludeItems()
        self._updateIncludeInfo()
        

        # Now either print the complete message or the "check log" message
        if self.errorToLog:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32019))#, ADDON.getLocalizedString(32020))
        else:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32033))#, ADDON.getLocalizedString(32022))

    # Save the new contents, taking a backup of the old file
    def _saveNewFile(self, sourceXml, destXml, dialogXmlStr):
        log("SaveNewFile: New file content: %s" % dialogXmlStr)

        # Now save the file to disk, start by backing up the old file
        xbmcvfs.copy(sourceXml, destXml)

        # Now save the new file
        dialogXmlFile = xbmcvfs.File(sourceXml, 'w')
        dialogXmlFile.write(dialogXmlStr)
        dialogXmlFile.close()

    ##########################################################################
    # UPDATES FOR DialogVideoInfo.xml
    ##########################################################################
    # Makes all the required changes to DialogVideoInfo.xml
    def _updateDialogVideoInfo(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.horizon2path, 'DialogVideoInfo.xml')
        destXml = os_path_join(self.backupPath, 'DialogVideoInfo.xml')
        log("DialogVideoInfo: Horizon2 dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("DialogVideoInfo: Unable to find the file DialogVideoInfo.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the DialogVideoInfo.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the ParentalGuide bits added
        if 'script.parentalguide' in dialogXmlStr:
            # Already have ParentalGuide referenced, so we do not want to do anything else
            # to this file
            log("DialogVideoInfo: ParentalGuide already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Now we need to add the button after the Final button
        previousButton = '<menucontrol>4000</menucontrol>'

        if previousButton not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("DialogVideoInfo: Could not find final button, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # # Check to make sure we use a unique ID value for the button
        # idOK = False
        # idval = 202
        # while not idOK:
            # idStr = '<param name="id" value="%d"' % idval
            # if idStr not in dialogXmlStr:
                # idOK = True
            # else:
                # idval = idval + 1

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t<onload>RunScript(special://home/addons/script.parentalguide/ClearProperties.py,)</onload>
\t<onload>RunScript(special://home/addons/script.parentalguide/NudityCheck.py,)</onload>
\t<onunload>RunScript(special://home/addons/script.parentalguide/ClearProperties.py,)</onunload>
'''
# \t<onunload>ClearProperty(IMDB-NVotes,Home)</onunload>
# \t<onunload>ClearProperty(IMDB-NIcon,Home)</onunload>
# \t<onunload>ClearProperty(IMDB-NRate,Home)</onunload>
# \t<onunload>ClearProperty(CSM-Age,Home)</onunload>
# \t<onunload>ClearProperty(CSM-Icon,Home)</onunload>
# \t<onunload>ClearProperty(KidsInMind-NRate,Home)</onunload>
# \t<onunload>ClearProperty(KidsInMind-NIcon,Home)</onunload>
# \t<onunload>ClearProperty(MovieGuide-NIcon,Home)</onunload>
# \t<onunload>ClearProperty(MovieGuide-NRate,Home)</onunload>
# \t<onunload>ClearProperty(RaisingChildren-Icon,Home)</onunload>
# \t<onunload>ClearProperty(RaisingChildren-Age,Home)</onunload>
# \t<onunload>ClearProperty(DoveFoundation-NIcon,Home)</onunload>
# \t<onunload>ClearProperty(DoveFoundation-NRate,Home)</onunload>
# \t<onunload>ClearProperty(PGFurnitureTitle,Home)</onunload>
# \t<onunload>ClearProperty(PGFurnitureIcon,Home)</onunload>
# \t<onunload>ClearProperty(KidsInMind-Icon,Home)</onunload>
# \t<onunload>ClearProperty(MovieGuide-Icon,Home)</onunload>
# \t<onunload>ClearProperty(IMDB-Icon,Home)</onunload>
# \t<onunload>ClearProperty(DoveFoundation-Icon,Home)</onunload>
# '''

        insertTxt = previousButton + (DIALOG_VIDEO_INFO_BUTTON)
        dialogXmlStr = dialogXmlStr.replace(previousButton, insertTxt)

        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


    def _updateIncludeItems(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.horizon2path, 'Includes_Items.xml')
        destXml = os_path_join(self.backupPath, 'Includes_Items.xml')
        log("Includes_Items: Horizon2 dialog XML file: %s" % dialogXml)
        

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("Includes_Items.xml: Unable to find the file Include_Items.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the Includes_Items.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the ParentalGuide bits added
        if 'script.parentalguide' in dialogXmlStr:
            # Already have ParentalGuide referenced, so we do not want to do anything else
            # to this file
            log("Includes_Items: ParentalGuide already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Now we need to add the button after the Final button
        previousbutton = '''<param name="label">Trakt</param>'''

        if previousbutton not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Items: Could not find previous button, skipping file", xbmc.LOGERROR)
            #log(previousbutton, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # # Check to make sure we use a unique ID value for the button
        # idOK = False
        # idval = 202
        # while not idOK:
            # idStr = '<param name="id" value="%d"' % idval
            # if idStr not in dialogXmlStr:
                # idOK = True
            # else:
                # idval = idval + 1

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t\t\t</include>
\t\t</include>
\t\t<include content="OSD_Button">
\t\t\t<param name="vertical">true</param>
\t\t\t<param name="id" value="5007"/>
\t\t\t<param name="groupid" value="5107"/>
\t\t\t<param name="sliceid" value="5207"/>
\t\t\t<param name="label" value="ParentalGuide"/>
\t\t\t<param name="icon" value="special://home/addons/script.parentalguide/icon-m.png"/>
\t\t\t<visible>true</visible>
\t\t\t<onclick condition="String.IsEmpty(ListItem.TvShowTitle) + !String.IsEmpty(ListItem.Title)+ !String.IsEmpty(ListItem.IMDBNumber)">RunScript(special://home/addons/script.parentalguide/default.py,)</onclick>
\t\t\t<include content="OSD_Button_HintLabel">
\t\t\t\t<param name="label">ParentalGuide</param>'''

        insertTxt = previousbutton + (DIALOG_VIDEO_INFO_BUTTON) 
        dialogXmlStr = dialogXmlStr.replace(previousbutton, insertTxt)

        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


    def _updateIncludeInfo(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.horizon2path, 'Includes_Info.xml')
        destXml = os_path_join(self.backupPath, 'Includes_Info.xml')
        log("Include_Info: Horizon2 dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("Includes_Info: Unable to find the file Include_Info.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the Includes_Info.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        # Now check to see if the skin file has already had the ParentalGuide bits added
        if '$PARAM[parentalrating]' in dialogXmlStr:
            # Already have ParentalGuide referenced, so we do not want to do anything else
            # to this file
            log("Includes_Info: ParentalGuide already referenced in %s, skipping file" % dialogXml, xbmc.LOGINFO)
            self.errorToLog = True
            return

        # Now we need to add the button after the Final button
        previousButton3 = '''<definition>
            <control type="grouplist">
                <hitrect x="0" y="0" w="0" h="0" />
                <nested />'''
        
        if previousButton3 not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Info: Could not find final button, skipping file", xbmc.LOGERROR)
            log(previousButton3, xbmc.LOGERROR)
            #log(dialogXmlStr, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t\t\t\t<top>5</top>'''

        insertTxt = previousButton3 + (DIALOG_VIDEO_INFO_BUTTON)
        dialogXmlStr = dialogXmlStr.replace(previousButton3, insertTxt)
        
        # Now we need to add the button after the Final button
        previousButton1 = '''<visible>$PARAM[releasestatus]</visible>'''

        if previousButton1 not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Info: Could not find final button, skipping file", xbmc.LOGERROR)
            log(previousButton1, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t\t\t\t</include>
\t\t\t</control>
\n\t\t\t<control type="grouplist">
\t\t\t\t<hitrect x="0" y="0" w="0" h="0"/>
\t\t\t\t<nested/>
\t\t\t\t<top>50</top>
\t\t\t\t<height>32</height>
\t\t\t\t<orientation>horizontal</orientation>
\t\t\t\t<align>$PARAM[align]</align>
\t\t\t\t<aligny>center</aligny>
\t\t\t\t<itemgap>10</itemgap>
\t\t\t\t<usecontrolcoords>true</usecontrolcoords>
\t\t\t\t<!-- Provider Icon -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(IMDB-Icon)]</param>
\t\t\t\t\t<param name="icon_top">0</param>
\t\t\t\t\t<param name="icon_width">32</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Data -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(IMDB-NIcon)]</param>
\t\t\t\t\t<param name="icon_top">2</param>
\t\t\t\t\t<param name="icon_height">28</param>
\t\t\t\t\t<param name="icon_width">14</param>
\t\t\t\t\t<param name="label">$INFO[Window(home).Property(IMDB-NVotes)]   </param>
\t\t\t\t\t<param name="label_fallback">           </param>
\t\t\t\t\t<param name="is_varlabel">true</param>
\t\t\t\t\t<param name="is_updating">false</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Icon -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(KidsInMind-Icon)]</param>
\t\t\t\t\t<param name="icon_top">0</param>
\t\t\t\t\t<param name="icon_width">32</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Data -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(KidsInMind-NIcon)]</param>
\t\t\t\t\t<param name="icon_top">2</param>
\t\t\t\t\t<param name="icon_height">28</param>
\t\t\t\t\t<param name="icon_width">14</param>
\t\t\t\t\t<param name="label">$INFO[Window(home).Property(KidsInMind-NRate)]   </param>
\t\t\t\t\t<param name="label_fallback">           </param>
\t\t\t\t\t<param name="is_varlabel">True</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Icon -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(MovieGuide-Icon)]</param>
\t\t\t\t\t<param name="icon_top">0</param>
\t\t\t\t\t<param name="icon_width">32</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Data -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(MovieGuide-NIcon)]</param>
\t\t\t\t\t<param name="icon_top">2</param>
\t\t\t\t\t<param name="icon_height">28</param>
\t\t\t\t\t<param name="icon_width">14</param>
\t\t\t\t\t<param name="label">$INFO[Window(home).Property(MovieGuide-NRate)]   </param>
\t\t\t\t\t<param name="label_fallback">           </param>
\t\t\t\t\t<param name="is_varlabel">True</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Icon -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(DoveFoundation-Icon)]</param>
\t\t\t\t\t<param name="icon_top">0</param>
\t\t\t\t\t<param name="icon_width">32</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>
\t\t\t\t</include>
\t\t\t\t<!-- Provider Data -->
\t\t\t\t<include content="Info_Ratings_Item">
\t\t\t\t\t<param name="include_condition">!Skin.HasSetting(Ratings.DisableIMDb)</param>
\t\t\t\t\t<param name="colordiffuse">$PARAM[colordiffuse]</param>
\t\t\t\t\t<param name="icon">$INFO[Window(home).Property(DoveFoundation-NIcon)]</param>
\t\t\t\t\t<param name="icon_top">2</param>
\t\t\t\t\t<param name="icon_height">28</param>
\t\t\t\t\t<param name="icon_width">14</param>
\t\t\t\t\t<param name="label">$INFO[Window(home).Property(DoveFoundation-NRate)]   </param>
\t\t\t\t\t<param name="label_fallback">           </param>
\t\t\t\t\t<param name="is_varlabel">True</param>
\t\t\t\t\t<param name="is_updating">False</param>
\t\t\t\t\t<param name="is_autohide">Skin.HasSetting(Ratings.AutoHide)</param>
\t\t\t\t\t<visible>true</visible>'''


        insertTxt = previousButton1 + (DIALOG_VIDEO_INFO_BUTTON)
        dialogXmlStr = dialogXmlStr.replace(previousButton1, insertTxt)

        # Now we need to add the button after the Final button
        previousButton2 = '''<include content="Info_Ratings" condition="!Skin.HasSetting(Ratings.HideAll)">'''
        
        if previousButton2 not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Info: Could not find final button, skipping file", xbmc.LOGERROR)
            log(previousButton2, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''\n\t\t\t\t\t\t\t<param name="parentalrating">$INFO[Window(home).Property(Nvotes)]</param>
\t\t\t\t\t\t\t<param name="parentalratingicon">$INFO[Window(home).Property(Nicon)]</param>'''

        insertTxt = previousButton2 + (DIALOG_VIDEO_INFO_BUTTON)
        dialogXmlStr = dialogXmlStr.replace(previousButton2, insertTxt)

        # Now we need to add the button after the Final button
        previousButton4 = '''<include content="Info_Line_Label" condition="!$PARAM[player]">
                        <param name="controltype" value="$PARAM[controltype]" />
                        <param name="label" value="$INFO[$PARAM[container]ListItem.Size]" />
                        <param name="visible" value="!String.IsEmpty($PARAM[container]ListItem.PictureResolution) + !String.IsEmpty($PARAM[container]ListItem.Size)" />
                        <param name="textcolor" value="$PARAM[colordiffuse]_90" />
                    </include>'''
        
        if previousButton4 not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Info: Could not find final button, skipping file", xbmc.LOGERROR)
            log(previousButton4, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''
\n\t\t\t\t\t<!--Recommened Age-->
\t\t\t\t\t<include content="Info_Line_Label" condition="!$PARAM[player]">
\t\t\t\t\t\t<param name="controltype" value="$PARAM[controltype]"/>
\t\t\t\t\t\t<param name="label" value="$INFO[Window(home).Property(CSM-Age)]"/>
\t\t\t\t\t\t<param name="visible" value="true"/>
\t\t\t\t\t\t<param name="textcolor" value="$PARAM[colordiffuse]_90"/>
\t\t\t\t\t</include>
\t\t\t\t\t<include content="Info_Line_Label" condition="!$PARAM[player]">
\t\t\t\t\t\t<param name="controltype" value="$PARAM[controltype]"/>
\t\t\t\t\t\t<param name="label" value="$INFO[Window(home).Property(RaisingChildren-Age)]"/>
\t\t\t\t\t\t<param name="visible" value="true"/>
\t\t\t\t\t\t<param name="textcolor" value="$PARAM[colordiffuse]_90"/>
\t\t\t\t\t</include>'''

        insertTxt = previousButton4 + (DIALOG_VIDEO_INFO_BUTTON)
        dialogXmlStr = dialogXmlStr.replace(previousButton4, insertTxt)

        previousButton5 = '''<param name="ratingsheight" default="80" />'''
        
        if previousButton5 not in dialogXmlStr:
            # The file has had a standard component deleted, so quit
            log("Includes_Info: Could not find final button, skipping file", xbmc.LOGERROR)
            log(previousButton5, xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Now add the ParentalGuide button after the Final one
        DIALOG_VIDEO_INFO_BUTTON = '''<param name="ratingsheight" default="90" />'''

        insertTxt = DIALOG_VIDEO_INFO_BUTTON
        dialogXmlStr = dialogXmlStr.replace(previousButton5, insertTxt)
        
        
        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


#########################
# Main
#########################
if __name__ == '__main__':
    log("ParentalGuide: Updating Horizon2 Skin (version %s)" % ADDON.getAddonInfo('version'))

    doUpdate = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32034))

    if doUpdate:
        try:
            Horizon2Up = Horizon2Update()
            Horizon2Up.updateSkin()
            del Horizon2Up
        except:
            log("ParentalGuide: %s" % traceback.format_exc(), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32035))#, ADDON.getLocalizedString(32020))
