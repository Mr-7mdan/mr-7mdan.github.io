# -*- coding: utf-8 -*-
"""
FajerShow Site Module - fajer.show (updated from show.alfajertv.com)
"""

import re
from resources.lib import utils
from resources.lib.basics import addon, addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('fajershow', 'FajerShow', url=None, image='sites/alfajertv.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    site.add_dir('Search', site.url, 'search', get_category_icon('Search'))
    site.add_dir('English Movies', site.url + 'genre/english-movies/', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Arabic Movies', site.url + 'genre/arabic-movies/', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Turkish Movies', site.url + 'genre/turkish-movies/', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Indian Movies', site.url + 'genre/indian-movies/', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Cartoon Movies', site.url + 'genre/animation/', 'getMovies', get_category_icon('Cartoon Movies'))
    site.add_dir('English TV Shows', site.url + 'genre/english-series/', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + 'genre/arabic-series/', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + 'genre/turkish-series/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Indian TV Shows', site.url + 'genre/indian-series/', 'getTVShows', get_category_icon('Indian TV Shows'))
    site.add_dir('Theater', site.url + 'genre/plays/', 'getMovies', get_category_icon('Theater'))
    utils.eod()


def _listing_pattern(html):
    """Extract items from .item-card listing pages"""
    pattern = r'<a href="(https://fajer\.show/[^"]+)" class="item-card">\s*<div class="card-poster">\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>.*?<h3>([^<]+)</h3>\s*<span class="year-badge">([^<]*)</span>'
    return re.findall(pattern, html, re.DOTALL)


def _hi_res(img):
    return re.sub(r'-\d+x\d+\.', '.', img)


@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        url = site.url + '?s=' + search_text.replace(' ', '+')
        searchResults(url)


@site.register()
def searchResults(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod()
        return

    matches = _listing_pattern(html)
    utils.kodilog('FajerShow Search: Found {} results'.format(len(matches)))

    for item_url, img, alt_title, title, year in matches:
        img = _hi_res(img)
        if '/movies/' in item_url:
            site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='movie')
        else:
            site.add_dir(title, item_url, 'getSeasons', img, fanart=img, year=year, media_type='tvshow')

    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'searchResults', addon_image(site.img_next))

    utils.eod()


@site.register()
def getMovies(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod()
        return

    matches = _listing_pattern(html)
    utils.kodilog('FajerShow getMovies: Found {} items from {}'.format(len(matches), url))

    for item_url, img, alt_title, title, year in matches:
        img = _hi_res(img)
        site.add_dir(title, item_url, 'getLinks', img, fanart=img, year=year, media_type='movie')

    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getMovies', addon_image(site.img_next))

    utils.eod()


@site.register()
def getTVShows(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod()
        return

    matches = _listing_pattern(html)
    utils.kodilog('FajerShow getTVShows: Found {} items from {}'.format(len(matches), url))

    for item_url, img, alt_title, title, year in matches:
        img = _hi_res(img)
        site.add_dir(title, item_url, 'getSeasons', img, fanart=img, year=year, media_type='tvshow')

    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getTVShows', addon_image(site.img_next))

    utils.eod()


@site.register()
def getSeasons(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod()
        return

    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None

    year = None
    year_match = re.search(r'<span[^>]*class="[^"]*year[^"]*"[^>]*>(\d{4})<', html)
    if year_match:
        year = year_match.group(1)

    # Episodes are embedded directly in the HTML as .episode-card elements
    # Format: <span class="episode-number">SxE</span>
    ep_pattern = r'<a href="(https://fajer\.show/episodes/[^"]+)" class="episode-card">.*?<img src="([^"]+)".*?<span class="episode-number">(\d+)x(\d+)</span>.*?<h4>([^<]+)</h4>'
    episodes = re.findall(ep_pattern, html, re.DOTALL)

    utils.kodilog('FajerShow getSeasons: Found {} episodes for {}'.format(len(episodes), show_title))

    for ep_url, ep_img, season_num, ep_num, ep_title in episodes:
        ep_img = _hi_res(ep_img)
        display_title = utils.cleantext(ep_title)
        site.add_dir(display_title, ep_url, 'getLinks', ep_img, fanart=ep_img,
                    season=int(season_num), episode=int(ep_num),
                    show_title=show_title, year=year, media_type='episode')

    utils.eod()


@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    if not html:
        utils.eod()
        return

    utils.kodilog('FajerShow getLinks: Extracting from {}'.format(url))

    post_id_match = re.search(r'var postId = (\d+)', html)
    post_type_match = re.search(r"var postType = '([^']+)'", html)

    if not post_id_match:
        utils.kodilog('FajerShow getLinks: No postId found in page')
        utils.eod()
        return

    post_id = post_id_match.group(1)
    post_type = post_type_match.group(1) if post_type_match else 'movie'
    ajax_url = site.url + 'wp-admin/admin-ajax.php'

    utils.kodilog('FajerShow getLinks: postId={}, postType={}'.format(post_id, post_type))

    hoster_manager = get_hoster_manager()
    headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': url,
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'fajer.show',
    }

    found_links = False
    for num in range(1, 8):
        post_data = {
            'action': 'doo_player_ajax',
            'post': post_id,
            'type': post_type,
            'nume': str(num),
        }

        ajax_response = utils.postHtml(ajax_url, post_data, headers)

        if not ajax_response or len(ajax_response) < 10:
            break

        iframe_url = None
        iframe_match = re.search(r'<iframe[^>]+src=["\']([^"\']+)["\']', ajax_response, re.IGNORECASE)
        if iframe_match:
            iframe_url = iframe_match.group(1)
        else:
            escaped_match = re.search(r'src=\\"([^\\]+)\\"', ajax_response)
            if escaped_match:
                iframe_url = escaped_match.group(1).replace('\\/', '/')

        if not iframe_url:
            continue

        utils.kodilog('FajerShow getLinks: Server {}: {}'.format(num, iframe_url[:100]))

        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            iframe_url,
            'FajerShow',
            name if name else 'Video'
        )

        if should_skip:
            utils.kodilog('FajerShow getLinks: Filtered: {}'.format(iframe_url[:80]))
            continue

        site.add_download_link(label, iframe_url, 'PlayVid', site.image, desc=name,
                              fanart=site.image, landscape=site.image)
        found_links = True

    if not found_links:
        utils.kodilog('FajerShow getLinks: No links found for postId={}'.format(post_id))

    utils.eod()


@site.register()
def PlayVid(url, name=''):
    hoster_manager = get_hoster_manager()
    utils.kodilog('FajerShow PlayVid: Resolving {}'.format(url[:100]))

    result = hoster_manager.resolve(url, referer=site.url)

    if result:
        video_url = result['url']
        utils.kodilog('FajerShow PlayVid: Resolved to {}'.format(video_url[:100]))
    else:
        utils.kodilog('FajerShow PlayVid: No resolver, trying direct playback')
        video_url = url

    utils.playvid(video_url, name, site.image)
