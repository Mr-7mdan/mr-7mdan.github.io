# -*- coding: utf-8 -*-
"""
Daktna TV Site Module - video.daktna.tv
"""

import re
from resources.lib import utils
from resources.lib.basics import addon_image, aksvicon
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('daktna', 'Daktna', url=None, image='sites/daktna.png')

_HEADERS = {'User-Agent': utils.USER_AGENT}

# Pattern for listing items on category pages
_LISTING_PAT = r'<a href="(https://video\.daktna\.tv/watch\.php\?vid=[^"]+)" title="([^"]+)"[^>]*>.*?data-echo="([^"]+)"'

# Items per page (used for next-page detection)
_PAGE_SIZE = 16


def _clean_title(title):
    """Remove Arabic junk words from title"""
    title = re.sub(r'مشاهدة|مسلسل|انمي|مترجمة|مترجم\s+للعربية|مترجم|مدبلجة|مدبلج|كاملة|كامل|اون\s+لاين|HD', '', title)
    title = re.sub(r'\s+-\s*$|\s*-\s*$', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title


def _strip_episode(title):
    """Strip episode suffix: 'Show S3 الحلقة 10' → 'Show S3'"""
    return re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()


def _parse_listing(html):
    """Return [(url, title, img), ...] from a category/listing page"""
    return re.findall(_LISTING_PAT, html, re.DOTALL)


def _next_page_url(current_url, raw_count):
    """Return the next page URL if there may be more items, else None"""
    if raw_count < _PAGE_SIZE:
        return None
    # Remove any existing &sortby=... and &page=... params
    base = re.sub(r'&(?:page|sortby)=[^&]*', '', current_url)
    page_match = re.search(r'[?&]page=(\d+)', current_url)
    next_page = (int(page_match.group(1)) + 1) if page_match else 2
    return f'{base}&page={next_page}&sortby=date'


def _find_show_category(show_title):
    """
    Fetch category.php (all shows) and find the slug whose label
    contains show_title.  Returns full URL or None.
    """
    if not show_title:
        return None
    html = utils.getHtml(site.url + '/category.php', headers=_HEADERS, site_name=site.name)
    if not html:
        return None
    cat_links = re.findall(r'href="([^"]*category\.php\?cat=[^"&]+)"[^>]*>([^<]{3,80})<', html)
    for url, label in cat_links:
        # Skip aggregate pages
        if url.endswith(('turkish-series', 'arabic-series', 'mexican-dubbing-series',
                          'foreign-films', 'arabic-movies')):
            continue
        clean_label = re.sub(r'مسلسل|مترجم|مدبلج|كامل|للعربية|HD|\s+', ' ', label).strip()
        if show_title in clean_label:
            return url
    return None


@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon
    site.add_dir('Turkish TV Shows', site.url + '/category.php?cat=turkish-series', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + '/category.php?cat=arabic-series', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Dubbed TV Shows', site.url + '/category.php?cat=mexican-dubbing-series', 'getTVShows', get_category_icon('Dubbed TV Shows'))
    site.add_dir('Foreign Movies', site.url + '/category.php?cat=foreign-films', 'getMovies', get_category_icon('Movies'))
    site.add_dir('Arabic Movies', site.url + '/category.php?cat=arabic-movies', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    utils.eod()


@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        import urllib.parse
        getTVShows(site.url + '/search.php?q=' + urllib.parse.quote(search_text))


@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    html = utils.getHtml(url, headers=_HEADERS, site_name=site.name)
    if not html:
        utils.eod(content='movies')
        return

    matches = _parse_listing(html)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    for item_url, title, img in matches:
        clean = _clean_title(title)
        if not clean:
            continue
        year = None
        ym = re.search(r'(\d{4})', clean)
        if ym:
            year = ym.group(1)
        site.add_dir(clean, item_url, 'getLinks', img, year=year, media_type='movie')

    next_url = _next_page_url(url, len(matches))
    if next_url:
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    """Get TV shows listing — strips episode suffix and deduplicates"""
    utils.kodilog(f'{site.title}: Getting TV shows from: {url}')
    html = utils.getHtml(url, headers=_HEADERS, site_name=site.name)
    if not html:
        utils.eod(content='tvshows')
        return

    matches = _parse_listing(html)
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')

    seen_titles = set()

    for item_url, title, img in matches:
        clean = _clean_title(title)
        if not clean:
            continue

        show_title = _strip_episode(clean)
        show_title = re.sub(r'\s+', ' ', show_title).strip()

        if not show_title or show_title in seen_titles:
            continue
        seen_titles.add(show_title)

        site.add_dir(show_title, item_url, 'getEpisodes', img, media_type='tvshow')

    utils.kodilog(f'{site.title}: Deduplicated to {len(seen_titles)} shows')

    next_url = _next_page_url(url, len(matches))
    if next_url:
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getEpisodes(url):
    """
    Get episodes for a show.
    url = watch.php?vid=XXXX (first episode from category listing).
    Looks up the show's dedicated category page, then lists all episodes.
    """
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')

    html = utils.getHtml(url, headers=_HEADERS, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    # Extract show title from page title
    title_match = re.search(r'<title>([^<]+)</title>', html)
    if not title_match:
        utils.eod(content='episodes')
        return

    raw_title = title_match.group(1).replace(' - دكتنا TV', '').strip()
    show_title = _strip_episode(_clean_title(raw_title))
    utils.kodilog(f'{site.title}: Show title: "{show_title}"')

    # Try to find the show's dedicated category page
    category_url = _find_show_category(show_title)

    if category_url:
        utils.kodilog(f'{site.title}: Found show category: {category_url}')
        html = utils.getHtml(category_url, headers=_HEADERS, site_name=site.name)
        if not html:
            utils.eod(content='episodes')
            return
    else:
        utils.kodilog(f'{site.title}: No dedicated category for "{show_title}", listing available episodes')
        category_url = None

    matches = _parse_listing(html)
    utils.kodilog(f'{site.title}: Found {len(matches)} episode items')

    seen_eps = set()
    for ep_url, ep_title, ep_img in matches:
        clean_ep = _clean_title(ep_title)
        if not clean_ep or clean_ep in seen_eps:
            continue
        seen_eps.add(clean_ep)

        ep_num = None
        ep_match = re.search(r'(?:الحلقة|حلقة)\s*(\d+)', ep_title)
        if ep_match:
            ep_num = ep_match.group(1)

        site.add_dir(clean_ep, ep_url, 'getLinks', ep_img,
                     episode=ep_num, show_title=show_title, media_type='episode')

    if category_url:
        next_url = _next_page_url(category_url, len(matches))
        if next_url:
            site.add_dir('Next Page', next_url, 'getEpisodes', addon_image(site.img_next))

    utils.eod(content='episodes')


@site.register()
def getLinks(url):
    """Extract embed URL from watch page and offer for playback"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')

    html = utils.getHtml(url, headers=_HEADERS, site_name=site.name)
    if not html:
        utils.notify('Daktna', 'Failed to load page', icon=site.image)
        utils.eod(content='videos')
        return

    # Extract the iframe embed URL
    embed_match = re.search(r'<iframe[^>]+src="(https://video\.daktna\.tv/embed\.php\?vid=[^"]+)"', html)
    if not embed_match:
        utils.notify('Daktna', 'No video source found', icon=site.image)
        utils.eod(content='videos')
        return

    embed_url = embed_match.group(1)
    utils.kodilog(f'{site.title}: Embed URL: {embed_url}')

    title_match = re.search(r'<title>([^<]+)</title>', html)
    title = _clean_title(title_match.group(1).replace(' - دكتنا TV', '').strip()) if title_match else 'Video'

    hoster_manager = get_hoster_manager()
    label, should_skip = utils.format_resolver_link(hoster_manager, embed_url, 'Daktna', title)

    if not should_skip:
        site.add_download_link(label, embed_url, 'PlayVid', site.image,
                               desc=title, fanart=site.image, landscape=site.image)
    else:
        site.add_download_link('Daktna Player', embed_url, 'PlayVid', site.image, desc=title)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    hoster_manager = get_hoster_manager()
    utils.kodilog(f'{site.title}: Resolving: {url[:100]}')

    result = hoster_manager.resolve(url, referer=site.url)
    if result:
        video_url = result['url']
        utils.kodilog(f'{site.title}: Resolved to: {video_url[:100]}')
    else:
        utils.kodilog(f'{site.title}: No resolver, trying direct playback')
        video_url = url

    utils.playvid(video_url, name, site.image)
