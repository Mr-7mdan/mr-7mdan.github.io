# -*- coding: utf-8 -*-
"""
Best Drama Site Module
https://best-drama.com

Asian/Arabic drama site (theme: ourdrama). Series-heavy.
Structure (verified live via probe harness):
  - Listings: /movies/ , /series/ , /episodes/ , /cate-serie/<slug>/
    Each item: <div class="postmovie"> ... <a href="URL"> ... <img src="IMG" alt="TITLE">
  - Item routing by URL:
      /series/<slug>/   -> series page (episode list) -> getEpisodes  (Pattern B, no seasons)
      /episodes/<slug>/ -> single episode watch page   -> getLinks
      /movies/<slug>/   -> single movie watch page      -> getLinks
  - Pagination: <link rel="next" href="..."/>
  - Search: regular GET /?s=<query>
  - Episode list (on a /series/ page): inside <div class="box-loop-episode"> ...
      <a href=".../episodes/<slug>/" class="colorsw"><div class="titlepisode">الحلقة N</div>
  - Watch page servers (verified live 2026-06):
      Both episodes AND movies now use ONE markup:
        <li class="getplay ..." data-url="https://<base>/embed_player/?code=...">HOST</li>
          -> internal embed_player page contains <iframe src="REAL_EMBED">
      BUT: a /movies/<slug>/ page is an info page with NO server <li>; the server
      tabs only render on the watch variant (<slug>/?watch). /episodes/ pages embed
      the tabs inline (no ?watch needed). getLinks therefore retries with ?watch when
      the first fetch yields no servers. The legacy hrefa/titlea movie markup is gone
      (kept only as a defensive fallback).
    Real embed hosts seen: 7.rpmvid.site (rpmshare), ourdrama.cc (earnvids),
      vidmoly.net, streamwish.to, ok.ru, vk.com
"""

import re
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('bestdrama', 'Best Drama', url=None, image='sites/bestdrama.png')

# Shared item pattern (works on movies/series/episodes/category/search pages)
LIST_PATTERN = (
    r'<div class="postmovie">.*?<div class="postmovie-photo">\s*'
    r'<a href="([^"]+)">\s*<div class="postmovie-thumb-bg">'
    r'<img[^>]*src="([^"]+)"[^>]*alt="([^"]*)"'
)

# Category listing (cate-serie) discovered from the live homepage/series page
CATEGORIES = [
    ('مسلسلات كورية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d9%83%d9%88%d8%b1%d9%8a%d8%a9/'),
    ('مسلسلات صينية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b5%d9%8a%d9%86%d9%8a%d8%a9/'),
    ('دراما صينية', '/cate-serie/%d8%af%d8%b1%d8%a7%d9%85%d8%a7-%d8%b5%d9%8a%d9%86%d9%8a%d8%a9/'),
    ('مسلسلات تركية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/'),
    ('مسلسلات تايلندية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%a7%d9%8a%d9%84%d9%86%d8%af%d9%8a%d8%a9/'),
    ('مسلسلات يابانية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d9%8a%d8%a7%d8%a8%d8%a7%d9%86%d9%8a%d8%a9/'),
    ('مسلسلات فلبينية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d9%81%d9%84%d8%a8%d9%8a%d9%86%d9%8a%d8%a9/'),
    ('مسلسلات باكستانية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a8%d8%a7%d9%83%d8%b3%d8%aa%d8%a7%d9%86%d9%8a%d8%a9/'),
    ('مسلسلات عربية', '/cate-serie/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b9%d8%b1%d8%a8%d9%8a%d8%a9/'),
    ('رومانسي', '/cate-serie/%d8%b1%d9%88%d9%85%d8%a7%d9%86%d8%b3%d9%8a/'),
    ('كوميدي', '/cate-serie/%d9%83%d9%88%d9%85%d9%8a%d8%af%d9%8a/'),
    ('برامج', '/cate-serie/%d8%a8%d8%b1%d8%a7%d9%85%d8%ac/'),
]


def _clean_title(title):
    title = title.strip()
    title = re.sub(r'مشاهدة|تحميل|اون لاين|مترجمة|مترجم|مدبلجة|مدبلج|كاملة|كامل|HD', '', title).strip()
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def _extract_year(title):
    year = ''
    m = re.search(r'(19|20)\d{2}', title)
    if m:
        year = m.group(0)
        title = title.replace(year, '').strip()
    return title, year


def _route_item(item_url, title, image, year):
    """Route a discovered item to the right handler based on its URL type."""
    full_image = re.sub(r'-\d+x\d+', '', image)
    if '/series/' in item_url:
        site.add_dir(title, item_url, 'getEpisodes', full_image, year=year, media_type='tvshow')
    elif '/episodes/' in item_url:
        site.add_dir(title, item_url, 'getLinks', full_image, year=year, media_type='episode')
    else:  # /movies/
        site.add_dir(title, item_url, 'getLinks', full_image, year=year, media_type='movie')


