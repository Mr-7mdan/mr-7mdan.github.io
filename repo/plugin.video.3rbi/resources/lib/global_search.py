# -*- coding: utf-8 -*-
"""
Global Search - searches all active sites asynchronously.

Strategy (like plugin.video.matrix):
  - Call each site's LISTING function directly with a pre-built search URL
    (bypassing search() which shows a keyboard dialog)
  - Monkey-patch url_dispatcher.addDir / url_dispatcher.addDownLink
    (the actual call site used by ALL site.add_dir / site.add_download_link calls)
    using a threading.Lock to be thread-safe, capturing items into a
    thread-local list instead of sending them to Kodi's directory
  - After all threads finish, render the collected items normally
"""

import re
import threading
import importlib
import time
from resources.lib import utils
from resources.lib import basics
from resources.lib import url_dispatcher as _url_dispatcher_mod
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.url_dispatcher import URL_Dispatcher

url_dispatcher = URL_Dispatcher('global_search')

# Thread-local storage: each worker thread has its own item list
_thread_local = threading.local()

# Global lock protecting the monkey-patch swap (though swap is atomic in CPython)
_patch_lock = threading.Lock()

# ── SEARCH CONFIG ─────────────────────────────────────────────────────────────
# site_name -> {
#   'url': search URL pattern  ({base}=site.url, {q}=url-encoded query)
#   'func': name of the listing function in resources.lib.sites.<name>
#   'kwargs': optional extra kwargs to pass to the function
# }
SEARCH_CONFIG = {
    # Standard sites: listing func takes (url) as first arg
    'cimanow':          {'url': '{base}/?s={q}',                    'func': 'getMovies'},
    'cima4u':           {'url': '{base}/?s={q}',                    'func': 'getMovies'},
    'faselhd':          {'url': '{base}/?s={q}',                    'func': 'searchResults'},
    'egydead':          {'url': '{base}/?s={q}',                    'func': 'getMovies'},
    # egydrama search is broken server-side (/?s= returns homepage, search.php ignores query)
    # shoofvod: /Search/ endpoint is dead (redirects to homepage) - excluded
    'shoofmax':         {'url': '{base}/search?q={q}',              'func': 'getMovies'},
    'shahidmosalsalat': {'url': '{base}/search.php?keywords={q}',   'func': 'getTVShows',       'kwargs': {'is_search': True}},
    'asia2tv':          {'url': '{base}/search?s={q}',              'func': 'getMixed'},
    'larozza':          {'url': '{base}/search.php?keywords={q}',   'func': 'getVideos'},
    'daktna':           {'url': '{base}/search.php?q={q}',          'func': 'getTVShows'},
    'viola':            {'url': '{base}/search.php?keywords={q}',   'func': 'getMovies'},
    'esseq':            {'url': '{base}/?s={q}',                    'func': 'getMovies'},
    'qrmzi':            {'url': '{base}/?s={q}',                    'func': 'getTVShows'},
    'fajershow':        {'url': '{base}?s={q}',                     'func': 'searchResults'},
    'shhid4u':          {'url': '{base}/?s={q}',                    'func': 'getMixed'},
    # Special sites: listing func takes (url, mode, target_mode) or (keyword, content_type)
    'akwam':            {'url': '{base}/search?q={q}',              'func': '_common_listing',
                         'extra_args': ["'Search'", 'None']},
    'arabseed':         {'url': None,                               'func': '_performSearch',
                         'query_args': ['plain_query', 'content_type']},
}


# ── INTERCEPTORS ──────────────────────────────────────────────────────────────

def _make_intercept_addDir():
    """Returns a replacement for basics.addDir that captures items per thread."""
    def _intercept(name, url, mode, iconimage=None, *args, **kwargs):
        items = getattr(_thread_local, 'items', None)
        if items is not None:
            # Skip pagination / navigation entries
            if any(x in name for x in ['الصفحة التالية', 'Next Page', 'Next ', 'بحث', 'Search']):
                return
            # Skip items with no Arabic characters (likely site UI / nav junk)
            if not re.search(r'[\u0600-\u06ff]', name):
                return
            # Skip very short titles (< 3 Arabic chars) - likely navigation
            ar_chars = re.findall(r'[\u0600-\u06ff]', name)
            if len(ar_chars) < 3:
                return
            items.append({
                'name': name,
                'url': url,
                'mode': mode,
                'img': iconimage or '',
                'year': kwargs.get('year'),
                'is_folder': kwargs.get('Folder', True),
            })
        else:
            # Not in a search thread - call original
            basics._orig_addDir(name, url, mode, iconimage, *args, **kwargs)
    return _intercept


