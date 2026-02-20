# -*- coding: utf-8 -*-
"""
ArabSeed Site Module
"""

import re
import json
from resources.lib import utils
from resources.lib.basics import addon, addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager, extract_iframe_sources
from six.moves import urllib_parse

site = SiteBase('arabseed', 'ArabSeed', url=None, image='sites/arabseed.png')

def _get_dynamic_url():
    """Extract the dynamic main URL from the site"""
    try:
        html = utils.getHtml(site.url)
        # Look for HomeURL in JavaScript
        match = re.search(r'HomeURL\s*=\s*["\']([^"\']+)["\']', html)
        if match:
            dynamic_url = match.group(1)
            utils.kodilog('ArabSeed: Found dynamic URL: {}'.format(dynamic_url))
            return dynamic_url
    except:
        pass
    # Fallback to main4
    return site.url + 'main4/'

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon
    
    site.add_dir('Search', site.url, 'searchMovies', get_category_icon('Search'))
    site.add_dir('Search', site.url, 'searchSeries', get_category_icon('Search'))
    site.add_dir('Recently Added', site.url + 'recently/', 'getRecent', get_category_icon('Recently Added'))
    site.add_dir('English Movies', site.url + 'category/foreign-movies-10/', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Arabic Movies', site.url + 'category/arabic-movies-10/', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Netflix Movies', site.url + 'category/netfilx/افلام-netfilx/', 'getMovies', get_category_icon('Netflix Movies'))
    site.add_dir('English TV Shows', site.url + 'category/foreign-series-3/', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + 'category/arabic-series-8/', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + 'category/turkish-series-2/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Netflix TV Shows', site.url + 'category/netfilx/مسلسلات-netfilx-1/', 'getTVShows', get_category_icon('Netflix TV Shows'))
    site.add_dir('WWE', site.url + 'category/wwe-shows-1/', 'getTVShows', get_category_icon('WWE'))
    utils.eod()

@site.register()
def searchMovies():
    search_text = utils.get_search_input()
    if search_text:
        _performSearch(search_text, 'movies')

@site.register()
def searchSeries():
    search_text = utils.get_search_input()
    if search_text:
        _performSearch(search_text, 'series')

def _performSearch(search_text, content_type):
    """Perform search using /find__posts/ AJAX endpoint"""
    # Get csrf_token from a category page (token not present on home page)
    token_url = site.url + 'category/foreign-movies-10/'
    html = utils.getHtml(token_url, headers={'User-Agent': utils.USER_AGENT})
    
    # Pattern matches: 'csrf__token': "f76bb2e259" or "csrf__token": "f76bb2e259"
    csrf_match = re.search(r'["\']csrf__token["\']\s*:\s*["\']([a-zA-Z0-9]+)["\']', html)
    csrf_token = csrf_match.group(1) if csrf_match else ''
    
    if not csrf_token:
        utils.kodilog('ArabSeed Search: Failed to extract csrf_token from {}'.format(token_url))
        utils.notify('ArabSeed', 'Search failed - no token')
        utils.eod(content='movies')
        return
    
    # POST to search endpoint
    search_url = site.url + 'find__posts/'
    post_data = {
        'search': search_text,
        'search_type': '',
        'csrf_token': csrf_token
    }
    
    headers = {
        'User-Agent': utils.USER_AGENT,
        'Referer': site.url,
        'X-Requested-With': 'XMLHttpRequest',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    }
    
    try:
        # Debug
        utils.kodilog('ArabSeed Search csrf_token: {}'.format(csrf_token))
        utils.kodilog('ArabSeed Search URL: {}'.format(search_url))
        utils.kodilog('ArabSeed Search data: {}'.format(post_data))
        
        response = utils.postHtml(search_url, post_data, headers)
        
        # Debug response
        utils.kodilog('ArabSeed Search response type: {}'.format(type(response)))
        utils.kodilog('ArabSeed Search response first 200 chars: {}'.format(response[:200] if response else 'EMPTY'))
        
        # Response is JSON with 'type' and 'html' keys
        result = json.loads(response)
        
        utils.kodilog('ArabSeed Search result type: {}'.format(type(result)))
        utils.kodilog('ArabSeed Search result keys: {}'.format(result.keys() if isinstance(result, dict) else 'NOT A DICT'))
        
        if isinstance(result, dict) and 'html' in result:
            # Parse search results HTML - different structure than category listings
            _parseSearchResults(result['html'], content_type)
        else:
            utils.kodilog('ArabSeed Search: Unexpected response format')
    except Exception as e:
        utils.kodilog('ArabSeed Search Error: {}'.format(str(e)))
        import traceback
        utils.kodilog('ArabSeed Search Traceback: {}'.format(traceback.format_exc()))
        utils.notify('ArabSeed', 'Search failed')
    
    utils.eod(content='movies')

