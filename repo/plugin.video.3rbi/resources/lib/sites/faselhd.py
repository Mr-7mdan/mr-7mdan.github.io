# -*- coding: utf-8 -*-
"""
FaselHD Site Module
https://faselhd.club/
"""

import re
from urllib.parse import urlparse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('faselhd', 'FaselHD', url=None, image='sites/faselhd.png')


def _clean_title(title):
    title = utils.cleantext(title)
    for word in ['مشاهدة', 'تحميل', 'فيلم', 'مسلسل', 'انمي', 'انمى', 'مترجم', 'مترجمة',
                 'مدبلج للعربية', 'مدبلج', 'اونلاين', 'اون لاين', 'كامل', 'كاملة',
                 'حلقات كاملة', 'جودة عالية', 'HD', 'مباشرة', 'والأخيرة', 'والاخيرة',
                 'برنامج', 'السلسلة الوثائقية', 'الفيلم الوثائقي']:
        title = title.replace(word, '')
    year = None
    year_match = re.search(r'(\d{4})', title)
    if year_match:
        year = year_match.group(1)
        title = title.replace(year, '')
    title = re.sub(r'\s+', ' ', title).strip(' -|:')
    return title, year


def _hi_res(img):
    return re.sub(r'-\d+x\d+\.', '.', img)


def _parse_listing(html):
    pattern = r'<div class="postDiv\s*">\s*<a href="(https?://[^"]+)".*?data-src="([^"?]+).*?<div class="h1">([^<]+)</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    results = []
    for item_url, img, raw_title in matches:
        title, year = _clean_title(raw_title)
        results.append((item_url, _hi_res(img), title, year))
    return results


def _get_next_page(html):
    m = re.search(r"href='([^']+)'>&rsaquo;</a>", html)
    if m:
        return m.group(1)
    m2 = re.search(r'href="([^"]+/page/\d+[^"]*)"', html)
    if m2:
        return m2.group(1)
    return None


def _get_og_meta(html):
    title, year = None, None
    og_t = re.search(r'property="og:title"\s+content="([^"]+)"', html)
    if og_t:
        title, year = _clean_title(og_t.group(1))
    img = None
    og_i = re.search(r'property="og:image"\s+content="([^"]+)"', html)
    if og_i:
        img = og_i.group(1)
    return title, year, img