def _make_intercept_addDownLink():
    """Returns a replacement for basics.addDownLink that captures items per thread."""
    def _intercept(name, url, mode, iconimage=None, *args, **kwargs):
        items = getattr(_thread_local, 'items', None)
        if items is not None:
            items.append({
                'name': name,
                'url': url,
                'mode': mode,
                'img': iconimage or '',
                'year': kwargs.get('year'),
                'is_folder': False,
            })
        else:
            basics._orig_addDownLink(name, url, mode, iconimage, *args, **kwargs)
    return _intercept


def _intercept_eod(*args, **kwargs):
    """Swallow eod() calls from within search threads."""
    if getattr(_thread_local, 'items', None) is None:
        utils.eod(*args, **kwargs)


def _install_patches():
    """
    url_dispatcher.py does 'from resources.lib.basics import addDir, addDownLink'
    at import time, binding local names in its module dict.
    site.add_dir() calls those local names - NOT basics.addDir.
    So we must patch the local names IN url_dispatcher's module __dict__.
    We also patch basics module for any site that calls basics.addDir directly.
    """
    intercept_add_dir = _make_intercept_addDir()
    intercept_add_dl = _make_intercept_addDownLink()

    # Patch the local names that url_dispatcher.add_dir() actually calls
    _url_dispatcher_mod._orig_addDir = _url_dispatcher_mod.addDir
    _url_dispatcher_mod._orig_addDownLink = _url_dispatcher_mod.addDownLink
    _url_dispatcher_mod.addDir = intercept_add_dir
    _url_dispatcher_mod.addDownLink = intercept_add_dl

    # Also patch basics module for direct callers
    basics._orig_addDir = basics.addDir
    basics._orig_addDownLink = basics.addDownLink
    basics.addDir = intercept_add_dir
    basics.addDownLink = intercept_add_dl

    # Swallow eod() and notify() calls from background threads
    utils._orig_eod = utils.eod
    utils._orig_notify = utils.notify
    utils.eod = lambda *a, **kw: None
    utils.notify = lambda *a, **kw: None
    basics._orig_eod = basics.eod
    basics.eod = lambda *a, **kw: None


def _remove_patches():
    """Restore all patched functions."""
    if hasattr(_url_dispatcher_mod, '_orig_addDir'):
        _url_dispatcher_mod.addDir = _url_dispatcher_mod._orig_addDir
    if hasattr(_url_dispatcher_mod, '_orig_addDownLink'):
        _url_dispatcher_mod.addDownLink = _url_dispatcher_mod._orig_addDownLink
    if hasattr(basics, '_orig_addDir'):
        basics.addDir = basics._orig_addDir
    if hasattr(basics, '_orig_addDownLink'):
        basics.addDownLink = basics._orig_addDownLink
    if hasattr(utils, '_orig_eod'):
        utils.eod = utils._orig_eod
    if hasattr(utils, '_orig_notify'):
        utils.notify = utils._orig_notify
    if hasattr(basics, '_orig_eod'):
        basics.eod = basics._orig_eod


# ── WORKER ────────────────────────────────────────────────────────────────────

def _search_site_worker(site_inst, cfg, plain_query, encoded_query, raw_query, results, lock, search_type='tvshows'):
    """Run in background thread. Captures items via thread-local list."""
    site_name = site_inst.name
    base_url = site_inst.url.rstrip('/')

    url_pattern = cfg.get('url') or ''
    search_url = (url_pattern
                  .replace('{base}', base_url)
                  .replace('{q}', encoded_query)
                  .replace('{q_raw}', raw_query))

    utils.kodilog('Global Search: {} -> {}'.format(site_inst.title, search_url))

    # Activate thread-local capture
    _thread_local.items = []

    try:
        mod = importlib.import_module('resources.lib.sites.{}'.format(site_name))
        func_name = cfg['func']

        if not hasattr(mod, func_name):
            utils.kodilog('Global Search: {} - function {} not found'.format(site_name, func_name))
            return

        func = getattr(mod, func_name)
        kwargs = dict(cfg.get('kwargs', {}))

        if 'query_args' in cfg:
            # arabseed-style: func(plain_query, content_type) - builds its own URL internally
            content_type_arg = 'movies' if search_type == 'movies' else 'series'
            args = [plain_query if a == 'plain_query' else
                    content_type_arg if a == 'content_type' else
                    a.strip("'") for a in cfg['query_args']]
            func(*args)
        elif 'extra_args' in cfg:
            # akwam-style: func(url, 'Search', None)
            extra = [None if a == 'None' else a.strip("'") for a in cfg['extra_args']]
            func(search_url, *extra)
        else:
            func(search_url, **kwargs)

        captured = list(_thread_local.items)
        utils.kodilog('Global Search: {} found {} items'.format(site_inst.title, len(captured)))

        if captured:
            with lock:
                for item in captured:
                    item['site'] = site_inst.title
                    item['site_name'] = site_name
                    item['site_img'] = site_inst.image
                    results.append(item)

    except Exception as e:
        utils.kodilog('Global Search: {} error - {}'.format(site_name, str(e)))
    finally:
        _thread_local.items = None