def _parseSearchResults(html, content_type):
    """Parse search results HTML - different structure than category listings"""
    # Pattern for search results: <a class="search__item"> with <h3> title and data-src image
    pattern = r'<a href="([^"]+)" class="search__item[^"]*">.*?data-src="([^"]+)".*?<h3>([^<]+)</h3>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for item_url, img, title in entries:
        # Clean title
        clean_title = utils.cleantext(title)
        clean_title = re.sub(r'(مشاهدة|مسلسل|انمي|مترجمة|مترجم|برنامج|فيلم|مدبلج|كاملة|اونلاين|HD)', '', clean_title)
        clean_title = clean_title.strip()
        
        # Extract year from title (format: "Title ( 2025 )")
        year = None
        year_match = re.search(r'\(\s*(\d{4})\s*\)', clean_title)
        if year_match:
            year = year_match.group(1)
            clean_title = re.sub(r'\s*\(\s*\d{4}\s*\)', '', clean_title).strip()
        
        # Determine if it's a series or movie based on URL or title
        is_series = '/series' in item_url or 'مسلسل' in title or content_type == 'series'
        
        if is_series:
            site.add_dir(clean_title, item_url, 'getSeasons', img, fanart=img,
                       year=year, media_type='tvshow', original_title=title)
        else:
            site.add_dir(clean_title, item_url, 'getLinks', img, fanart=img,
                       year=year, media_type='movie', original_title=title)

@site.register()
def getRecent(url):
    html = utils.getHtml(url)
    _parseListings(html, 'mixed')
    utils.eod(content='movies')

@site.register()
def getMovies(url):
    html = utils.getHtml(url)
    _parseListings(html, 'movies')
    
    # Check for pagination - look for rel="next"
    next_match = re.search(r'<link rel="next" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')

@site.register()
def getTVShows(url):
    html = utils.getHtml(url)
    _parseListings(html, 'series')
    
    # Check for pagination - look for rel="next"
    next_match = re.search(r'<link rel="next" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')

def _parseListings(html, content_type):
    """Parse movie/series listings"""
    # Pattern for ArabSeed items - matches both movie__block and movie__block is__episode
    pattern = r'<a href="([^"]+)"[^>]+title="([^"]+)"[^>]*class="movie__block[^"]*"[^>]*>.*?<img[^>]+src="([^"]+)"'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for item_url, title, img in entries:
        # Clean title
        clean_title = utils.cleantext(title)
        clean_title = re.sub(r'(مشاهدة|مسلسل|انمي|مترجمة|مترجم|برنامج|فيلم|مدبلج|كاملة|اونلاين|HD)', '', clean_title)
        clean_title = clean_title.strip()
        
        # Extract year
        year = None
        year_match = re.search(r'(\d{4})', clean_title)
        if year_match:
            year = year_match.group(1)
            clean_title = clean_title.replace(year, '').strip()
        
        # Build display title
        if year:
            display_title = '{} ({})'.format(clean_title, year)
        else:
            display_title = clean_title
        
        # Determine if it's a series or movie based on URL or title
        is_series = '/series' in item_url or 'مسلسل' in title or content_type == 'series'
        
        if is_series:
            site.add_dir(display_title, item_url, 'getSeasons', img, fanart=img,
                       year=year, media_type='tvshow', original_title=title)
        else:
            site.add_dir(display_title, item_url, 'getLinks', img, fanart=img,
                       year=year, media_type='movie', original_title=title)

@site.register()
def getSeasons(url):
    html = utils.getHtml(url)
    if not html:
        utils.eod(content='seasons')
        return
    
    # Extract show info
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None
    if show_title:
        show_title = re.sub(r'(مشاهدة|مسلسل|مترجم)', '', show_title).strip()
    
    # Extract year
    year = None
    if show_title:
        year_match = re.search(r'(\d{4})', show_title)
        if year_match:
            year = year_match.group(1)
            show_title = show_title.replace(year, '').strip()
    
    # Look for seasons - ArabSeed lists seasons with links
    # Pattern: season links or episode listings
    season_pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?(?:الموسم|Season)\s*(\d+)'
    seasons = re.findall(season_pattern, html, re.IGNORECASE)
    
    if seasons:
        # Has explicit seasons
        seen_seasons = set()
        for season_url, season_num in seasons:
            if season_num not in seen_seasons:
                seen_seasons.add(season_num)
                season_title = '{} - الموسم {}'.format(show_title, season_num)
                site.add_dir(season_title, season_url, 'getEpisodes', site.image,
                           season=int(season_num), show_title=show_title, year=year,
                           media_type='season')
    else:
        # No explicit seasons, look for episodes directly
        getEpisodes(url, show_title=show_title, year=year)
        return
    
    utils.eod(content='seasons')

