import os.path
import sqlite3
import six
from six.moves import urllib_parse
import shutil
from kodi_six import xbmc, xbmcaddon, xbmcplugin, xbmcgui, xbmcvfs
import os
import sys

__scriptname__ = "3rbi"
__author__ = "3rbi"
__scriptid__ = "plugin.video.aksv"

addon_handle = int(sys.argv[1])
addon_sys = sys.argv[0]
addon = xbmcaddon.Addon()
TRANSLATEPATH = xbmcvfs.translatePath if six.PY3 else xbmc.translatePath

rootDir = addon.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = TRANSLATEPATH(rootDir)
resDir = os.path.join(rootDir, 'resources')
imgDir = os.path.join(resDir, 'images')
aboutDir = os.path.join(resDir, 'about')
profileDir = addon.getAddonInfo('profile')
profileDir = TRANSLATEPATH(profileDir)
cookiePath = os.path.join(profileDir, 'cookies.lwp')
if addon.getSetting('custom_favorites') == 'true':
    fav_path = addon.getSetting('favorites_path')
    if fav_path == '':
        fav_path = profileDir
    favoritesdb = os.path.join(fav_path, 'favorites.db')
else:
    favoritesdb = os.path.join(profileDir, 'favorites.db')
customSitesDir = os.path.join(profileDir, 'custom_sites')
tempDir = os.path.join(profileDir, 'temp')

aksvicon = TRANSLATEPATH(os.path.join(rootDir, 'icon.png'))
changelog = TRANSLATEPATH(os.path.join(rootDir, 'changelog.txt'))


if not os.path.exists(profileDir):
    os.makedirs(profileDir)

if not os.path.exists(customSitesDir):
    os.makedirs(customSitesDir)

if not os.path.exists(tempDir):
    os.makedirs(tempDir)

try:
    _kodi_build = xbmc.getInfoLabel('system.buildversion')
    KODIVER = float(_kodi_build.split(' ')[0][:4]) if _kodi_build else float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])
except:
    KODIVER = float(xbmcaddon.Addon('xbmc.addon').getAddonInfo('version')[:4])


def addon_image(filename, custom=False):
    if filename.startswith('http'):
        return filename
    else:
        img = os.path.join(customSitesDir if custom else imgDir, filename)
        return img


def eod(handle=addon_handle, cache=True, content=None):
    if content:
        xbmcplugin.setContent(handle, content)
    if addon.getSetting('customview') == 'true':
        skin = xbmc.getSkinDir().lower()
        viewtype = 55 if 'estuary' in skin else 50
        setview = addon.getSetting('setview')
        if ';' in setview:
            currentskin, viewno = setview.split(';')
            if currentskin == skin:
                viewtype = viewno
        xbmc.executebuiltin("Container.SetViewMode(%s)" % str(viewtype))
    xbmcplugin.endOfDirectory(handle, cacheToDisc=cache)