# ── POST-PROCESSING ───────────────────────────────────────────────────────────

# Arabic/English junk words to strip before similarity comparison
_JUNK_WORDS = re.compile(
    r'\b(مشاهدة|تحميل|مسلسل|فيلم|انمي|مترجم|مترجمة|مدبلج|كامل|كاملة|اون لاين|'
    r'الحلقة|حلقة|الجزء|جزء|الموسم|موسم|season|episode|ep\.?|part|s\d+e\d+)\b',
    re.IGNORECASE | re.UNICODE
)
# Matches "الحلقة 5", "ح 5", "ح5", "Ep 5", "Episode 5" at end of title (with optional trailing junk)
_EP_SUFFIX = re.compile(
    r'[\s\-–_]+(?:الحلقة|الحلقه|حلقة|ح\s*)[\s\d\-–]+.*$'
    r'|[\s\-–_]+(?:ep\.?\s*|episode\s*)[\d\s\-–]+.*$',
    re.IGNORECASE | re.UNICODE
)
# Detects whether a title IS an episode entry
_IS_EPISODE = re.compile(
    r'(?:الحلقة|الحلقه|حلقة|ح\s*)\s*\d+'
    r'|(?:\bep\.?\s*|episode\s*)\d+',
    re.IGNORECASE | re.UNICODE
)


def _clean_title(title):
    """Strip junk words and normalise Arabic for comparison."""
    t = _JUNK_WORDS.sub(' ', title)
    t = re.sub(r'\s+', ' ', t).strip()
    return t.lower()


def _filter_by_similarity(results, query):
    """
    Keep only results whose title shares at least one meaningful word with the query.
    Meaningful = length > 1 after stripping Arabic alef variants.
    """
    # Normalise alef forms so اورهان == أورهان == إورهان
    def norm(s):
        s = re.sub(r'[أإآا]', 'ا', s)
        return s.lower()

    q_clean = norm(_clean_title(query))
    q_words = {w for w in q_clean.split() if len(w) > 1}

    if not q_words:
        return results

    kept = []
    for item in results:
        t_clean = norm(_clean_title(item['name']))
        t_words = set(t_clean.split())
        if q_words & t_words:          # at least one word in common
            kept.append(item)

    utils.kodilog('Global Search: similarity filter {} -> {}'.format(len(results), len(kept)))
    return kept


def _deduplicate_episodes(results):
    """
    Detect episode entries by title (contains 'الحلقة N', 'ح N', 'Ep N', etc.)
    regardless of URL structure.  Group by (site, clean_show_title) and keep only
    one representative entry per show, using the item with the lowest episode number
    (so the show-level URL is most likely the series root).
    """
    seen = {}    # (site_name, clean_show_title) -> item
    non_ep = []

    for item in results:
        name = item['name']

        if _IS_EPISODE.search(name):
            # Strip episode suffix to recover the show title
            show_title = _EP_SUFFIX.sub('', name).strip()
            # Also strip trailing season/part suffix
            show_title = re.sub(
                r'[\s\-–_]+(?:الجزء|جزء|الموسم|موسم|part|season)[\s\d\-–]+$',
                '', show_title, flags=re.IGNORECASE | re.UNICODE
            ).strip()
            if not show_title:
                show_title = name  # fallback

            key = (item['site_name'], _clean_title(show_title))

            if key not in seen:
                new_item = dict(item)
                new_item['name'] = show_title
                new_item['is_folder'] = True
                # If URL contains /episode/, redirect to /season/ equivalent
                url = item.get('url', '')
                if '/episode/' in url:
                    new_item['url'] = re.sub(r'/episode/([^/]+)/', r'/season/\1/', url)
                    new_item['mode'] = item['site_name'] + '.getSeasons'
                seen[key] = new_item
        else:
            non_ep.append(item)

    deduped_eps = list(seen.values())
    utils.kodilog('Global Search: episode dedup {} eps -> {} shows'.format(
        len(results) - len(non_ep), len(deduped_eps)))

    # Also dedup non-episode entries per site by raw normalised title.
    # Use raw title (not _clean_title) so 'المداح 6' and 'المداح 7' remain distinct.
    def _norm_title(s):
        s = re.sub(r'[أإآا]', 'ا', s)
        return re.sub(r'\s+', ' ', s).strip().lower()
    seen_non_ep = {}
    for item in non_ep:
        key = (item['site_name'], _norm_title(item['name']))
        if key not in seen_non_ep:
            seen_non_ep[key] = item
    deduped_non_ep = list(seen_non_ep.values())

    return deduped_non_ep + deduped_eps


