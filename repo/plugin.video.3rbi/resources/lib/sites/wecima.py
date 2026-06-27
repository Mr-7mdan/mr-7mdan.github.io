# -*- coding: utf-8 -*-
"""
WeCima Site Module
https://wecima.gold/
WordPress-based Arabic movies/series site (GridItem / Thumb markup).
"""

import re
import base64
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('wecima', 'WeCima', url=None, image='sites/wecima.png')

# Listing card: <div class="GridItem"> ... <a href="URL"> ... url(IMG) ... <strong ...>TITLE</strong>
LIST_PATTERN = r'<div class="GridItem">.*?<a href="([^"]+)"[^>]*>.*?url\(([^)]+)\).*?<strong[^>]*>(.*?)</strong>'
NEXT_PATTERN = r'<a class="next page-numbers" href="([^"]+)"'


@site.register(default_mode=True)
def Main():
    """Main menu - canonical English category labels (verified live)."""
    from resources.lib.category_mapper import get_category_icon

    # Movies
    site.add_dir('English Movies', site.url + '/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a/', 'getMovies', get_category_icon('English Movies') or site.image)
    site.add_dir('Arabic Movies', site.url + '/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%b9%d8%b1%d8%a8%d9%8a/', 'getMovies', get_category_icon('Arabic Movies') or site.image)
    site.add_dir('Indian Movies', site.url + '/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d9%87%d9%86%d8%af%d9%8a/', 'getMovies', get_category_icon('Indian Movies') or site.image)
    site.add_dir('Asian Movies', site.url + '/category/%d8%a7%d9%81%d9%84%d8%a7%d9%85-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a%d8%a9/', 'getMovies', get_category_icon('Asian Movies') or site.image)

    # TV Shows
    site.add_dir('English TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a7%d8%ac%d9%86%d8%a8%d9%8a/', 'getTVShows', get_category_icon('English TV Shows') or site.image)
    site.add_dir('Arabic TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b9%d8%b1%d8%a8%d9%8a%d8%a9/', 'getTVShows', get_category_icon('Arabic TV Shows') or site.image)
    site.add_dir('Turkish TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%aa%d8%b1%d9%83%d9%8a%d8%a9/', 'getTVShows', get_category_icon('Turkish TV Shows') or site.image)
    site.add_dir('Indian TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d9%87%d9%86%d8%af%d9%8a%d8%a9/', 'getTVShows', get_category_icon('Indian TV Shows') or site.image)
    site.add_dir('Asian TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%a7%d8%b3%d9%8a%d9%88%d9%8a%d8%a9/', 'getTVShows', get_category_icon('Asian TV Shows') or site.image)
    site.add_dir('Ramadan TV Shows', site.url + '/category/%d9%85%d8%b3%d9%84%d8%b3%d9%84%d8%a7%d8%aa-%d8%b1%d9%85%d8%b6%d8%a7%d9%86-2025/', 'getTVShows', get_category_icon('Ramadan TV Shows') or site.image)

    # Search
    site.add_dir('Search', '', 'search', get_category_icon('Search') or site.image)

    utils.eod()


def _clean_title(raw):
    """Strip the year <span>, any tags, and Arabic/English stopwords."""
    title = re.sub(r'<span[^>]*class="year"[^>]*>.*?</span>', '', raw, flags=re.DOTALL)
    title = re.sub(r'<[^>]+>', '', title)
    title = re.sub(r'مشاهدة|فيلم|مسلسل|انمي|اون لاين|أون لاين|مترجمة|مترجم|مدبلجة|مدبلج|كاملة|كامل|HD', '', title)
    return re.sub(r'\s+', ' ', title).strip()


def _full_image(img):
    return re.sub(r'-\d+x\d+', '', img.strip())


def _convert_seasons(title):
    repl = [
        ('الموسم الخامس عشر', 'S15'), ('الموسم الرابع عشر', 'S14'),
        ('الموسم الثالث عشر', 'S13'), ('الموسم الثاني عشر', 'S12'),
        ('الموسم الحادي عشر', 'S11'), ('الموسم العاشر', 'S10'),
        ('الموسم التاسع', 'S9'), ('الموسم الثامن', 'S8'),
        ('الموسم السابع', 'S7'), ('الموسم السادس', 'S6'),
        ('الموسم الخامس', 'S5'), ('الموسم الرابع', 'S4'),
        ('الموسم الثالث', 'S3'), ('الموسم الثاني', 'S2'),
        ('الموسم الأول', 'S1'), ('الموسم الاول', 'S1'),
    ]
    for ar, en in repl:
        title = title.replace(ar, en)
    return title


