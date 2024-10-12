#!/usr/bin/python

import os
import errno
import sqlite3
import sys
from time import time
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui
from shutil import rmtree
#from SQLiteCache import SqliteCache
import shutil
from pathlib import Path
from typing import Union

import logging
from utils import logger

logger = logging.getLogger(__name__)
ADDON = xbmcaddon.Addon(id='script.parentalguide')

def clear_directory(directory_path: Union[str, Path]) -> list:
    """Irreversibly removes all files and folders inside the specified
    directory. Returns a list with paths Python lacks permission to delete."""
    erroneous_paths = []
    for path_object in Path(directory_path).iterdir():
        try:
            if path_object.is_dir():
                shutil.rmtree(path_object)
                logger.info("Cache db file deletion succeeded " + directory_path)
                xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Parental Guide Cache', 'Cache was cleared' , ADDON.getAddonInfo('icon')))
            else:
                path_object.unlink()
                logger.info("Cache db file deletion failed " + directory_path)
                xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Parental Guide Cache', 'Clearing Cache failed' , ADDON.getAddonInfo('icon')))
        except PermissionError:
            erroneous_paths.append(path_object)
    return erroneous_paths
    
# def __init__(self):
if __name__ == '__main__':
    logger.info('Cache db clearing script started')
    ADDON = xbmcaddon.Addon(id='script.parentalguide')
    temp_dir = ADDON.getAddonInfo('path')
    cache_dir = os.path.join(temp_dir, 'cache', ADDON.getAddonInfo('id'))
    clear_directory (cache_dir)
    # if xbmcvfs.exists(cache_dir):
        # xbmcvfs.rmdir(cache_dir)
        
    # if os.path.exists(cache_dir):
        # logger.info("shutil.rmtree Removing path")
        # shutil.rmtree(cache_dir, ignore_errors=True)

        