# ── KODI MENU ─────────────────────────────────────────────────────────────────

@url_dispatcher.register()
def show_menu(url=''):
    basics.addDir('Search Movies', '', 'global_search.search_movies',
                  addon_image('professional-icon-pack/Search.png'), list_avail=False)
    basics.addDir('Search TV Shows', '', 'global_search.search_tvshows',
                  addon_image('professional-icon-pack/Search.png'), list_avail=False)
    utils.eod()


@url_dispatcher.register()
def search_movies(url=''):
    query = utils.get_search_input()
    if query:
        _run_global_search(query, 'movies')
    else:
        utils.eod(content='movies')


@url_dispatcher.register()
def search_tvshows(url=''):
    query = utils.get_search_input()
    if query:
        _run_global_search(query, 'tvshows')
    else:
        utils.eod(content='tvshows')


# ── CORE SEARCH ───────────────────────────────────────────────────────────────

def _run_global_search(query, content_type):
    utils.kodilog('Global Search: Query="{}" Type={}'.format(query, content_type))

    if not query:
        utils.eod(content=content_type)
        return

    try:
        from urllib.parse import quote_plus, quote
    except ImportError:
        from urllib import quote_plus, quote

    encoded = quote_plus(query)
    raw = quote(query)

    active_sites = {s.name: s for s in SiteBase.get_sites()}

    work = []
    for site_name, cfg in SEARCH_CONFIG.items():
        if site_name not in active_sites:
            continue
        site_inst = active_sites[site_name]
        if not site_inst.url:
            continue
        work.append((site_inst, cfg))

    if not work:
        utils.kodilog('Global Search: No sites to search')
        utils.notify('Global Search', 'No sites configured for search')
        utils.eod(content=content_type)
        return

    utils.kodilog('Global Search: Searching {} sites'.format(len(work)))

    results = []
    lock = threading.Lock()

    # Install patches BEFORE starting threads
    _install_patches()

    try:
        threads = []
        for site_inst, cfg in work:
            t = threading.Thread(
                target=_search_site_worker,
                args=(site_inst, cfg, query, encoded, raw, results, lock, content_type)
            )
            t.daemon = True
            threads.append(t)
            t.start()

        # Single wall-clock deadline for ALL threads (true parallel)
        deadline = time.time() + 8
        for t in threads:
            remaining = deadline - time.time()
            if remaining <= 0:
                break
            t.join(timeout=remaining)

        still_running = [work[i][0].title for i, t in enumerate(threads) if t.is_alive()]
        if still_running:
            utils.kodilog('Global Search: Timed out: {}'.format(', '.join(still_running)))

    finally:
        # Always restore originals, even on exception
        _remove_patches()

    utils.kodilog('Global Search: Total results before filter {}'.format(len(results)))

    # ── Post-processing ───────────────────────────────────────────────────────
    results = _filter_by_similarity(results, query)
    results = _deduplicate_episodes(results)

    utils.kodilog('Global Search: Total results after filter {}'.format(len(results)))

    if not results:
        utils.notify('Global Search', 'No results found for "{}"'.format(query))
        utils.eod(content=content_type)
        return

    results.sort(key=lambda x: (x['site'], x['name'].lower()))

    for item in results:
        title_label = '[COLOR cyan][{}][/COLOR] {}'.format(item['site'], item['name'])
        img = item['img'] or item['site_img']

        if item['is_folder']:
            basics.addDir(title_label, item['url'], item['mode'],
                          img, year=item.get('year'), list_avail=False)
        else:
            basics.addDownLink(title_label, item['url'], item['mode'],
                               img, year=item.get('year'))

    utils.eod(content=content_type)
