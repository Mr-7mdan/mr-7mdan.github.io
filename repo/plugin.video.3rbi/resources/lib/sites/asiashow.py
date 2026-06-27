# -*- coding: utf-8 -*-
"""
AsiaShow Site Module
https://asiashow.net

Asian/Arabic drama site (WordPress + "ts-feed"/Elementor "extended-toolkit" theme).
TV hierarchy: Pattern B — series page lists its episodes directly (no seasons step).
Search: regular WordPress ?s= (archive <li> list, different markup than listings).
Video servers: base64-encoded embed URLs in <li data-etk-server-btn data-etk-src="...">.
"""

import re
import base64
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('asiashow', 'AsiaShow', url=None, image='sites/asiashow.png')

# --- Tested patterns --------------------------------------------------------
# Poster/episode card (movies, series, genre listings AND episode cards on a series page)
CARD_PATTERN = (
    r'<article class="etk-card[^>]*>\s*'
    r'<a class="etk-card-link" href="([^"]+)"[^>]*>'
    r'.*?<img class="etk-card-img"\s+src="([^"]+)"'
    r'.*?<h2 class="etk-card-title">([^<]+)</h2>'
)
# Search results = plain archive <li><a> list (domain-agnostic)
SEARCH_PATTERN = (
    r'<li>\s*<a href="(https?://[^"]+/(?:series|movies|episodes)/[^"]+)">([^<]+)</a>\s*</li>'
)
# Episode cards live inside the "extended-toolkit-episode-card" Elementor widget.
# Scoping to that widget keeps related/popular poster cards (and any site-wide
# "latest episodes" widget) from leaking into a series' episode list.
EPISODE_PATTERN = (
    r'extended-toolkit-episode-card.*?'
    r'<a class="etk-card-link" href="([^"]+)"[^>]*>'
    r'.*?<img class="etk-card-img"\s+src="([^"]+)"'
    r'.*?<h2 class="etk-card-title">([^<]+)</h2>'
)
# Video server buttons: base64 embed url + label
SERVER_PATTERN = (
    r'data-etk-server-btn\s+data-etk-src="([^"]+)"[^>]*>\s*'
    r'<span class="etk-popup-item-label">([^<]+)</span>'
)

_JUNK = r'مشاهدة|تحميل|اون لاين|أون لاين|مترجمة|مترجم|مدبلجة|مدبلج|كاملة|كامل|HD'

# Listing pagination — the Voxel theme "ts-post-feed" widget paginates via a JS
# "load more" button (data-paginate="load_more", data-per-page="40"); there is NO
# path-based /movies/page/2/ (those 404). The button GETs the Voxel front-end AJAX
# endpoint /?vx=1&action=search_posts&type=<key>[&genres=<slug>]&pg=<n>&limit=40,
# which returns the next 40 cards in the SAME etk-card markup (no nonce required).
PER_PAGE = 40


def _clean(title):
    title = title.strip()
    title = re.sub(_JUNK, '', title).strip()
    return re.sub(r'\s+', ' ', title).strip()


def _ajax_page_url(url, page):
    """Build the Voxel load-more URL for page N of an archive/genre listing.

    `type` (and the active genre term filter) are derived from the archive URL
    path: /movies/ -> movies, /series/ -> series, /genre/<slug>/ -> series + that
    genre slug. Mirrors the request the theme's JS sends on "load more".
    """
    path = urllib_parse.urlparse(url).path
    params = {'action': 'search_posts'}
    gm = re.search(r'/genre/([^/]+)/?', path)
    if gm:
        params['type'] = 'series'
        params['genres'] = gm.group(1)
    elif '/movies' in path:
        params['type'] = 'movies'
    else:
        params['type'] = 'series'
    if page > 1:
        params['pg'] = page
    params['limit'] = PER_PAGE
    return f'{site.url}/?vx=1&' + urllib_parse.urlencode(params)


@site.register(default_mode=True)
def Main():
    """Main menu"""
    site.add_dir('Asian TV Shows', site.url + '/series/', 'getTVShows', get_category_icon('Asian TV Shows') or site.image)
    site.add_dir('Asian Movies', site.url + '/movies/', 'getMovies', get_category_icon('Asian Movies') or site.image)
    site.add_dir('TV Programs', site.url + '/genre/shows/', 'getTVShows', get_category_icon('TV Programs') or site.image)
    site.add_dir('Search', '', 'search', get_category_icon('Search') or site.image)
    utils.eod()