def addImgLink(name, url, mode):
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&name=" + urllib_parse.quote_plus(name))
    liz = xbmcgui.ListItem(name)
    if KODIVER < 19.8:
        liz.setInfo(type='pictures', infoLabels={'title': name})
    liz.setArt({'thumb': url, 'icon': url, 'poster': url})
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def addDownLink(name, url, mode, iconimage, desc='', stream=None, fav='add', noDownload=False, contextm=None, fanart=None, duration='', quality='',
                year=None, season=None, episode=None, show_title=None, media_type=None, original_title=None, episode_name=None, **kwargs):
    contextMenuItems = []
    favtext = "Remove from" if fav == 'del' else "Add to"  # fav == 'add' or 'del'
    dname = desc == name
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&name=" + urllib_parse.quote_plus(name))
    dwnld = (sys.argv[0]
             + "?url=" + urllib_parse.quote_plus(url)
             + "&mode=" + str(mode)
             + "&download=" + str(1)
             + "&name=" + urllib_parse.quote_plus(name))
    favorite = (sys.argv[0]
                + "?url=" + urllib_parse.quote_plus(url)
                + "&fav=" + fav
                + "&favmode=" + str(mode)
                + "&mode=" + str('favorites.Favorites')
                + "&img=" + urllib_parse.quote_plus(iconimage)
                + "&name=" + urllib_parse.quote_plus(name)
                + "&duration=" + duration
                + "&quality=" + quality)
    ok = True
    if not iconimage:
        iconimage = aksvicon
    if duration:
        if addon.getSetting('duration_in_name') == 'true':
            duration = " [" + duration + "]"
            name = name + duration if six.PY3 else (name.decode('utf-8') + duration).encode('utf-8')
        else:
            secs = 0
            try:
                duration = duration.upper().replace('H', ':').replace('M', ':').replace('S', '').replace('EC', '').replace(' ', '').replace('IN', '0').replace('::', ':').strip()
                if ':' in duration:
                    if duration.endswith(':'):
                        duration += '0'
                    if duration.startswith(':'):
                        duration = '0' + duration
                    secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(':'))))
                elif duration.isdigit():
                    secs = int(duration)
                if secs is None and len(duration) > 0:
                    xbmc.log("@@@@3rbi: Duration format error: " + str(duration), xbmc.LOGERROR)
            except:
                xbmc.log("@@@@3rbi: Duration format error: " + str(duration), xbmc.LOGERROR)
    width = None
    if quality:
        if addon.getSetting('quality_in_name') == 'true':
            quality = " [" + quality + "]"
            name = name + quality if six.PY3 else (name.decode('utf-8') + quality).encode('utf-8')
        else:
            width, height = get_resolution(quality)
    if dname:
        desc = name
    liz = xbmcgui.ListItem(name, offscreen=True) if KODIVER >= 20.0 else xbmcgui.ListItem(name)
    
    # Explicitly set label and label2
    liz.setLabel(name)
    if original_title:
        liz.setLabel2(original_title)
    elif desc:
        liz.setLabel2(desc[:50] if len(desc) > 50 else desc)
    
    if KODIVER >= 20.0:
        vtag = liz.getVideoInfoTag()
        if media_type:
            vtag.setMediaType(media_type)
        elif episode is not None:
            vtag.setMediaType('episode')
        else:
            vtag.setMediaType('movie')
        vtag.setTitle(name)
        if episode_name:
            vtag.setTitle(episode_name)
        if original_title:
            vtag.setOriginalTitle(original_title)
        if show_title:
            vtag.setTvShowTitle(show_title)
        if year:
            try:
                vtag.setYear(int(year))
            except:
                pass
        if season is not None:
            try:
                vtag.setSeason(int(season))
            except:
                pass
        if episode is not None:
            try:
                vtag.setEpisode(int(episode))
            except:
                pass
        if duration and addon.getSetting('duration_in_name') != 'true':
            vtag.setDuration(secs)
        if desc:
            vtag.setPlot(desc)
            vtag.setPlotOutline(desc)
        if width:
            vtag.addVideoStream(xbmc.VideoStreamDetail(width=width, height=height, codec='h264'))
        else:
            vtag.addVideoStream(xbmc.VideoStreamDetail(codec='h264'))
    else:
        info_labels = {"title": name}
        if duration and addon.getSetting('duration_in_name') != 'true':
            info_labels["duration"] = secs
        if desc:
            info_labels["plot"] = desc
            info_labels["plotoutline"] = desc
        if year:
            try:
                info_labels["year"] = int(year)
            except:
                pass
        if season is not None:
            try:
                info_labels["season"] = int(season)
            except:
                pass
        if episode is not None:
            try:
                info_labels["episode"] = int(episode)
            except:
                pass
        if show_title:
            info_labels["tvshowtitle"] = show_title
        if original_title:
            info_labels["originaltitle"] = original_title
        liz.setInfo(type="Video", infoLabels=info_labels)
        if width:
            liz.addStreamInfo('video', {'codec': 'h264', 'width': width, 'height': height})
        else:
            liz.addStreamInfo('video', {'codec': 'h264'})
    
    # Set properties for skin access
    liz.setProperty('Title', name)
    if desc:
        liz.setProperty('Plot', desc)
    if year:
        liz.setProperty('year', str(year))
    if season is not None:
        liz.setProperty('season', str(season))
    if episode is not None:
        liz.setProperty('episode', str(episode))
    if episode_name:
        liz.setProperty('EpisodeName', episode_name)
    if show_title:
        liz.setProperty('TVShowTitle', show_title)
    if original_title:
        liz.setProperty('OriginalTitle', original_title)

    if not fanart:
        fanart = iconimage
    
    landscape = kwargs.get('landscape')
    if not landscape:
        landscape = iconimage

    art = {
        'thumb': iconimage,
        'icon': iconimage,
        'poster': iconimage,
        'fanart': fanart,
        'landscape': landscape,
        'banner': iconimage,
        'clearart': iconimage,
        'clearlogo': iconimage,
        'logo': iconimage
    }
    liz.setArt(art)

    if stream:
        liz.setProperty('IsPlayable', 'true')

    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    favorder = addon.getSetting("favorder") or 'date added'
    if fav == 'del' and favorder == 'date added':
        favorite_move_to_top = (sys.argv[0]
                                + "?url=" + urllib_parse.quote_plus(url)
                                + "&fav=" + 'move_to_top'
                                + "&favmode=" + str(mode)
                                + "&mode=" + str('favorites.Favorites')
                                + "&img=" + urllib_parse.quote_plus(iconimage)
                                + "&name=" + urllib_parse.quote_plus(name)
                                + "&duration=" + urllib_parse.quote_plus(duration)
                                + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('Move favorite to Top', 'RunPlugin(' + favorite_move_to_top + ')'))
        favorite_move_up = (sys.argv[0]
                            + "?url=" + urllib_parse.quote_plus(url)
                            + "&fav=" + 'move_up'
                            + "&favmode=" + str(mode)
                            + "&mode=" + str('favorites.Favorites')
                            + "&img=" + urllib_parse.quote_plus(iconimage)
                            + "&name=" + urllib_parse.quote_plus(name)
                            + "&duration=" + urllib_parse.quote_plus(duration)
                            + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('Move favorite Up', 'RunPlugin(' + favorite_move_up + ')'))
        favorite_move_down = (sys.argv[0]
                              + "?url=" + urllib_parse.quote_plus(url)
                              + "&fav=" + 'move_down'
                              + "&favmode=" + str(mode)
                              + "&mode=" + str('favorites.Favorites')
                              + "&img=" + urllib_parse.quote_plus(iconimage)
                              + "&name=" + urllib_parse.quote_plus(name)
                              + "&duration=" + urllib_parse.quote_plus(duration)
                              + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('Move favorite Down', 'RunPlugin(' + favorite_move_down + ')'))
        favorite_move_to_bottom = (sys.argv[0]
                                   + "?url=" + urllib_parse.quote_plus(url)
                                   + "&fav=" + 'move_to_bottom'
                                   + "&favmode=" + str(mode)
                                   + "&mode=" + str('favorites.Favorites')
                                   + "&img=" + urllib_parse.quote_plus(iconimage)
                                   + "&name=" + urllib_parse.quote_plus(name)
                                   + "&duration=" + urllib_parse.quote_plus(duration)
                                   + "&quality=" + urllib_parse.quote_plus(quality))
        contextMenuItems.append(('Move favorite to Bottom', 'RunPlugin(' + favorite_move_to_bottom + ')'))
    contextMenuItems.append((favtext + ' favorites', 'RunPlugin(' + favorite + ')'))
    if not noDownload:
        contextMenuItems.append(('Download Video', 'RunPlugin(' + dwnld + ')'))
    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('Addon settings', 'RunPlugin(' + settings_url + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=False)
    return ok


