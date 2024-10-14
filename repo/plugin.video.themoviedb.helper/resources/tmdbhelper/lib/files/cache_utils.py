import sqlite3
import json
from datetime import datetime, timedelta
import logging
import xbmcvfs

DB_PATH = 'special://profile/addon_data/plugin.video.themoviedb.helper/parental_guide_cache.db'

def get_db_connection():
    conn = sqlite3.connect(xbmcvfs.translatePath(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''CREATE TABLE IF NOT EXISTS parental_guide_cache
                    (id TEXT PRIMARY KEY, data TEXT, expiry DATE)''')
    conn.commit()
    conn.close()

def get_cached_data(imdb_id, video_name, year):
    conn = get_db_connection()
    cur = conn.cursor()
    cache_id = f"{imdb_id}_{video_name}_{year}"
    cur.execute("SELECT * FROM parental_guide_cache WHERE id = ? AND expiry > date('now')", (cache_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return json.loads(row['data'])
    return None

def set_cached_data(imdb_id, video_name, year, data):
    conn = get_db_connection()
    cur = conn.cursor()
    cache_id = f"{imdb_id}_{video_name}_{year}"
    current_year = datetime.now().year
    if int(year) == current_year:
        expiry = datetime.now() + timedelta(days=7)
    else:
        expiry = datetime.now() + timedelta(days=365)
    cur.execute("INSERT OR REPLACE INTO parental_guide_cache (id, data, expiry) VALUES (?, ?, ?)",
                (cache_id, json.dumps(data), expiry.date()))
    conn.commit()
    conn.close()

# Initialize the database
init_db()