@site.register(default_mode=True)
def Main():
    site.add_dir('Movies', site.url + '/movies', 'getMovieCategories', get_category_icon('Movies'))
    site.add_dir('TV Shows', site.url + '/series', 'getSeriesCategories', get_category_icon('TV Shows'))
    site.add_dir('TV Programs', site.url + '/tvshows', 'getTVShows', get_category_icon('TV Programs'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    utils.eod()


@site.register()
def getMovieCategories(url):
    base = site.url
    site.add_dir('Movies', base + '/all-movies', 'getMovies', get_category_icon('Movies'))
    site.add_dir('English Movies', base + '/movies', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Dubbed Movies', base + '/dubbed-movies', 'getMovies', get_category_icon('Dubbed Movies'))
    site.add_dir('Indian Movies', base + '/hindi', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Asian Movies', base + '/asian-movies', 'getMovies', get_category_icon('Asian Movies'))
    site.add_dir('Anime Movies', base + '/anime-movies', 'getMovies', get_category_icon('Anime Movies'))
    site.add_dir('Top Voted Movies', base + '/movies_top_votes', 'getMovies', get_category_icon('Movies'))
    site.add_dir('Most Viewed Movies', base + '/movies_top_views', 'getMovies', get_category_icon('Movies'))
    site.add_dir('Top IMDB Movies', base + '/movies_top_imdb', 'getMovies', get_category_icon('Movies'))
    site.add_dir('Movie Collections', base + '/movies_collections', 'getMovies', get_category_icon('Movies'))
    utils.eod(content='movies')


@site.register()
def getSeriesCategories(url):
    base = site.url
    site.add_dir('TV Shows', base + '/series', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Asian TV Shows', base + '/asian-series', 'getTVShows', get_category_icon('Asian TV Shows'))
    site.add_dir('Short TV Shows', base + '/short_series', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Most Viewed TV Shows', base + '/series_top_views', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Top IMDB TV Shows', base + '/series_top_imdb', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Recently Added', base + '/episodes', 'getRecentEpisodes', get_category_icon('Recently Added'))
    site.add_dir('Anime TV Shows', base + '/anime', 'getTVShows', get_category_icon('TV Shows'))
    utils.eod(content='tvshows')


@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        url = site.url + '/?s=' + search_text.replace(' ', '+')
        searchResults(url)


@site.register()
def searchResults(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='movies')
        return

    items = _parse_listing(html)
    utils.kodilog('FaselHD search: Found {} items'.format(len(items)))

    for item_url, img, title, year in items:
        if not title:
            continue
        if '/series/' in item_url:
            site.add_dir(title, item_url, 'getSeasons', img, fanart=img, year=year, media_type='tvshow')
        elif '/seasons/' in item_url:
            site.add_dir(title, item_url, 'getEpisodes', img, fanart=img, year=year, media_type='tvshow')
        elif '/episodes/' in item_url:
            site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='episode')
        else:
            site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='movie')

    next_url = _get_next_page(html)
    if next_url:
        site.add_dir('Next Page', next_url, 'searchResults', addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def getMovies(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='movies')
        return

    items = _parse_listing(html)
    utils.kodilog('FaselHD getMovies: Found {} items from {}'.format(len(items), url))

    for item_url, img, title, year in items:
        if not title:
            continue
        site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='movie')

    next_url = _get_next_page(html)
    if next_url:
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='tvshows')
        return

    items = _parse_listing(html)
    utils.kodilog('FaselHD getTVShows: Found {} items from {}'.format(len(items), url))

    for item_url, img, title, year in items:
        if not title:
            continue
        if '/seasons/' in item_url:
            site.add_dir(title, item_url, 'getEpisodes', img, fanart=img, year=year, media_type='tvshow')
        elif '/episodes/' in item_url:
            site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='episode')
        else:
            site.add_dir(title, item_url, 'getSeasons', img, fanart=img, year=year, media_type='tvshow')

    next_url = _get_next_page(html)
    if next_url:
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getRecentEpisodes(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    items = _parse_listing(html)
    utils.kodilog('FaselHD getRecentEpisodes: Found {} items from {}'.format(len(items), url))

    for item_url, img, title, year in items:
        if not title:
            continue
        site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='episode')

    next_url = _get_next_page(html)
    if next_url:
        site.add_dir('Next Page', next_url, 'getRecentEpisodes', addon_image(site.img_next))

    utils.eod(content='episodes')


@site.register()
def getSeasons(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod(content='seasons')
        return

    parsed = urlparse(url)
    base = '{}://{}'.format(parsed.scheme, parsed.netloc)

    show_title, _, thumb = _get_og_meta(html)

    season_pattern = r'<div class="seasonDiv[^"]*"[^>]*onclick="window\.location\.href\s*=\s*\'([^\']+)\'".*?data-src="([^"?]+).*?<div class="title">([^<]+)</div>'
    seasons = re.findall(season_pattern, html, re.DOTALL)

    utils.kodilog('FaselHD getSeasons: Found {} seasons for {}'.format(len(seasons), url))

    if seasons:
        for s_url, s_img, s_title in seasons:
            if s_url.startswith('/'):
                s_url = base + s_url
            s_img = _hi_res(s_img)
            s_title_clean = s_title.strip()
            season_num = None
            snum = re.search(r'(\d+)', s_title)
            if snum:
                season_num = int(snum.group(1))
            site.add_dir(s_title_clean, s_url, 'getEpisodes', s_img or thumb or site.image,
                        fanart=s_img or thumb, season=season_num,
                        show_title=show_title, media_type='season')
        utils.eod(content='seasons')
    else:
        getEpisodes(url)


@site.register()
def getEpisodes(url, show_title=None, show_img=None):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod(content='episodes')
        return

    if not show_title:
        show_title, _, og_img = _get_og_meta(html)
        if not show_img:
            show_img = og_img

    season_num = None
    snum = re.search(r'(?:موسم|season)[^\d]*(\d+)', url, re.IGNORECASE)
    if snum:
        season_num = int(snum.group(1))

    ep_block_match = re.search(r'id="epAll"(.*?)</div>', html, re.DOTALL)
    if ep_block_match:
        eps = re.findall(r'<a href="([^"]+)"[^>]*>\s*([^<]+?)\s*</a>', ep_block_match.group(1))
        utils.kodilog('FaselHD getEpisodes: Found {} episodes'.format(len(eps)))

        for ep_url, ep_title in eps:
            ep_title = ep_title.strip()
            ep_num = None
            enum = re.search(r'(\d+)', ep_title)
            if enum:
                ep_num = int(enum.group(1))
            display = '{} - {}'.format(show_title, ep_title) if show_title else ep_title
            site.add_dir(display, ep_url, 'getLinks', show_img or site.image,
                        fanart=show_img, episode=ep_num, season=season_num,
                        show_title=show_title, media_type='episode')
    else:
        utils.kodilog('FaselHD getEpisodes: No epAll block at {}'.format(url))

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod(content='videos')
        return

    utils.kodilog('FaselHD getLinks: Extracting from {}'.format(url))
    hoster_manager = get_hoster_manager()
    found = False

    # --- Watch links ---
    watch_urls = re.findall(r"player_iframe\.location\.href\s*=\s*'(https?://[^']+)'", html)
    li_texts = re.findall(r'<li[^>]*onclick=[^>]+>.*?</li>', html, re.DOTALL)
    server_names = [re.sub(r'<[^>]+>', '', li).strip() for li in li_texts]

    utils.kodilog('FaselHD getLinks: {} watch servers'.format(len(watch_urls)))

    for i, w_url in enumerate(watch_urls):
        sname = server_names[i] if i < len(server_names) else 'Server {}'.format(i + 1)
        label, should_skip = utils.format_resolver_link(hoster_manager, w_url, 'FaselHD', name, sname)
        if not should_skip:
            site.add_download_link(label, w_url, 'PlayVid', site.image, desc=name,
                                   quality=sname, fanart=site.image, landscape=site.image)
            found = True

    # --- Download links (after تحميل section) ---
    dl_idx = html.find('تحميل')
    if dl_idx > 0:
        dl_block = html[dl_idx:dl_idx + 3000]
        dl_links = re.findall(r'<a href="(https?://[^"]+)"[^>]*>.*?<span>سيرفر</span>([^<]+)</a>', dl_block, re.DOTALL)
        utils.kodilog('FaselHD getLinks: {} download links'.format(len(dl_links)))
        for d_url, d_name in dl_links:
            d_name = d_name.strip()
            quality = 'تحميل - {}'.format(d_name)
            label, should_skip = utils.format_resolver_link(hoster_manager, d_url, 'FaselHD', name, quality)
            if not should_skip:
                site.add_download_link(label, d_url, 'PlayVid', site.image, desc=name,
                                       quality=quality, fanart=site.image, landscape=site.image)
                found = True

    if not found:
        utils.notify('FaselHD', 'No links found', icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    utils.kodilog('FaselHD PlayVid: Resolving {}'.format(url[:100]))
    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)

    if result and result.get('url'):
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(result['url'])
    else:
        utils.notify('FaselHD', 'فشل تشغيل الفيديو', icon=site.image)