def get_resolution(quality):
    resolution = (None, None)
    try:
        quality = str(quality).upper()

        if quality.endswith('P'):
            quality = quality[:-1]
        if quality.isdigit():
            resolution = (int(quality) * 16 // 9, int(quality))
        resolutions = {'SD': (640, 480), 'FULLHD': (1920, 1080), 'FHD': (1920, 1080), '2K': (2560, 1440), '4K': (3840, 2160), 'UHD': (3840, 2160), 'HD': (1280, 720), '8K': (7680, 4320)}
        for x in resolutions.keys():
            if x in quality:
                quality = x
                break

        if quality in resolutions.keys():
            resolution = resolutions[quality]
        if len(quality) > 0 and resolution == (None, None):
            xbmc.log("@@@@3rbi: Quality format error: " + str(quality), xbmc.LOGERROR)
    except:
        xbmc.log("@@@@3rbi: Quality format error: " + str(quality), xbmc.LOGERROR)
    return resolution


def addDir(name, url, mode, iconimage=None, page=None, channel=None, section=None, keyword='', Folder=True, about=None,
           custom=False, list_avail=True, listitem_id=None, custom_list=False, contextm=None, desc='', fanart=None, landscape=None, fav='add',
           year=None, season=None, episode=None, show_title=None, media_type=None, original_title=None):
    u = (sys.argv[0]
         + "?url=" + urllib_parse.quote_plus(url)
         + "&mode=" + str(mode)
         + "&page=" + str(page)
         + "&channel=" + str(channel)
         + "&section=" + str(section)
         + "&keyword=" + urllib_parse.quote_plus(keyword)
         + "&name=" + urllib_parse.quote_plus(name))
    ok = True
    if not iconimage:
        iconimage = aksvicon
    liz = xbmcgui.ListItem(name, offscreen=True) if KODIVER >= 20.0 else xbmcgui.ListItem(name)
    
    # Explicitly set label and label2
    liz.setLabel(name)
    if original_title:
        liz.setLabel2(original_title)
    elif desc:
        liz.setLabel2(desc[:50] if len(desc) > 50 else desc)
    
    if not fanart:
        fanart = iconimage
    
    if not landscape:
        landscape = iconimage

    art = {
        'thumb': iconimage,
        'icon': iconimage,
        'poster': iconimage,
        'fanart': fanart,
        'landscape': landscape,
        'banner': iconimage,
        'clearart': iconimage,
        'clearlogo': iconimage,
        'logo': iconimage
    }
    liz.setArt(art)
    if KODIVER >= 20.0:
        vtag = liz.getVideoInfoTag()
        if media_type:
            vtag.setMediaType(media_type)
        elif season is not None:
            vtag.setMediaType('season')
        elif episode is not None:
            vtag.setMediaType('episode')
        else:
            vtag.setMediaType('video')
        vtag.setTitle(name)
        if original_title:
            vtag.setOriginalTitle(original_title)
        if year:
            try:
                vtag.setYear(int(year))
            except:
                pass
        if season is not None:
            try:
                vtag.setSeason(int(season))
            except:
                pass
        if episode is not None:
            try:
                vtag.setEpisode(int(episode))
            except:
                pass
        if show_title:
            vtag.setTvShowTitle(show_title)
        if desc:
            vtag.setPlot(desc)
            vtag.setPlotOutline(desc)
    else:
        info_labels = {"title": name}
        if desc:
            info_labels["plot"] = desc
            info_labels["plotoutline"] = desc
        if year:
            try:
                info_labels["year"] = int(year)
            except:
                pass
        if season is not None:
            try:
                info_labels["season"] = int(season)
            except:
                pass
        if episode is not None:
            try:
                info_labels["episode"] = int(episode)
            except:
                pass
        if show_title:
            info_labels["tvshowtitle"] = show_title
        if original_title:
            info_labels["originaltitle"] = original_title
        liz.setInfo(type="Video", infoLabels=info_labels)
    
    # Set properties for skin access
    liz.setProperty('Title', name)
    if desc:
        liz.setProperty('Plot', desc)
    if year:
        liz.setProperty('year', str(year))
    if season is not None:
        liz.setProperty('season', str(season))
    if episode is not None:
        liz.setProperty('episode', str(episode))
    if show_title:
        liz.setProperty('TVShowTitle', show_title)
    if original_title:
        liz.setProperty('OriginalTitle', original_title)
    contextMenuItems = []
    if contextm:
        if isinstance(contextm, list):
            for i in contextm:
                if isinstance(i, tuple):
                    contextMenuItems.append(i)
        else:
            if isinstance(contextm, tuple):
                contextMenuItems.append(contextm)
    if about:
        about_url = (sys.argv[0]
                     + "?mode=" + str('main.about_site')
                     + "&img=" + urllib_parse.quote_plus(iconimage)
                     + "&name=" + urllib_parse.quote_plus(name)
                     + "&about=" + str(about)
                     + "&custom=" + str(custom))
        contextMenuItems.append(
            ('About site', 'RunPlugin(' + about_url + ')'))
    if len(keyword) >= 1:
        keyw = (sys.argv[0]
                + "?mode=" + str('utils.delKeyword')
                + "&keyword=" + urllib_parse.quote_plus(keyword))
        keywedit = (sys.argv[0]
                    + "?mode=" + str('utils.newSearch')
                    + "&keyword=" + urllib_parse.quote_plus(keyword))
        keywcopy = (sys.argv[0]
                    + "?mode=" + str('utils.copySearch')
                    + "&keyword=" + urllib_parse.quote_plus(keyword))
        contextMenuItems.append(('Remove keyword', 'RunPlugin(' + keyw + ')'))
        contextMenuItems.append(('Edit keyword', 'RunPlugin(' + keywedit + ')'))
        contextMenuItems.append(('Copy keyword', 'RunPlugin(' + keywcopy + ')'))
    if list_avail:
        favtext = "Remove from" if fav == 'del' else "Add to"
        fav_url = (sys.argv[0]
                   + "?url=" + urllib_parse.quote_plus(url)
                   + "&fav=" + fav
                   + "&favmode=" + str(mode)
                   + "&mode=" + str('favorites.Favorites')
                   + "&img=" + urllib_parse.quote_plus(iconimage)
                   + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('{} favorites'.format(favtext), 'RunPlugin(' + fav_url + ')'))

        list_item_name = 'Add to My Lists'
        list_url = (sys.argv[0]
                    + "?url=" + urllib_parse.quote_plus(url)
                    + "&favmode=" + str(mode)
                    + "&mode=" + str('favorites.add_listitem')
                    + "&img=" + urllib_parse.quote_plus(iconimage)
                    + "&name=" + urllib_parse.quote_plus(name))
        contextMenuItems.append(('%s' % list_item_name, 'RunPlugin(' + list_url + ')'))
    if listitem_id:
        move_listitem_url = (sys.argv[0]
                             + "?mode=" + str('favorites.move_listitem')
                             + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('Move item to ...', 'RunPlugin(' + move_listitem_url + ')'))
        listitem_url = (sys.argv[0]
                        + "?mode=" + str('favorites.remove_listitem')
                        + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('Remove from list', 'RunPlugin(' + listitem_url + ')'))
        moveupitem_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_listitem')
                          + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('Move item Up', 'RunPlugin(' + moveupitem_url + ')'))
        movedownitem_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_listitem')
                            + "&listitem_id=" + str(listitem_id))
        contextMenuItems.append(('Move item Down', 'RunPlugin(' + movedownitem_url + ')'))

    if custom_list:
        editlist_url = (sys.argv[0]
                        + "?mode=" + str('favorites.edit_list')
                        + "&rowid=" + str(url))
        contextMenuItems.append(('Edit name', 'RunPlugin(' + editlist_url + ')'))
        dellist_url = (sys.argv[0]
                       + "?mode=" + str('favorites.remove_list')
                       + "&rowid=" + str(url))
        contextMenuItems.append(('Remove list', 'RunPlugin(' + dellist_url + ')'))
        moveuplist_url = (sys.argv[0]
                          + "?mode=" + str('favorites.moveup_list')
                          + "&rowid=" + str(url))
        contextMenuItems.append(('Move list Up', 'RunPlugin(' + moveuplist_url + ')'))
        movedownlist_url = (sys.argv[0]
                            + "?mode=" + str('favorites.movedown_list')
                            + "&rowid=" + str(url))
        contextMenuItems.append(('Move list Down', 'RunPlugin(' + movedownlist_url + ')'))

    settings_url = (sys.argv[0]
                    + "?mode=" + str('utils.openSettings'))
    contextMenuItems.append(
        ('Addon settings', 'RunPlugin(' + settings_url + ')'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=False)
    ok = xbmcplugin.addDirectoryItem(handle=addon_handle, url=u, listitem=liz, isFolder=Folder)
    return ok


def searchDir(url, mode, page=None, alphabet=None):
    if not alphabet:
        addDir('One time search', url, 'utils.oneSearch', addon_image('addon-search.png'), page=page, channel=mode, Folder=False)
        addDir('Add Keyword', url, 'utils.newSearch', addon_image('addon-search.png'), '', mode, Folder=False)
        addDir('Alphabetical', url, 'utils.alphabeticalSearch', addon_image('addon-search.png'), '', mode)
        if addon.getSetting('keywords_sorted') == 'true':
            addDir('Unsorted Keywords', url, 'utils.setUnsorted', addon_image('addon-search.png'), '', mode, Folder=False)
        else:
            addDir('Sorted Keywords', url, 'utils.setSorted', addon_image('addon-search.png'), '', mode, Folder=False)
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()

    try:
        if alphabet:
            c.execute("SELECT * FROM keywords WHERE keyword LIKE ? ORDER BY keyword ASC", (alphabet.lower() + '%', ))
        else:
            if addon.getSetting('keywords_sorted') == 'true':
                c.execute("SELECT * FROM keywords ORDER by keyword")
            else:
                c.execute("SELECT * FROM keywords ORDER BY rowid DESC")
        for (keyword,) in c.fetchall():
            keyword = keyword if six.PY3 else keyword.encode('utf8')
            keyword = urllib_parse.unquote_plus(keyword)
            name = keyword
            addDir(name, url, mode, addon_image('addon-search.png'), page=page, keyword=keyword)
    except:
        pass
    conn.close()
    eod()


def keys():
    ret = {}
    conn = sqlite3.connect(favoritesdb)
    c = conn.cursor()
    try:
        c.execute("""SELECT substr(upper(keyword),1,1) AS letter, count(keyword) AS count FROM keywords
                     GROUP BY substr(upper(keyword),1,1)
                     ORDER BY keyword""")
        for (letter, count) in c.fetchall():
            ret[letter] = count
    except:
        pass
    conn.close()
    return ret


def clean_temp():
    shutil.rmtree(tempDir)
    os.makedirs(tempDir)
