#!/usr/bin/python

import os
import errno
import sqlite3
import sys
from time import time
import _pickle as cPickle
from _pickle import loads, dumps, PickleBuffer
import xbmc
import xbmcvfs
import xbmcaddon
import xbmcgui

import logging
from resources.lib.utils import logger as logx

logger = logging.getLogger(__name__)
ADDON = xbmcaddon.Addon(id='script.parentalguide')


class SqliteCache:
    """
        SqliteCache

        Ripped heavily from: http://flask.pocoo.org/snippets/87/
        This implementation is a simple Sqlite based cache that
        supports cache timers too. Not specifying a timeout will
        mean that the TITLEue will exist forever.
    """

    # prepared queries for cache operations
    _create_sql = (
        'CREATE TABLE IF NOT EXISTS entries '
        '( KEY TEXT PRIMARY KEY, val BLOB, exp BLOB )'
    )
    _create_sql_reviews = (
        'CREATE TABLE IF NOT EXISTS reviews '
        '( ID TEXT PRIMARY KEY, NAME BLOB, SCORE BLOB, description BLOB, CAT BLOB, VOTES BLOB, PROVIDERKEY BLOB )'
    )
    _create_index = 'CREATE INDEX IF NOT EXISTS keyname_index ON entries (key)'
    _create_index_reviews = 'CREATE INDEX IF NOT EXISTS keyname_index ON reviews (key)'
    
    _get_sql = 'SELECT val, exp FROM entries WHERE key = ?'
    _get_sql_exp = 'SELECT exp FROM entries WHERE key = ?'
    _del_sql = 'DELETE FROM entries WHERE key = ?'
    _set_sql = 'REPLACE INTO entries (key, val, exp) VALUES (?, ?, ?)'
    _add_sql = 'INSERT INTO entries (key, val, exp) VALUES (?, ?, ?)'
    _clear_sql = 'DELETE * FROM entries'

    # other properties
    connection = None

    def __init__(self):
        ADDON = xbmcaddon.Addon(id='script.parentalguide')
        temp_dir = xbmcvfs.translatePath('special://temp')
        temp_dir = ADDON.getAddonInfo('path')
        logger.info('temp dir is ' + temp_dir)
        cache_dir = os.path.join(temp_dir, 'cache', ADDON.getAddonInfo('id'))
        if not xbmcvfs.exists(cache_dir):
            xbmcvfs.mkdir(cache_dir)
        logger.info('the cache dir is ' + cache_dir)
        
        self.path = cache_dir
    
    def _get_conn(self):
        """ Returns a Sqlite connection """
        if self.connection:
            return self.connection

        # specify where we want the cache db to live
        cache_db_path = os.path.join(self.path, 'cache.sqlite')

        # setup the connection
        conn = sqlite3.Connection(cache_db_path, timeout=60, check_same_thread=False)
        logger.debug('Connected to {path}'.format(path=cache_db_path))

        # ensure that the table schema is available. The
        # 'IF NOT EXISTS' in the create_sql should be
        # pretty self explanitory
        with conn:
            conn.execute(self._create_sql)
            conn.execute(self._create_index)
            logger.debug('Ran the create table && index SQL.')

        # set the connection property
        self.connection = conn

        # return the connection
        return self.connection

    # def get(self, key):

        # """ Retreive a value from the Cache """

        # return_value = None
        # key = key.lower()
        # # get a connection to run the lookup query with
        # with self._get_conn() as conn:
            
            # # loop the response rows looking for a result
            # # that is not expired
            # # for row in conn.execute(self._get_sql, (key,)):
                # #return_value = loads(row[0])
                
                # expire = loads(row[1])
                
                # #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('expiry of {k}'.format(k=key), expire , ADDON.getAddonInfo('icon')))
                
                # if expire == 0 or expire > time():
                    # return_value = loads(row[0])
                    # # TODO: Delete the value that is expired?
                # # else:
                    # # self.delete(key)
                # break

        # return return_value

    def get(self, key):

        """ Retreive a value from the Cache """

        return_value = None
        key = key.lower()
        
        # get a connection to run the lookup query with
        with self._get_conn() as conn:
            
            # loop the response rows looking for a result
            # that is not expired
            for row in conn.execute(self._get_sql, (key,)):
                #return_value = loads(row[0])
                
                expire = loads(row[1])
                
                #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('expiry of {k} {kk}'.format(k=key, kk=provider), expire , ADDON.getAddonInfo('icon')))
                
                if expire == 0 or expire > time():
                    return_value = loads(row[0])
                    #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ('Cach for %s' % key, return_value , ADDON.getAddonInfo('icon')))
                    # TODO: Delete the value that is expired?
                else:
                    self.delete(key)
                    return_value = None
                break

        return return_value
        
    def get_exp(self, key):
        return_value = None
        key = key.lower()

        with self._get_conn() as conn:
            #for row in conn.execute(self._get_sql_exp, (key,)):
                try:
                    expire = loads(conn.execute(self._get_sql_exp, (key,)))
                except:
                    expire = "No Result"
            
        return expire
        
    def delete(self, key):

        """ Delete a cache entry """

        with self._get_conn() as conn:
            conn.execute(self._del_sql, (key,))

    def update(self, show_info, timeout=None):

        """ Sets a k,v pair with a optional timeout """

        # if no timeout is specified, then we will
        # leave it as a non-expiring value. Other-
        # wise, we add the timeout in seconds to
        # the current time
        Default_caching_period = 30*24*60*60 ## 30days
        expire = time() + Default_caching_period if not timeout else time() + timeout

        # serialize the value with protocol 2
        # ref: https://docs.python.org/2/library/pickle.html#data-stream-format

        val = PickleBuffer(dumps(show_info))
        expire = PickleBuffer(dumps(expire))
       
        if show_info["id"]:
            key = show_info["id"].lower()+"_"+show_info["provider"].lower()
        else:
            key = show_info["title"].replace(":","").replace("-","_").replace(" ","_").lower()+"_"+show_info["provider"].lower()

        # write the updated value to the db
        with self._get_conn() as conn:
            try:
                conn.execute(self._set_sql, (key, val, expire))
                logx.info("Sucessfully Updated results to cache for [%s] [%s]" % (show_info["title"], show_info["provider"]))

            except:
                logx.info("Failed to update results to cache for [%s] [%s]" % (show_info["title"], show_info["provider"]))
    
    def set(self, show_info, timeout=None):

        """ Adds a k,v pair with a optional timeout """

        # if no timeout is specified, then we will
        # leave it as a non-expiring value. Other-
        # wise, we add the timeout in seconds to
        # the current time
        logx.info("Trying to save results to cache for [%s] [%s]" % (show_info["title"], show_info["provider"]))
        
        Default_caching_period = 30*24*60*60 ## 30days
        expire = time() + Default_caching_period if not timeout else time() + timeout

        # serialize the value with protocol 2
        # ref: https://docs.python.org/2/library/pickle.html#data-stream-format

        val = PickleBuffer(dumps(show_info))
        expire2 = PickleBuffer(dumps(expire))
        
        if show_info["id"]:
            key = show_info["id"].lower()+"_"+show_info["provider"].lower()
        else:
            key = show_info["title"].replace(":","").replace("-","_").replace(" ","_").lower()+"_"+show_info["provider"].lower()
            
        
        #data = PickleBuffer(dumps(value))

        # adding a new entry that may cause a duplicate key
        # error if they key already exists. In this case
        # we will fall back to the update method.
        with self._get_conn() as conn:

            try:

                conn.execute(self._add_sql, (key, val, expire2))

            except sqlite3.IntegrityError:

                # call the update method as fallback
                logx.info(
                    'Attempting to set an existing key {k}. Falling back to update method.'.format(
                        k=key))
                self.update(show_info, expire)
                pass

    def clear(self):

        """ Clear a cache """

        with self._get_conn() as conn:
            conn.execute(self._clear_sql, )
            logx.info('Cache cleared sucessfully')
        
    def __del__(self):

        """ Cleans up the object by destroying the sqlite connection """

        if self.connection:
            self.connection.close()


# allow this module to be used to clear the cache
if __name__ == '__main__':
    logger.info('ParentalGuide Cache Initiated')
    # check args
    if len(sys.argv) != 3 or sys.argv[1] != 'clear':
        print('[!] Error: You have to specify the clear with `python %s clear <path to cache.sqlite>`' % sys.argv[0])
        sys.exit(1)

    if not os.path.isdir(sys.argv[2]):
        print('[!] Error: %s does not seem to be a path!' % sys.argv[2])
        sys.exit(1)

    # setup the cache instance and clear it.
    c = SqliteCache(sys.argv[2])
    c.clear()
    print(' * Cache cleared')
