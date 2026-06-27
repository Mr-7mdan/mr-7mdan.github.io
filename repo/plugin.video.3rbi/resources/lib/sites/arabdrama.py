# -*- coding: utf-8 -*-
"""
Arab Drama Site Module
https://www.arab-drama.me

Asian/Korean drama site (series-heavy). The site is JS-driven, but all the
data needed by the scraper is exposed server-side:

  * Listing (homepage)       -> static `as-episode` blocks
  * Search                   -> JSON API `/api/search?q=` (results are base64 JSON)
  * Episodes + servers        -> a base64-encoded JSON blob inside `#datawatch`
                                 on every `/watch-<id>/<slug>/<ep>` page
  * A "server" is a base64 string -> decodes to a `/embed?m=`/`?o=` URL whose
    page carries a direct `<source src="...mp4/m3u8">`.

No JS execution is required — only base64 decoding.
"""

import re
import json
import base64
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('arabdrama', 'Arab Drama', url=None, image='sites/arabdrama.png')

EPS_PER_PAGE = 50


def _b64json(blob):
    """Decode a base64 string into a Python object (JSON)."""
    return json.loads(base64.b64decode(blob).decode('utf-8'))


def _datawatch(html):
    """Extract & decode the #datawatch base64 JSON blob from a watch page."""
    m = re.search(r"id=['\"]datawatch['\"][^>]*>([A-Za-z0-9+/=]+)<", html)
    if not m:
        return None
    try:
        return _b64json(m.group(1).strip())
    except Exception as e:
        utils.kodilog(f'{site.title}: datawatch decode failed: {e}')
        return None


def _abs(url):
    if not url:
        return site.image
    if url.startswith('//'):
        return 'https:' + url
    if url.startswith('/'):
        return site.url + url
    return url


def _icon(label):
    """Category icon with a fallback to the site image."""
    from resources.lib.category_mapper import get_category_icon
    return get_category_icon(label) or site.image


# (label, type, Arabic tag) — tag is URL-encoded with quote at build time.
_CATEGORIES = [
    ('Asian TV Shows',     1, ''),
    ('Asian Movies',       0, ''),
    ('Korean TV Shows',    1, 'كوري'),
    ('Korean Movies',      0, 'كوري'),
    ('Japanese TV Shows',  1, 'ياباني'),
    ('Japanese Movies',    0, 'ياباني'),
    ('Chinese TV Shows',   1, 'صيني'),
    ('Chinese Movies',     0, 'صيني'),
    ('Taiwanese TV Shows', 1, 'تايواني'),
    ('Taiwanese Movies',   0, 'تايواني'),
    ('Thai TV Shows',      1, 'تايلندي'),
    ('Thai Movies',        0, 'تايلندي'),
]


def _api_url(type_, tag, page=1):
    """Build the JSON listing API URL for a (type, tag, page)."""
    return (f'{site.url}/api?order=2&type={type_}&stat='
            f'&tags={urllib_parse.quote(tag)}&page={page}')


