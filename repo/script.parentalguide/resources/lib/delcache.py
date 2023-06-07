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
from resources.lib.SQLiteCache import SqliteCache

import logging
from resources.lib.utils import logger

logger = logging.getLogger(__name__)
ADDON = xbmcaddon.Addon(id='script.parentalguide')

# def __init__(self):
if __name__ == '__main__':
    ADDON = xbmcaddon.Addon(id='script.parentalguide')
    temp_dir = ADDON.getAddonInfo('path')
    cache_dir = os.path.join(temp_dir, 'cache', ADDON.getAddonInfo('id'))
    # if xbmcvfs.exists(cache_dir):
        # xbmcvfs.rmdir(cache_dir)
        
    # if os.path.exists(cache_dir):
        # log("shutil.rmtree Removing path")
        # shutil.rmtree(cache_dir, ignore_errors=True)
    
    db = SqliteCache()
    de.clear
    logger.info('the cache dir is ' + cache_dir + " was deleted")
        
