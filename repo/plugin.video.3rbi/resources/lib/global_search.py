# -*- coding: utf-8 -*-
"""
Global Search - searches all active sites asynchronously
Registered modes: global_search.show_menu, global_search.search_movies, global_search.search_tvshows
"""

import re
import threading
import importlib
from kodi_six import xbmcgui
from resources.lib import utils
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.url_dispatcher import URL_Dispatcher

url_dispatcher = URL_Dispatcher('global_search')

# Search URL template per site name.
# {base} = site.url, {q} = encoded query
SEARCH_CONFIG = {
    # url: search URL template  content: movies|tvshows|both
    # mode_movies/mode_tvshows: function to call when user clicks a search result
    'cima4u':    {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getLinks'},
    'arabseed':  {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getSeasons'},
    'fajershow': {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getSeasons'},
    'faselhd':   {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getSeasons'},
    'egydead':   {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getSeasons'},
    'shoofvod':  {'url': '{base}/Search/{q}',        'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getLinks'},
    'shoofmax':  {'url': '{base}/search?q={q}',      'content': 'both',    'mode_movies': 'PlayVid',   'mode_tvshows': 'PlayVid'},
    'esseq':     {'url': '{base}/?s={q}',            'content': 'movies',  'mode_movies': 'getLinks',  'mode_tvshows': 'getLinks'},
    'qrmzi':     {'url': '{base}/?s={q}',            'content': 'tvshows', 'mode_movies': 'PlayVid',   'mode_tvshows': 'PlayVid'},
    'daktna':    {'url': '{base}/search.php?q={q}',  'content': 'tvshows', 'mode_movies': 'getLinks',  'mode_tvshows': 'getLinks'},
    'asia2tv':   {'url': '{base}?s={q}',             'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getLinks'},
    'akwam':     {'url': '{base}/?s={q}',            'content': 'both',    'mode_movies': 'getLinks',  'mode_tvshows': 'getSeasons'},
}

# Common listing patterns tried in order
_COMMON_PATTERNS = [
    # postDiv (faselhd style)
    r'<div class="postDiv[^"]*">\s*<a href="(https?://[^"]+)"[^>]*>.*?(?:data-src|src)="([^"?]+)[^"]*".*?<div class="h1">([^<]+)</div>',
    # MovieBlock / li style
    r'<li[^>]+class="[^"]*[Mm]ovie[Bb]lock[^"]*"[^>]*>.*?<a href="(https?://[^"]+)".*?(?:data-image|src)="([^"]+)".*?<(?:h3|h2|div)[^>]*[Tt]itle[^>]*>([^<]+)</',
    # article with h3/h2 title
    r'<article[^>]*>.*?<a href="(https?://[^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)".*?<(?:h3|h2)[^>]*>([^<]+)</',
    # Generic card
    r'<div[^>]+class="[^"]*(?:card|item|post|movie)[^"]*"[^>]*>.*?<a href="(https?://[^"]+)".*?src="([^"?]+)[^"]*".*?<(?:h3|h2|h1|div)[^>]*>([^<]{3,80})</',
]


def _parse_html(html, site_name):
    """Try site-specific parser then common fallback. Returns list of (url, img, title, year)."""
    try:
        mod = importlib.import_module('resources.lib.sites.{}'.format(site_name))
        if hasattr(mod, '_parse_listing'):
            results = mod._parse_listing(html)
            if results:
                return results
    except Exception:
        pass

    for pattern in _COMMON_PATTERNS:
        try:
            matches = re.findall(pattern, html, re.DOTALL)
            if matches:
                results = []
                for m in matches:
                    item_url, img, raw_title = m[0], m[1], m[2]
                    title = re.sub(r'\s+', ' ', utils.cleantext(raw_title)).strip()
                    if not title or len(title) < 2:
                        continue
                    year_m = re.search(r'(20\d\d|19\d\d)', title)
                    year = year_m.group(1) if year_m else None
                    if year:
                        title = title.replace(year, '').strip(' -|:')
                    results.append((item_url, img, title, year))
                if results:
                    return results
        except Exception:
            pass
    return []


def _get_result_mode(site_name, content_type):
    """Return the correct mode to use when a search result is clicked."""
    cfg = SEARCH_CONFIG.get(site_name, {})
    if content_type == 'tvshows':
        return cfg.get('mode_tvshows', 'getLinks')
    return cfg.get('mode_movies', 'getLinks')


def _search_site_worker(site_instance, search_url, result_list, lock, content_type):
    """Thread worker: fetch + parse one site's search page."""
    try:
        html = utils.getHtml(search_url, headers={'User-Agent': utils.USER_AGENT},
                             site_name=site_instance.name)
        if not html:
            return
        items = _parse_html(html, site_instance.name)
        utils.kodilog('Global Search: {} found {} items'.format(site_instance.title, len(items)))
        if items:
            mode = _get_result_mode(site_instance.name, content_type)
            with lock:
                for item_url, img, title, year in items:
                    result_list.append({
                        'title': title,
                        'url': item_url,
                        'img': img or site_instance.image,
                        'year': year,
                        'site': site_instance.title,
                        'site_name': site_instance.name,
                        'site_image': site_instance.image,
                        'mode': mode,
                    })
    except Exception as e:
        utils.kodilog('Global Search: {} error - {}'.format(site_instance.title, str(e)))


def _run_global_search(query, content_type):
    """Core: search all matching sites in parallel, collect + display results."""
    if not query:
        utils.eod(content=content_type)
        return

    encoded = query.replace(' ', '+')
    active_sites = {s.name: s for s in SiteBase.get_sites()}

    work = []
    for name, cfg in SEARCH_CONFIG.items():
        if name not in active_sites:
            continue
        if cfg['content'] != 'both':
            if content_type == 'movies' and cfg['content'] != 'movies':
                continue
            if content_type == 'tvshows' and cfg['content'] != 'tvshows':
                continue
        site_inst = active_sites[name]
        if not site_inst.url:
            continue
        search_url = cfg['url'].replace('{base}', site_inst.url.rstrip('/')).replace('{q}', encoded)
        work.append((site_inst, search_url))

    if not work:
        utils.eod(content=content_type)
        return

    results = []
    lock = threading.Lock()
    progress = xbmcgui.DialogProgressBG()
    progress.create('Global Search', 'Searching {} sites for "{}"...'.format(len(work), query))

    threads = []
    for site_inst, search_url in work:
        t = threading.Thread(target=_search_site_worker,
                             args=(site_inst, search_url, results, lock, content_type))
        t.daemon = True
        threads.append(t)
        t.start()

    total = len(threads)
    for i, t in enumerate(threads):
        t.join(timeout=20)
        progress.update(int((i + 1) * 100 / total))

    progress.close()
    utils.kodilog('Global Search: Total results {}'.format(len(results)))

    if not results:
        utils.notify('Global Search', 'No results found for "{}"'.format(query))
        utils.eod(content=content_type)
        return

    results.sort(key=lambda x: (x['site'], x['title'].lower()))

    site_inst_map = {s.name: s for s in SiteBase.get_sites()}
    for item in results:
        title_label = '[COLOR cyan][{}][/COLOR] {}'.format(item['site'], item['title'])
        if item.get('year'):
            title_label += ' ({})'.format(item['year'])

        s = site_inst_map.get(item['site_name'])
        if s:
            s.add_dir(title_label, item['url'], item['mode'],
                      item['img'], fanart=item['img'], year=item.get('year'))

    utils.eod(content=content_type)


@url_dispatcher.register()
def show_menu():
    """Show Global Search submenu: Movies / TV Shows"""
    url_dispatcher.add_dir('Search Movies', '', 'search_movies',
                           addon_image('professional-icon-pack/Search.png'), list_avail=False)
    url_dispatcher.add_dir('Search TV Shows', '', 'search_tvshows',
                           addon_image('professional-icon-pack/Search.png'), list_avail=False)
    utils.eod()


@url_dispatcher.register()
def search_movies():
    """Global Search - Movies"""
    query = utils.get_search_input()
    _run_global_search(query, 'movies')


@url_dispatcher.register()
def search_tvshows():
    """Global Search - TV Shows"""
    query = utils.get_search_input()
    _run_global_search(query, 'tvshows')