@site.register(default_mode=True)
def Main():
    """Main menu

    NOTE: these are written as LITERAL add_dir calls (not a loop) with pre-encoded
    tag URLs so category_browser.py can statically extract each category for the
    cross-site "Browse by Category" view (it regex-parses Main's source and evals
    only `site.url + 'literal'` URL expressions — no function calls, no builtins).
    Tags are URL-encoded inline: كوري=%D9%83%D9%88%D8%B1%D9%8A, ياباني=%D9%8A%D8%A7%D8%A8%D8%A7%D9%86%D9%8A,
    صيني=%D8%B5%D9%8A%D9%86%D9%8A, تايواني=%D8%AA%D8%A7%D9%8A%D9%88%D8%A7%D9%86%D9%8A, تايلندي=%D8%AA%D8%A7%D9%8A%D9%84%D9%86%D8%AF%D9%8A
    """
    site.add_dir('Asian TV Shows',     site.url + '/api?order=2&type=1&stat=&tags=&page=1', 'getApiList', _icon('Asian TV Shows'))
    site.add_dir('Asian Movies',       site.url + '/api?order=2&type=0&stat=&tags=&page=1', 'getApiList', _icon('Asian Movies'))
    site.add_dir('Korean TV Shows',    site.url + '/api?order=2&type=1&stat=&tags=%D9%83%D9%88%D8%B1%D9%8A&page=1', 'getApiList', _icon('Korean TV Shows'))
    site.add_dir('Korean Movies',      site.url + '/api?order=2&type=0&stat=&tags=%D9%83%D9%88%D8%B1%D9%8A&page=1', 'getApiList', _icon('Korean Movies'))
    site.add_dir('Japanese TV Shows',  site.url + '/api?order=2&type=1&stat=&tags=%D9%8A%D8%A7%D8%A8%D8%A7%D9%86%D9%8A&page=1', 'getApiList', _icon('Japanese TV Shows'))
    site.add_dir('Japanese Movies',    site.url + '/api?order=2&type=0&stat=&tags=%D9%8A%D8%A7%D8%A8%D8%A7%D9%86%D9%8A&page=1', 'getApiList', _icon('Japanese Movies'))
    site.add_dir('Chinese TV Shows',   site.url + '/api?order=2&type=1&stat=&tags=%D8%B5%D9%8A%D9%86%D9%8A&page=1', 'getApiList', _icon('Chinese TV Shows'))
    site.add_dir('Chinese Movies',     site.url + '/api?order=2&type=0&stat=&tags=%D8%B5%D9%8A%D9%86%D9%8A&page=1', 'getApiList', _icon('Chinese Movies'))
    site.add_dir('Taiwanese TV Shows', site.url + '/api?order=2&type=1&stat=&tags=%D8%AA%D8%A7%D9%8A%D9%88%D8%A7%D9%86%D9%8A&page=1', 'getApiList', _icon('Taiwanese TV Shows'))
    site.add_dir('Taiwanese Movies',   site.url + '/api?order=2&type=0&stat=&tags=%D8%AA%D8%A7%D9%8A%D9%88%D8%A7%D9%86%D9%8A&page=1', 'getApiList', _icon('Taiwanese Movies'))
    site.add_dir('Thai TV Shows',      site.url + '/api?order=2&type=1&stat=&tags=%D8%AA%D8%A7%D9%8A%D9%84%D9%86%D8%AF%D9%8A&page=1', 'getApiList', _icon('Thai TV Shows'))
    site.add_dir('Thai Movies',        site.url + '/api?order=2&type=0&stat=&tags=%D8%AA%D8%A7%D9%8A%D9%84%D9%86%D8%AF%D9%8A&page=1', 'getApiList', _icon('Thai Movies'))
    site.add_dir('Search', '', 'search', _icon('Search'))
    utils.eod()


