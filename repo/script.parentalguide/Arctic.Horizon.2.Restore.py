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
class Horizon2restore():
    def __init__(self):
        # Find out where the Horizon2 skin files are located
        skinAddon = xbmcaddon.Addon(id='skin.arctic.horizon.2')
        self.horizon2path = xbmcvfs.translatePath(skinAddon.getAddonInfo('path'))
        self.horizon2path = os_path_join(self.horizon2path, '1080i')
        self.backupPath = xbmcvfs.translatePath(ADDON.getAddonInfo('path'))
        self.backupPath = os_path_join(self.backupPath, 'Arctic.Horizon.2')
        log("Horizon2 Location: %s" % self.horizon2path)
        log("Backup Location: %s" % self.backupPath)
        # Create the timestamp centrally, as we want all files changed for a single
        # run to have the same backup timestamp so it can be easily undone if the
        # user wishes to switch it back
        #self.bak_timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        self.errorToLog = False

    # Method to restore all of the required Horizon2 files
    def restoreSkin(self):
        # restore the files one at a time
        self._restoreDialogVideoInfo()
        self._restoreIncludeItems()
        self._restoreIncludeInfo()
        

        # Now either print the complete message or the "check log" message
        if self.errorToLog:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32019))#, ADDON.getLocalizedString(32020))
        else:
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32021))#, ADDON.getLocalizedString(32022))

    # Save the new contents, taking a backup of the old file
    def _saveNewFile(self, sourceXml, destXml, dialogXmlStr):
        log("SaveNewFile: New file content: %s" % dialogXmlStr)

        # Now save the file to disk, start by backing up the old file
        xbmcvfs.copy(sourceXml, destXml)

        # Now save the new file
        dialogXmlFile = xbmcvfs.File(destXml, 'w')
        dialogXmlFile.write(dialogXmlStr)
        dialogXmlFile.close()

    ##########################################################################
    # restoreS FOR DialogVideoInfo.xml
    ##########################################################################
    # Makes all the required changes to DialogVideoInfo.xml
    def _restoreDialogVideoInfo(self):
        # Get the location of the information dialog XML file
        dialogXml = os_path_join(self.backupPath, 'DialogVideoInfo.xml')
        destXml = os_path_join(self.horizon2path, 'DialogVideoInfo.xml')
        log("DialogVideoInfo: Horizon2 dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("DialogVideoInfo: Unable to find the backup file DialogVideoInfo.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the DialogVideoInfo.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


    def _restoreIncludeItems(self):
        # Get the location of the information dialog XML file
        destXml = os_path_join(self.horizon2path, 'Includes_Items.xml')
        dialogXml = os_path_join(self.backupPath, 'Includes_Items.xml')
        log("Includes_Items: Horizon2 dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("Includes_Items.xml: Unable to find the backup file Include_Items.xml, skipping file" + dialogXml, xbmc.LOGERROR)
            log("Backup Location: %s" % dialogXml)
            self.errorToLog = True
            return

        # Load the Includes_Items.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()

        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


    def _restoreIncludeInfo(self):
        # Get the location of the information dialog XML file
        destXml = os_path_join(self.horizon2path, 'Includes_Info.xml')
        dialogXml = os_path_join(self.backupPath, 'Includes_Info.xml')
        log("Include_Info: Horizon2 dialog XML file: %s" % dialogXml)

        # Make sure the file exists (It should always exist)
        if not xbmcvfs.exists(dialogXml):
            log("Includes_Info: Unable to find the backup file Include_Info.xml, skipping file", xbmc.LOGERROR)
            self.errorToLog = True
            return

        # Load the Includes_Info.xml into a string
        dialogXmlFile = xbmcvfs.File(dialogXml, 'r')
        dialogXmlStr = dialogXmlFile.read()
        dialogXmlFile.close()
        
        self._saveNewFile(dialogXml, destXml, dialogXmlStr)


#########################
# Main
#########################
if __name__ == '__main__':
    log("ParentalGuide: restoring Horizon2 Skin (version %s)" % ADDON.getAddonInfo('version'))

    dorestore = xbmcgui.Dialog().yesno(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32017))

    if dorestore:
        try:
            Horizon2Up = Horizon2restore()
            Horizon2Up.restoreSkin()
            del Horizon2Up
        except:
            log("ParentalGuide: %s" % traceback.format_exc(), xbmc.LOGERROR)
            xbmcgui.Dialog().ok(ADDON.getLocalizedString(32001), ADDON.getLocalizedString(32018))#, ADDON.getLocalizedString(32020))
