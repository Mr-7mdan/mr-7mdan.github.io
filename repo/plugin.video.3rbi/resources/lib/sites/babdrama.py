# -*- coding: utf-8 -*-
"""
BabDrama Site Module
https://babdrama.com

Asian/Arabic-subtitled drama site (WordPress "arblionz"-style theme).
Series-only: no movies section. Hierarchy is Pattern A without seasons:
  series archive  ->  series page (/series/<slug>/)  ->  episode posts  ->  /watch servers
Listing markup is shared by the homepage (latest episodes), /series/, /views/
and ?s= search, so a single getList() parses & routes them all.
"""

import re
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('babdrama', 'BabDrama', url=None, image='sites/babdrama.png')

# Shared listing block: handles home/archive posters AND the /filtering pages
# (which insert whitespace between the MovieItem div and its <a>).
LIST_PATTERN = (
    r'<div class="MovieItem">\s*<a href="([^"]+)">.*?'
    r'background-image:\s*url\(([^)]+)\);?[^>]*></div>.*?'
    r'<h4>([^<]+)</h4>'
)

NEXT_PATTERN = r'<a class="next page-numbers" href="([^"]+)"'

# Stopwords to strip from titles
_JUNK = (r'مشاهدة|تحميل|جميع حلقات المسلسل|جميع حلقات|مسلسل|برنامج|انمي|'
         r'مترجمة|مترجم|مدبلجة|مدبلج|اون لاين|أون لاين|كاملة|كامل|HD')


def _clean_title(title):
    title = title.strip()
    title = re.sub(_JUNK, '', title).strip()
    title = re.sub(r'\s+', ' ', title).strip()
    return title


@site.register(default_mode=True)
def Main():
    """Main menu"""
    site.add_dir('Recently Added', site.url + '/', 'getList', get_category_icon('Recently Added') or site.image)
    site.add_dir('Asian TV Shows', site.url + '/series/', 'getList', get_category_icon('Asian TV Shows') or site.image)
    site.add_dir('Most Viewed', site.url + '/views/', 'getList', get_category_icon('Most Viewed') or site.image)
    # Category filtering (WordPress term IDs via /filtering?category=ID).
    site.add_dir('Chinese TV Shows', site.url + '/filtering?category=233', 'getList', get_category_icon('Chinese TV Shows') or site.image)
    site.add_dir('Korean TV Shows', site.url + '/filtering?category=1', 'getList', get_category_icon('Korean TV Shows') or site.image)
    site.add_dir('Thai TV Shows', site.url + '/filtering?category=151', 'getList', get_category_icon('Thai TV Shows') or site.image)
    site.add_dir('Japanese TV Shows', site.url + '/filtering?category=84', 'getList', get_category_icon('Japanese TV Shows') or site.image)
    site.add_dir('Filipino TV Shows', site.url + '/filtering?category=1661', 'getList', get_category_icon('Filipino TV Shows') or site.image)
    site.add_dir('Asian Variety Shows', site.url + '/filtering?category=2091', 'getList', get_category_icon('Asian Variety Shows') or site.image)
    site.add_dir('Taiwanese TV Shows', site.url + '/filtering?category=201', 'getList', get_category_icon('Taiwanese TV Shows') or site.image)
    site.add_dir('Indonesian TV Shows', site.url + '/filtering?category=5523', 'getList', get_category_icon('Indonesian TV Shows') or site.image)
    site.add_dir('Search', '', 'search', get_category_icon('Search') or site.image)
    utils.eod()


@site.register()
def search():
    """Regular ?s= search (markup identical to archive listings)."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    search_url = site.url + '/?s=' + urllib_parse.quote(search_text)
    getList(search_url)


@site.register()
def getList(url):
    """Unified listing: latest episodes, series archive, most-viewed, search.

    Routes /series/ posts to getEpisodes (TV shows) and individual
    episode posts to getLinks.
    """
    utils.kodilog(f'{site.title}: Getting list from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return

    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    for item_url, image, title in matches:
        title = _clean_title(title)
        if not title:
            continue

        year = ''
        year_match = re.search(r'(19|20)\d{2}', title)
        if year_match:
            year = year_match.group(0)

        if '/series/' in item_url:
            # Series container page -> list its episodes
            site.add_dir(title, item_url, 'getEpisodes', image,
                         year=year, media_type='tvshow')
        else:
            # Individual episode post -> servers
            site.add_dir(title, item_url, 'getLinks', image,
                         year=year, media_type='episode')

    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        next_url = urllib_parse.urljoin(site.url, next_match.group(1))
        site.add_dir('الصفحة التالية', next_url, 'getList', addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getEpisodes(url, name=''):
    """List episodes from a /series/<slug>/ page (inside div.EpisodesList)."""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    # Scope to the EpisodesList container so we don't grab related widgets
    block = re.search(r'<div class="EpisodesList"[^>]*>(.*?)</div>\s*</div>', html, re.DOTALL)
    section = block.group(1) if block else html

    episodes = re.findall(r'<a href="([^"]+)">\s*الحلقة\s*<em>(\d+)</em>\s*</a>',
                          section, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')

    show = _clean_title(name) if name else ''
    for ep_url, ep_num in episodes:
        ep_title = (f'{show} - الحلقة {ep_num}' if show else f'الحلقة {ep_num}')
        site.add_dir(ep_title, ep_url, 'getLinks', site.image,
                     episode=ep_num, media_type='episode')

    if not episodes:
        utils.notify(site.title, 'لا توجد حلقات', icon=site.image)

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract server embeds from an episode post's /watch page."""
    utils.kodilog(f'{site.title}: Getting links from: {url}')

    watch_url = url if url.rstrip('/').endswith('/watch') else url.rstrip('/') + '/watch'

    html = utils.getHtml(watch_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    hoster_manager = get_hoster_manager()

    # <ul id="watch"><li data-watch="EMBED_URL"><span>N</span>سيرفر N ...
    servers = re.findall(r'<li[^>]*data-watch="([^"]+)"[^>]*>\s*<span>\d+</span>\s*([^<]+?)\s*<',
                         html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(servers)} servers')

    for embed_url, server_name in servers:
        embed_url = embed_url.strip()
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        server_name = server_name.strip() or 'Server'

        label, should_skip = utils.format_resolver_link(
            hoster_manager, embed_url, site.title, name, quality=server_name)

        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)

    if not servers:
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
