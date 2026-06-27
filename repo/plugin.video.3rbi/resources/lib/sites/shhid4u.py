# -*- coding: utf-8 -*-
"""
Shahid4U Site Module
Live mirror: https://sh4u.cam  (recommended sites.json url)

Site layout (WordPress, custom "shahid4u" theme):
  - Listing cards: <a href=".." title=".." class="recent--block"> ... <img data-src="POSTER">
  - Browse pages : /movies/  /series/  /episodes/  /imdb/
  - Genre filter : /filtering?category=<TERM_ID>   (term ids are stable per genre)
  - Pagination   : /<path>/page/<n>/   and   /filtering/page/<n>/?category=<id>
  - Series page  : season tabs  <a href=".."><span>الموسم</span><em>N</em></a>
                   episode list <a href=".."><span>الحلقة</span><em>N</em></a>
  - Watch page   : <a class="watch" href="..//watch"> -> page with server buttons
  - Servers      : <button class="cwd-server-btn" data-server-url="EMBED">
                     <span class="cwd-server-name">السيرفر N</span>
"""

import re
import html as html_module
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('shhid4u', 'Shahid4U', url=None, image='sites/shhid4u.png')

# --- shared regexes (verified live against sh4u.cam) ------------------------
LIST_RE = re.compile(
    r'<a\s+href="([^"]+)"\s+title="([^"]*)"\s+class="recent--block">(.*?)</a>',
    re.DOTALL)
IMG_RE = re.compile(r'data-src="([^"]+)"')
IMG_FALLBACK_RE = re.compile(r'<img[^>]+src="([^"]+)"')
SEASON_RE = re.compile(
    r'<a[^>]*?\shref="([^"]+)"[^>]*>\s*<span>\s*الموسم\s*</span>\s*<em>\s*([^<]+?)\s*</em>',
    re.DOTALL)
EPISODE_RE = re.compile(
    r'<a[^>]*?\shref="([^"]+)"[^>]*>\s*<span>\s*الحلقة\s*</span>\s*<em>\s*([^<]+?)\s*</em>',
    re.DOTALL)
WATCH_RE = re.compile(r'<a[^>]*class="watch"[^>]*href="([^"]+)"|<a[^>]*href="([^"]+)"[^>]*class="watch"')
SERVER_RE = re.compile(
    r'data-server-url="([^"]+)"[^>]*>\s*<span class="cwd-server-content">.*?'
    r'cwd-server-name">\s*([^<]+?)\s*</span>',
    re.DOTALL)