@site.register()
def search():
    """Search for content. WeCima uses /search/<query>/ (GridItem markup)."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='movies')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    search_url = site.url + '/search/' + urllib_parse.quote(search_text) + '/'

    html = utils.getHtml(search_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='movies')
        return

    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} search results')

    for item_url, image, raw_title in matches:
        is_series = ('مسلسل' in raw_title) or ('حلقة' in raw_title) or ('انمي' in raw_title)
        title = _convert_seasons(raw_title)
        title = _clean_title(title)
        # Strip episode suffix for series so the show groups
        if is_series:
            title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
        year = ''
        ym = re.search(r'(\d{4})', raw_title)
        if ym:
            year = ym.group(1)
            title = title.replace(year, '').strip()
        if not title:
            continue
        image = _full_image(image)
        if is_series:
            site.add_dir(title, item_url, 'getEpisodes', image, year=year, media_type='tvshow', keyword=image)
        else:
            site.add_dir(title, item_url, 'getLinks', image, year=year, media_type='movie')

    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1).rstrip('/'), 'search_page', addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def search_page(url):
    """Paginated search results (same markup as getMovies, mixed routing)."""
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='movies')
        return
    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    for item_url, image, raw_title in matches:
        is_series = ('مسلسل' in raw_title) or ('حلقة' in raw_title) or ('انمي' in raw_title)
        title = _clean_title(_convert_seasons(raw_title))
        if is_series:
            title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
        year = ''
        ym = re.search(r'(\d{4})', raw_title)
        if ym:
            year = ym.group(1)
            title = title.replace(year, '').strip()
        if not title:
            continue
        image = _full_image(image)
        if is_series:
            site.add_dir(title, item_url, 'getEpisodes', image, year=year, media_type='tvshow', keyword=image)
        else:
            site.add_dir(title, item_url, 'getLinks', image, year=year, media_type='movie')
    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1).rstrip('/'), 'search_page', addon_image(site.img_next))
    utils.eod(content='movies')


@site.register()
def getMovies(url):
    """Get movies listing."""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='movies')
        return

    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} movies')

    for movie_url, image, raw_title in matches:
        title = _clean_title(raw_title)
        year = ''
        ym = re.search(r'(\d{4})', raw_title)
        if ym:
            year = ym.group(1)
            title = title.replace(year, '').strip()
        if not title:
            continue
        site.add_dir(title, movie_url, 'getLinks', _full_image(image), year=year, media_type='movie')

    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1).rstrip('/'), 'getMovies', addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    """Get TV shows listing. Series categories list individual episodes;
    group them by show+season and route to getEpisodes."""
    utils.kodilog(f'{site.title}: Getting series from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return

    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')

    # Dedup by show title (after converting season words, stripping episode no.)
    show_data = {}
    for series_url, image, raw_title in matches:
        title = _convert_seasons(raw_title)
        title = _clean_title(title)
        year = ''
        ym = re.search(r'(\d{4})', raw_title)
        if ym:
            year = ym.group(1)
            title = title.replace(year, '').strip()
        # Strip "الحلقة N" / "حلقة N" suffix to get the show key
        show_title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
        show_title = re.sub(r'\s+', ' ', show_title).strip()
        if not show_title:
            continue
        if show_title not in show_data:
            show_data[show_title] = (series_url, _full_image(image), year)

    utils.kodilog(f'{site.title}: Deduplicated to {len(show_data)} shows')

    for show_title, (show_url, show_image, show_year) in show_data.items():
        site.add_dir(show_title, show_url, 'getEpisodes', show_image,
                     year=show_year, media_type='tvshow', keyword=show_image)

    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1).rstrip('/'), 'getTVShows', addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getEpisodes(url, name='', keyword=''):
    """Get episodes for a show/season. The episode page carries the full
    EpisodesList inline (Pattern B). `keyword` carries the show poster so
    episodes use the show's image instead of the site logo."""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    # Episodes live in EpisodesList: <a href="URL" class="hoverable activable"> ... <episodetitle>الحلقة N</episodetitle>
    ep_pattern = r'href="([^"]+)"[^>]*class="hoverable activable">\s*<div class="Thumb">.*?<episodetitle>([^<]+)</episodetitle>'
    episodes = re.findall(ep_pattern, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')

    if not episodes:
        # No episode list -> treat the page itself as a watch page
        getLinks(url, name)
        return

    seen = set()
    for ep_url, ep_title in episodes:
        ep_url = ep_url.strip()
        if ep_url in seen:
            continue
        seen.add(ep_url)
        ep_title = re.sub(r'\s+', ' ', ep_title).strip()
        ep_num = ''
        em = re.search(r'(\d+)', ep_title)
        if em:
            ep_num = em.group(1)
        label = f'{name} - {ep_title}' if name else ep_title
        ep_poster = keyword or site.image
        site.add_dir(label, ep_url, 'getLinks', ep_poster, episode=ep_num,
                     media_type='episode', fanart=(keyword or None), landscape=(keyword or None))

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract video links. Servers are <li data-watch="URL">; many URLs are a
    redirector with a base64 'mycimafsd' param that decodes to the real embed."""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    hoster_manager = get_hoster_manager()

    servers = re.findall(r'<li[^>]+data-watch="([^"]+)"', html)
    utils.kodilog(f'{site.title}: Found {len(servers)} servers')

    added = 0
    seen = set()
    for i, server_url in enumerate(servers, 1):
        server_url = server_url.strip()
        # Decode the embedded real link if present
        m = re.search(r'mycimafsd=([^&]+)', server_url)
        if m:
            try:
                decoded = base64.b64decode(m.group(1) + '===').decode('utf-8', 'ignore')
                if decoded.startswith('http'):
                    server_url = decoded
            except Exception:
                pass
        if server_url.startswith('//'):
            server_url = 'https:' + server_url
        if not server_url.startswith('http') or server_url in seen:
            continue
        seen.add(server_url)

        label, should_skip = utils.format_resolver_link(
            hoster_manager, server_url, site.title, name, quality=f'Server {i}')
        if not should_skip:
            basics.addDownLink(label, server_url, f'{site.name}.PlayVid', site.image)
            added += 1

    if not added:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video."""
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