@site.register()
def search():
    """Search via regular WordPress ?s= page (archive list markup)."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    search_url = site.url + '/?s=' + urllib_parse.quote(search_text)
    getSearch(search_url)


@site.register()
def getSearch(url):
    """Parse a WordPress ?s= search-results page (plain <li><a> archive list).

    Registered separately from the etk-card listing parsers because the search
    markup differs; this is the function global search calls for asiashow.
    """
    utils.kodilog(f'{site.title}: Search listing from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No search results')
        utils.eod(content='tvshows')
        return

    matches = re.findall(SEARCH_PATTERN, html)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    seen = set()
    found = 0
    for result_url, title in matches:
        if result_url in seen:
            continue
        seen.add(result_url)

        title = _clean(title)
        if not title:
            continue

        year = ''
        ym = re.search(r'(19|20)\d{2}', title)
        if ym:
            year = ym.group(0)

        if '/series/' in result_url:
            site.add_dir(title, result_url, 'getEpisodes', site.image,
                         year=year, media_type='tvshow')
        else:
            # /movies/ and /episodes/ are watch pages
            site.add_dir(title, result_url, 'getLinks', site.image,
                         year=year, media_type='movie')
        found += 1

    if not found:
        utils.notify(site.title, 'لا توجد نتائج', icon=site.image)

    utils.eod(content='tvshows')


def _list_cards(url, mode, content, page=1):
    """Shared listing parser for movies / series / genre pages.

    Page 1 is the archive HTML; later pages come from the Voxel load-more AJAX
    endpoint (both return identical etk-card markup).
    """
    page = int(page)
    fetch_url = url if page <= 1 else _ajax_page_url(url, page)
    utils.kodilog(f'{site.title}: Listing (page {page}) from: {fetch_url}')

    html = utils.getHtml(fetch_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content=content)
        return

    matches = re.findall(CARD_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    seen = set()
    for item_url, image, title in matches:
        # Episode cards can appear in feeds — keep listings to shows/movies
        if '/episodes/' in item_url:
            continue
        if item_url in seen:
            continue
        seen.add(item_url)

        title = _clean(title)
        if not title:
            continue

        year = ''
        ym = re.search(r'(19|20)\d{2}', title)
        if ym:
            year = ym.group(0)

        if '/series/' in item_url:
            site.add_dir(title, item_url, 'getEpisodes', image,
                         year=year, media_type='tvshow')
        else:
            site.add_dir(title, item_url, 'getLinks', image,
                         year=year, media_type='movie')

    # A full page of cards (== per-page) means there is very likely another page;
    # keep the original archive URL and bump the page counter.
    if len(matches) >= PER_PAGE:
        site.add_dir('Next Page', url, mode, addon_image(site.img_next),
                     page=page + 1)

    utils.eod(content=content)


@site.register()
def getMovies(url, page=1):
    """Get movies listing"""
    _list_cards(url, 'getMovies', 'movies', page=page)


@site.register()
def getTVShows(url, page=1):
    """Get TV shows listing"""
    _list_cards(url, 'getTVShows', 'tvshows', page=page)


@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series — listed directly on the series page (Pattern B)."""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    # Scope to the episode-card widget so related/popular poster cards and any
    # site-wide "latest episodes" widget can't leak into this series' list.
    matches = re.findall(EPISODE_PATTERN, html, re.DOTALL)

    episodes = []
    seen = set()
    for ep_url, image, title in matches:
        # Episode watch pages live under /episodes/ or /episode/ (singular variant).
        if '/episode' not in ep_url or ep_url in seen:
            continue
        seen.add(ep_url)

        title = _clean(title)
        ep_num = ''
        em = re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', title, re.IGNORECASE)
        if em:
            ep_num = em.group(1)
        full_image = re.sub(r'/w\d+/', '/w500/', image)
        episodes.append((ep_url, full_image, title, ep_num))

    # Sort ascending by episode number when available
    def _key(e):
        return int(e[3]) if e[3].isdigit() else 0
    episodes.sort(key=_key)

    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')

    if episodes:
        for ep_url, image, title, ep_num in episodes:
            site.add_dir(title, ep_url, 'getLinks', image,
                         episode=ep_num, media_type='episode')
    else:
        utils.notify(site.title, 'لم يتم العثور على حلقات', icon=site.image)

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract video server links from a movie/episode watch page."""
    utils.kodilog(f'{site.title}: Getting links from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    hoster_manager = get_hoster_manager()

    servers = re.findall(SERVER_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(servers)} servers')

    added = 0
    for b64_url, server_name in servers:
        try:
            embed_url = base64.b64decode(b64_url).decode('utf-8', 'ignore').strip()
        except Exception:
            continue
        if not embed_url.startswith('http'):
            continue

        server_name = server_name.strip() or 'Server'

        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            embed_url,
            site.title,
            name,
            quality=server_name
        )

        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)
            added += 1

    if not added:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    utils.kodilog(f'{site.title}: Resolving URL: {url[:100]}')

    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)

    if result and result.get('url'):
        video_url = result['url']
        utils.kodilog(f'{site.title}: Playing: {video_url[:100]}')

        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'فشل تشغيل الفيديو', icon=site.image)