OG_IMAGE_RE = re.compile(r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"')


def _clean_title(title):
    title = html_module.unescape(title or '').strip()
    title = re.sub(r'^\s*(?:مشاهدة|تحميل)\s+', '', title)
    return title.strip()


def _extract_year(title):
    m = re.search(r'(19|20)\d{2}', title)
    return m.group(0) if m else ''


def _page_url(url, page):
    """Build a /page/N/ URL preserving any query string (filtering / search)."""
    if not page or page <= 1:
        return url
    base, _, query = url.partition('?')
    base = base.rstrip('/')
    return '%s/page/%d/%s' % (base, page, ('?' + query) if query else '')


def _parse_list(html):
    """Return list of (url, clean_title, image) from recent--block cards."""
    items = []
    for item_url, raw_title, body in LIST_RE.findall(html):
        img_m = IMG_RE.search(body) or IMG_FALLBACK_RE.search(body)
        image = img_m.group(1) if img_m else site.image
        items.append((item_url, _clean_title(raw_title), image))
    return items


def _fetch(url):
    return utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon

    utils.kodilog('%s: Main menu' % site.title)
    base = site.url

    def f(term):
        return '%s/filtering?category=%s' % (base, term)

    # Movies
    site.add_dir('All Movies', base + '/movies/', 'getMovies', get_category_icon('Movies'))
    site.add_dir('English Movies', f('27192'), 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Arabic Movies', f('29263'), 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Indian Movies', f('29407'), 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Turkish Movies', f('29419'), 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Asian Movies', f('28051'), 'getMovies', get_category_icon('Asian Movies'))
    site.add_dir('Anime Movies', f('28534'), 'getMovies', get_category_icon('Anime Movies'))
    site.add_dir('Dubbed Movies', f('32665'), 'getMovies', get_category_icon('Dubbed Movies'))
    site.add_dir('Netflix Movies', f('657'), 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Top IMDb', base + '/imdb/', 'getMovies', get_category_icon('Movies'))

    # Series (browse by show -> seasons -> episodes)
    site.add_dir('TV Series (Shows)', base + '/series/', 'getSeries', get_category_icon('English TV Shows'))

    # Episodes (latest + by genre, listed directly)
    site.add_dir('Latest Episodes', base + '/episodes/', 'getEpisodes', get_category_icon('English TV Shows'))
    site.add_dir('English TV Shows', f('27224'), 'getEpisodes', get_category_icon('English TV Shows'))
    site.add_dir('Turkish TV Shows', f('27854'), 'getEpisodes', get_category_icon('Turkish TV Shows'))
    site.add_dir('Korean TV Shows', f('27907'), 'getEpisodes', get_category_icon('Asian TV Shows'))
    site.add_dir('Arabic TV Shows', f('27811'), 'getEpisodes', get_category_icon('Arabic TV Shows'))
    site.add_dir('Indian TV Shows', f('18463'), 'getEpisodes', get_category_icon('Indian TV Shows'))
    site.add_dir('Cartoon TV Shows', f('45'), 'getEpisodes', get_category_icon('Cartoon TV Shows'))
    site.add_dir('Netflix Series', f('27256'), 'getEpisodes', get_category_icon('English TV Shows'))
    site.add_dir('TV Programs', f('164'), 'getEpisodes', get_category_icon('TV Programs'))
    site.add_dir('WWE', f('28879'), 'getEpisodes', get_category_icon('WWE'))

    # Search
    site.add_dir('Search', '', 'search', get_category_icon('Search'))

    utils.eod()


@site.register()
def search():
    """Search for content (mixed movies + episodes + shows)"""
    utils.kodilog('%s: Search' % site.title)

    keyboard = utils.get_keyboard('')
    if keyboard:
        query = keyboard.getText()
        if query:
            search_url = '%s/?s=%s' % (site.url, utils.quote_plus(query))
            getMixed(search_url)
            return
    utils.eod(content='tvshows')


@site.register()
def getMovies(url, page=1):
    """Get movies listing"""
    if page is None:
        page = 1
    fetch_url = _page_url(url, page)
    utils.kodilog('%s: Getting movies from: %s' % (site.title, fetch_url))

    html = _fetch(fetch_url)
    if not html:
        utils.kodilog('%s: No HTML received' % site.title)
        utils.eod(content='movies')
        return

    items = _parse_list(html)
    utils.kodilog('%s: Found %d movies' % (site.title, len(items)))

    for item_url, title, image in items:
        if not title:
            continue
        year = _extract_year(title)
        site.add_dir(title, item_url, 'getLinks', image, year=year, media_type='movie')

    if items:
        site.add_dir('الصفحة التالية', url, 'getMovies',
                     addon_image(site.img_next), page=page + 1)

    utils.eod(content='movies')


@site.register()
def getEpisodes(url, page=1):
    """Get episodes listing (genre/episodes pages list individual episodes)"""
    if page is None:
        page = 1
    fetch_url = _page_url(url, page)
    utils.kodilog('%s: Getting episodes from: %s' % (site.title, fetch_url))

    html = _fetch(fetch_url)
    if not html:
        utils.kodilog('%s: No HTML received' % site.title)
        utils.eod(content='episodes')
        return

    items = _parse_list(html)
    utils.kodilog('%s: Found %d episodes' % (site.title, len(items)))

    for item_url, title, image in items:
        if not title:
            continue
        # A /series/ permalink would be a show, not an episode -> drill down
        if '/series/' in item_url:
            site.add_dir(title, item_url, 'getSeasons', image, media_type='tvshow')
        else:
            site.add_dir(title, item_url, 'getLinks', image, media_type='episode')

    if items:
        site.add_dir('الصفحة التالية', url, 'getEpisodes',
                     addon_image(site.img_next), page=page + 1)

    utils.eod(content='episodes')


@site.register()
def getSeries(url, page=1):
    """Get TV shows listing -> each show drills into seasons/episodes"""
    if page is None:
        page = 1
    fetch_url = _page_url(url, page)
    utils.kodilog('%s: Getting series from: %s' % (site.title, fetch_url))

    html = _fetch(fetch_url)
    if not html:
        utils.kodilog('%s: No HTML received' % site.title)
        utils.eod(content='tvshows')
        return

    items = _parse_list(html)
    utils.kodilog('%s: Found %d shows' % (site.title, len(items)))

    for item_url, title, image in items:
        if not title:
            continue
        year = _extract_year(title)
        site.add_dir(title, item_url, 'getSeasons', image, year=year, media_type='tvshow')

    if items:
        site.add_dir('الصفحة التالية', url, 'getSeries',
                     addon_image(site.img_next), page=page + 1)

    utils.eod(content='tvshows')


@site.register()
def getMixed(url, page=1):
    """List mixed search results, routing each item to the right handler"""
    if page is None:
        page = 1
    fetch_url = _page_url(url, page)
    utils.kodilog('%s: Getting mixed results from: %s' % (site.title, fetch_url))

    html = _fetch(fetch_url)
    if not html:
        utils.kodilog('%s: No HTML received' % site.title)
        utils.eod()
        return

    items = _parse_list(html)
    utils.kodilog('%s: Found %d results' % (site.title, len(items)))

    for item_url, title, image in items:
        if not title:
            continue
        year = _extract_year(title)
        if '/series/' in item_url:
            site.add_dir(title, item_url, 'getSeasons', image, year=year, media_type='tvshow')
        elif 'فيلم' in title or '/movies/' in item_url:
            site.add_dir(title, item_url, 'getLinks', image, year=year, media_type='movie')
        else:
            site.add_dir(title, item_url, 'getLinks', image, media_type='episode')

    if items:
        site.add_dir('الصفحة التالية', url, 'getMixed',
                     addon_image(site.img_next), page=page + 1)

    utils.eod()


@site.register()
def getSeasons(url, name=''):
    """List a show's seasons; if only one season, list its episodes directly"""
    utils.kodilog('%s: Getting seasons from: %s' % (site.title, url))

    html = _fetch(url)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='seasons')
        return

    seasons = []
    seen = set()
    for s_url, s_num in SEASON_RE.findall(html):
        if s_url in seen:
            continue
        seen.add(s_url)
        seasons.append((s_url, s_num.strip()))

    img_m = OG_IMAGE_RE.search(html)
    image = img_m.group(1) if img_m else site.image

    if len(seasons) > 1:
        utils.kodilog('%s: Found %d seasons' % (site.title, len(seasons)))
        for s_url, s_num in seasons:
            label = '%s - الموسم %s' % (name, s_num) if name else 'الموسم %s' % s_num
            site.add_dir(label, s_url, 'getShowEpisodes', image, name=name, media_type='season')
        utils.eod(content='seasons')
    else:
        # Single (or no) season tab -> episodes are on this same page
        getShowEpisodes(url, name)


@site.register()
def getShowEpisodes(url, name=''):
    """List episodes inside a show/season page"""
    utils.kodilog('%s: Getting show episodes from: %s' % (site.title, url))

    html = _fetch(url)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='episodes')
        return

    img_m = OG_IMAGE_RE.search(html)
    image = img_m.group(1) if img_m else site.image

    episodes = []
    seen = set()
    for ep_url, ep_num in EPISODE_RE.findall(html):
        if ep_url in seen:
            continue
        seen.add(ep_url)
        episodes.append((ep_url, ep_num.strip()))

    utils.kodilog('%s: Found %d episodes' % (site.title, len(episodes)))

    for ep_url, ep_num in episodes:
        title = '%s - الحلقة %s' % (name, ep_num) if name else 'الحلقة %s' % ep_num
        site.add_dir(title, ep_url, 'getLinks', image, media_type='episode')

    if not episodes:
        utils.notify(site.title, 'لم يتم العثور على حلقات', icon=site.image)

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract embed/server links from a movie/episode watch page"""
    utils.kodilog('%s: Getting links from: %s' % (site.title, url))

    html = _fetch(url)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    # Find the watch page
    watch_url = ''
    wm = WATCH_RE.search(html)
    if wm:
        watch_url = wm.group(1) or wm.group(2)
    if not watch_url:
        watch_url = url.rstrip('/') + '/watch'
    if watch_url.startswith('/'):
        watch_url = site.url + watch_url

    utils.kodilog('%s: Watch URL: %s' % (site.title, watch_url))

    watch_html = _fetch(watch_url)
    if not watch_html:
        utils.notify(site.title, 'لم يتم تحميل صفحة المشاهدة', icon=site.image)
        utils.eod(content='videos')
        return

    servers = SERVER_RE.findall(watch_html)
    utils.kodilog('%s: Found %d servers' % (site.title, len(servers)))

    hoster_manager = get_hoster_manager()
    added = 0
    for embed_raw, server_name in servers:
        embed_url = html_module.unescape(embed_raw).strip()
        if not embed_url:
            continue
        server_name = html_module.unescape(server_name).strip() or 'Server'

        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            embed_url,
            site.title,
            name,
            quality=server_name
        )

        if not should_skip:
            basics.addDownLink(label, embed_url, '%s.PlayVid' % site.name, site.image)
            added += 1

    if not added:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    utils.kodilog('%s: Resolving URL: %s' % (site.title, url[:100]))

    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)

    if result and result.get('url'):
        video_url = result['url']
        utils.kodilog('%s: Playing: %s' % (site.title, video_url[:100]))

        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'فشل تشغيل الفيديو', icon=site.image)