@site.register()
def getEpisodes(url, show_title=None, year=None):
    html = utils.getHtml(url)
    if not html:
        utils.eod(content='episodes')
        return
    
    # Extract show title if not provided
    if not show_title:
        title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
        show_title = utils.cleantext(title_match.group(1)) if title_match else None
        if show_title:
            show_title = re.sub(r'(مشاهدة|مسلسل|مترجم)', '', show_title).strip()
    
    # Extract year if not provided
    if not year and show_title:
        year_match = re.search(r'(\d{4})', show_title)
        if year_match:
            year = year_match.group(1)
            show_title = show_title.replace(year, '').strip()
    
    # Pattern for episodes
    ep_pattern = r'<a[^>]+href="([^"]+)"[^>]*>.*?(?:الحلقة|Episode|حلقة)\s*(\d+)'
    episodes = re.findall(ep_pattern, html, re.IGNORECASE)
    
    if episodes:
        for ep_url, ep_num in episodes:
            episode_num = int(ep_num)
            
            # Try to extract season number from URL or title
            season_num = None
            season_match = re.search(r'(?:الموسم|season)[^\d]*(\d+)', ep_url, re.IGNORECASE)
            if season_match:
                season_num = int(season_match.group(1))
            
            # Build display title
            if show_title and season_num:
                display_title = '{} S{}E{}'.format(show_title, str(season_num).zfill(2), str(episode_num).zfill(2))
            elif show_title:
                display_title = '{} E{}'.format(show_title, str(episode_num).zfill(2))
            else:
                display_title = 'الحلقة {}'.format(episode_num)
            
            site.add_dir(display_title, ep_url, 'getLinks', site.image,
                       season=season_num, episode=episode_num, show_title=show_title,
                       year=year, media_type='episode')
    else:
        # No episodes found, might be a direct video page
        utils.kodilog('ArabSeed: No episodes found, trying direct playback')
        site.add_dir(show_title if show_title else 'Play', url, 'getLinks', site.image)
    
    utils.eod(content='episodes')

@site.register()
def getLinks(url, name=''):
    """Extract video links from data-link attributes"""
    import base64
    
    utils.kodilog('ArabSeed: Extracting links from: {}'.format(url))
    
    # Get watch page HTML
    watch_url = url.rstrip('/') + '/watch/'
    html = utils.getHtml(watch_url)
    if not html:
        utils.notify('ArabSeed', 'No video links found')
        utils.eod(content='videos')
        return
    
    # Extract server links — pattern captures data-qu quality attribute
    # <li data-server="0" data-qu="480" data-link="URL" ...><span>Server Name</span></li>
    server_pattern = r'<li[^>]*data-server="([^"]+)"[^>]*data-qu="([^"]*)"[^>]*data-link="([^"]+)"[^>]*>.*?<span>([^<]*)</span>'
    servers = re.findall(server_pattern, html, re.DOTALL)
    
    utils.kodilog('ArabSeed: Found {} servers with data-link'.format(len(servers)))
    
    if not servers:
        utils.notify('ArabSeed', 'No video links found')
        utils.eod(content='videos')
        return
    
    # Process each server
    hoster_manager = get_hoster_manager()
    
    for server_id, quality_raw, link_url, server_name in servers:
        utils.kodilog('ArabSeed: Processing server {}: {}'.format(server_id, server_name))
        
        # Normalise quality string (e.g. "480" → "480p")
        quality = ''
        if quality_raw:
            q = quality_raw.strip()
            quality = q if q.endswith('p') else q + 'p' if q.isdigit() else q
        
        # Handle relative URLs
        if link_url.startswith('/'):
            link_url = site.url.rstrip('/') + link_url
        
        utils.kodilog('ArabSeed: Server {} link: {}'.format(server_id, link_url))
        
        # Check if URL contains base64 encoded parameter
        final_url = link_url
        if '?url=' in link_url or '?id=' in link_url:
            try:
                param_match = re.search(r'[?&](?:url|id)=([^&]+)', link_url)
                if param_match:
                    encoded = param_match.group(1)
                    encoded = re.sub(r'[^A-Za-z0-9+/=]', '', encoded)
                    padding = len(encoded) % 4
                    if padding:
                        encoded += '=' * (4 - padding)
                    decoded = base64.b64decode(encoded).decode('utf-8')
                    utils.kodilog('ArabSeed: Decoded URL: {}'.format(decoded))
                    final_url = decoded
            except Exception as e:
                utils.kodilog('ArabSeed: Base64 decode error: {}'.format(str(e)))
        
        # Format link with icon and check filtering
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            final_url,
            'ArabSeed',
            name if name else 'Video',
            quality
        )
        
        if should_skip:
            utils.kodilog('ArabSeed: Filtered out: {}'.format(final_url[:100]))
            continue
        
        # Add link WITHOUT resolving - resolution happens in PlayVid
        site.add_download_link(label, final_url, 'PlayVid', site.image, desc=name,
                              quality=quality, fanart=site.image, landscape=site.image)
    
    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Play video - resolve hoster URL on-demand when user clicks"""
    hoster_manager = get_hoster_manager()
    
    utils.kodilog('ArabSeed: Attempting to resolve: {}'.format(url[:100]))
    
    # Try to resolve with hoster manager
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        headers = result.get('headers', {})
        
        # Format headers for URL (Kodi accepts headers in URL format)
        if headers:
            header_str = '|' + '&'.join(['{}={}'.format(k, v) for k, v in headers.items()])
            video_url = video_url + header_str
        
        utils.kodilog('ArabSeed: Resolved to: {}'.format(video_url[:100]))
    else:
        utils.kodilog('ArabSeed: No resolver found, trying direct playback')
        video_url = url
    
    utils.playvid(video_url, name, site.image)