@site.register(default_mode=True)
def Main():
    """Main menu"""
    site.add_dir('Asian Movies', site.url + '/movies/', 'getMovies', get_category_icon('Asian Movies') or site.image)
    site.add_dir('Asian TV Shows', site.url + '/series/', 'getMovies', get_category_icon('Asian TV Shows') or site.image)
    site.add_dir('Recently Added', site.url + '/episodes/', 'getMovies', get_category_icon('Recently Added') or site.image)

    for label, path in CATEGORIES:
        site.add_dir(label, site.url + path, 'getMovies', get_category_icon(label) or site.image)

    site.add_dir('Search', '', 'search', get_category_icon('Search') or site.image)
    utils.eod()


@site.register()
def search():
    """Regular GET search (/?s=). Returns mixed movies/series/episodes."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    search_url = site.url + '/?s=' + urllib_parse.quote_plus(search_text)
    getMovies(search_url)


@site.register()
def getMovies(url):
    """Generic listing (movies / series / episodes / categories / search)."""
    utils.kodilog(f'{site.title}: Getting listing from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='movies')
        return

    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    for item_url, image, title in matches:
        title = _clean_title(title)
        title, year = _extract_year(title)
        if title:
            _route_item(item_url, title, image, year)

    # Pagination (<link rel="next" href="..."/>)
    next_match = re.search(r'<link rel="next" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1).strip()
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))

    utils.eod(content='movies')


# Alias kept for clarity / contract completeness (series listing uses same parser).
@site.register()
def getTVShows(url):
    """TV shows listing (delegates to the shared listing parser)."""
    getMovies(url)


@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series (Pattern B: series page -> episodes directly)."""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    # Scope to the episode list container to avoid grabbing "related" widgets.
    block_match = re.search(r'box-loop-episode">(.*?)</section>', html, re.DOTALL)
    block = block_match.group(1) if block_match else html

    pattern = r'<a href="([^"]+/episodes/[^"]+)"[^>]*class="colorsw">\s*<div class="titlepisode">\s*([^<]+?)\s*</div>'
    episodes = re.findall(pattern, block, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')

    if not episodes:
        utils.notify(site.title, 'لا توجد حلقات', icon=site.image)
        utils.eod(content='episodes')
        return

    for ep_url, ep_title in episodes:
        ep_title = ep_title.strip()
        ep_num = ''
        ep_match = re.search(r'(\d+)', ep_title)
        if ep_match:
            ep_num = ep_match.group(1)
        display = f'{name} - {ep_title}' if name else ep_title
        site.add_dir(display, ep_url, 'getLinks', site.image, episode=ep_num, media_type='episode')

    # Episode pagination (long-running shows)
    next_match = re.search(r'<link rel="next" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1).strip()
        site.add_dir('Next Page', next_url, 'getEpisodes', addon_image(site.img_next))

    utils.eod(content='episodes')


def _resolve_embed_player(embed_player_url):
    """Fetch an internal /embed_player/?code=... page and return the real iframe src."""
    try:
        html = utils.getHtml(embed_player_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
        if html:
            m = re.search(r'<iframe[^>]+src="([^"]+)"', html)
            if m:
                return m.group(1).strip()
    except Exception as e:
        utils.kodilog(f'{site.title}: embed_player resolve failed: {e}')
    return None


def _watch_url(url):
    """Return the ?watch variant of a watch page (movie info pages need it)."""
    if re.search(r'[?&]watch(\b|=|&|$)', url):
        return url
    return url + ('&watch' if '?' in url else '?watch')


def _extract_servers(html):
    """Parse server <li> from a watch page -> list of (embed_url, host_label).

    Domain-agnostic: matches any data-url=".../embed_player/?code=..." (current
    markup) and the legacy hrefa/titlea markup as a fallback.
    """
    servers = []
    # Primary markup: data-url -> internal embed_player -> real iframe src.
    for embed_player_url, host in re.findall(
            r'<li class="getplay[^"]*"[^>]*data-url="([^"]+)">\s*([^<]*?)\s*</li>', html):
        real = _resolve_embed_player(embed_player_url) if '/embed_player/' in embed_player_url else embed_player_url
        if real:
            if real.startswith('//'):
                real = 'https:' + real
            servers.append((real, host.strip() or 'Server'))

    # Legacy fallback: hrefa carries the real embed URL directly.
    if not servers:
        for embed_url, host in re.findall(
                r'<li class="getplay[^"]*"[^>]*hrefa="([^"]+)"[^>]*titlea="([^"]*)"', html):
            embed_url = embed_url.strip()
            if embed_url:
                if embed_url.startswith('//'):
                    embed_url = 'https:' + embed_url
                servers.append((embed_url, host.strip() or 'Server'))
    return servers


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
    servers = _extract_servers(html)

    # Movie info pages have no server tabs inline; they live on the ?watch variant.
    if not servers:
        watch_url = _watch_url(url)
        if watch_url != url:
            utils.kodilog(f'{site.title}: No servers inline, retrying watch page: {watch_url}')
            html = utils.getHtml(watch_url, headers={'User-Agent': utils.USER_AGENT},
                                 site_name=site.name, referer=url) or html
            servers = _extract_servers(html)

    utils.kodilog(f'{site.title}: Found {len(servers)} servers')

    for embed_url, host in servers:
        label, should_skip = utils.format_resolver_link(
            hoster_manager, embed_url, site.title, name, quality=host or 'Server')
        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)

    if not servers:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play a video."""
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