@site.register()
def search():
    """Search via the JSON API (/api/search?q=)."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    api_url = site.url + '/api/search?q=' + urllib_parse.quote(search_text)
    html = utils.getHtml(api_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)

    results = []
    if html:
        try:
            data = json.loads(html)
            for blob in data.get('SearchResaults', []) or []:
                try:
                    results.append(_b64json(blob))
                except Exception:
                    continue
        except Exception as e:
            utils.kodilog(f'{site.title}: search JSON parse failed: {e}')

    utils.kodilog(f'{site.title}: Found {len(results)} search results')

    if not results:
        utils.notify(site.title, 'لا توجد نتائج', icon=site.image)
        utils.eod(content='tvshows')
        return

    for it in results:
        title = (it.get('drama_name') or '').strip()
        drama_id = it.get('drama_id')
        slug = it.get('drama_slug') or ''
        if not title or drama_id is None or not slug:
            continue
        year = str(it.get('drama_release_date') or '').strip()
        image = _abs(it.get('drama_cover_image_url'))
        mt = 'movie' if (it.get('drama_type') == 'Movie') else 'tvshow'
        # Build a watch URL (episode 1) — its #datawatch lists all episodes.
        # The show poster rides along in `keyword` so episodes can reuse it.
        watch_url = f'{site.url}/watch-{drama_id}/{slug}/1'
        site.add_dir(title, watch_url, 'getEpisodes', image,
                     keyword=image, year=year, media_type=mt)

    utils.eod(content='tvshows')


def _next_page_url(url, page):
    """Return `url` with its `page=` query value set to `page`."""
    if re.search(r'([?&]page=)\d+', url):
        return re.sub(r'([?&]page=)\d+', lambda m: m.group(1) + str(page), url)
    sep = '&' if '?' in url else '?'
    return f'{url}{sep}page={page}'


@site.register()
def getApiList(url):
    """Listing from the JSON API. Each Show is a base64-encoded JSON object."""
    utils.kodilog(f'{site.title}: API list from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)

    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return

    try:
        data = json.loads(html)
    except Exception as e:
        utils.kodilog(f'{site.title}: API JSON parse failed: {e}')
        utils.eod(content='tvshows')
        return

    shows = data.get('Shows') or []
    count = 0
    for blob in shows:
        try:
            it = _b64json(blob)
        except Exception:
            continue
        title = (it.get('drama_name') or '').strip()
        drama_id = it.get('drama_id')
        slug = it.get('drama_slug') or ''
        if not title or drama_id is None or not slug:
            continue
        # drama_cover_image_url is relative (prefix base) or already absolute.
        poster = _abs(it.get('drama_cover_image_url'))
        mt = 'movie' if (it.get('drama_type') == 'Movie') else 'tvshow'
        # Route to episodes via the watch URL; thread the show poster in `keyword`.
        watch_url = f'{site.url}/watch-{drama_id}/{slug}/1'
        site.add_dir(title, watch_url, 'getEpisodes', poster,
                     keyword=poster, media_type=mt)
        count += 1

    utils.kodilog(f'{site.title}: Listed {count} items')

    try:
        cur = int(data.get('current_page') or 1)
        last = int(data.get('last_page') or 1)
    except (TypeError, ValueError):
        cur, last = 1, 1
    # next_page_url is present even on the last page, so gate on the page numbers.
    if cur < last:
        site.add_dir('Next Page', _next_page_url(url, cur + 1), 'getApiList',
                     addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getTVShows(url):
    """TV-show listing (delegates to the shared API listing)."""
    getApiList(url)


@site.register()
def getMovies(url):
    """Movie listing (delegates to the shared API listing)."""
    getApiList(url)


@site.register()
def getEpisodes(url, name='', keyword='', page=None):
    """List all episodes of a drama from the watch page's #datawatch blob.

    `keyword` carries the show poster threaded from the listing item, used as
    every episode's thumbnail/fanart.
    """
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)

    data = _datawatch(html) if html else None
    if not data:
        utils.kodilog(f'{site.title}: No #datawatch data')
        utils.eod(content='episodes')
        return

    show_name = name
    try:
        show_name = name or data['show_info'][0].get('drama_name', '')
    except Exception:
        pass

    # Show poster: prefer the one threaded from the listing, else the blob's own.
    poster = keyword or ''
    if not poster:
        try:
            poster = _abs(data['show_info'][0].get('drama_cover_image_url'))
        except Exception:
            poster = site.image
    poster = poster or site.image

    eps = data.get('eps_urls') or []
    utils.kodilog(f'{site.title}: Found {len(eps)} episodes')

    try:
        page = int(page) if page else 1
    except (TypeError, ValueError):
        page = 1
    start = (page - 1) * EPS_PER_PAGE
    chunk = eps[start:start + EPS_PER_PAGE]

    for ep in chunk:
        ep_url = ep.get('watch_url')
        ep_name = (ep.get('episode_name') or '').strip()
        ep_num = str(ep.get('episode_number') or '').strip()
        if not ep_url:
            continue
        ep_title = f'{show_name} - {ep_name}'.strip(' -') if show_name else ep_name
        site.add_dir(ep_title, ep_url, 'getLinks', poster,
                     fanart=poster, episode=ep_num, media_type='episode')

    # Client-side pagination (eps_urls is a single JSON array).
    if start + EPS_PER_PAGE < len(eps):
        site.add_dir('Next Page', url, 'getEpisodes',
                     addon_image(site.img_next), keyword=poster, page=page + 1)

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract server (embed) links for an episode from #datawatch."""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)

    data = _datawatch(html) if html else None
    if not data:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    servers = []
    try:
        for enc in data['ep_info'][0].get('stream_servers', []) or []:
            try:
                servers.append(base64.b64decode(enc).decode('utf-8'))
            except Exception:
                continue
    except Exception as e:
        utils.kodilog(f'{site.title}: stream_servers decode failed: {e}')

    utils.kodilog(f'{site.title}: Found {len(servers)} servers')

    hoster_manager = get_hoster_manager()
    for i, embed_url in enumerate(servers, 1):
        embed_url = embed_url.strip()
        if not embed_url:
            continue
        server_name = f'Server {i}'
        label, should_skip = utils.format_resolver_link(
            hoster_manager, embed_url, site.title, name, quality=server_name)
        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)

    if not servers:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve an embed URL to a direct stream and play it."""
    utils.kodilog(f'{site.title}: Resolving URL: {url[:100]}')

    video_url = None
    # The /embed page carries a direct <source src="...mp4/m3u8">.
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if html:
        m = re.search(r'<source[^>]+src="(https?://[^"]+\.(?:m3u8|mp4)[^"]*)"', html)
        if m and '/static/images/' not in m.group(1):
            video_url = m.group(1)

    # Fallback: let the hoster manager try (external/backup hosts).
    if not video_url:
        result = get_hoster_manager().resolve(url, referer=site.url)
        if result and result.get('url'):
            video_url = result['url']

    if video_url:
        utils.kodilog(f'{site.title}: Playing: {video_url[:100]}')
        utils.VideoPlayer(name, False).play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'فشل تشغيل الفيديو', icon=site.image)
