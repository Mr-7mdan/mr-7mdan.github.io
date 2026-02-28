# -*- coding: utf-8 -*-
"""
ShoofMax Site Module
https://shoofmax.com/
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase

site = SiteBase('shoofmax', 'ShoofMax', url=None, image='sites/shoofmax.png')

# Default poster when listings don't have individual posters
DEFAULT_POSTER = 'https://shoofmax-static.b-cdn.net/v2/img/general/small-cover.jpg'


@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    """Main menu"""
    utils.kodilog(f'{site.title}: Main menu')
    
    site.add_dir('Movies', f'{site.url}/genre/فيلم', 'getMovies', get_category_icon('Movies'))
    site.add_dir('TV Shows', f'{site.url}/genre/مسلسل', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    utils.eod()


@site.register()
def search():
    """Search for content"""
    utils.kodilog(f'{site.title}: Search')
    
    keyboard = utils.get_keyboard('')
    if keyboard:
        query = keyboard.getText()
        if query:
            search_url = f'{site.url}/search?q={utils.quote_plus(query)}'
            getMovies(search_url)
    else:
        utils.eod(content='tvshows')


@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='movies')
        return
    
    # Find the start of synchronous-page-content
    idx = html.find('class="synchronous-page-content"')
    
    if idx < 0:
        utils.kodilog(f'{site.title}: No synchronous-page-content found')
        utils.eod(content='movies')
        return
    
    # Extract from this point forward (HTML may be truncated, so don't rely on closing tag)
    content_from_sync = html[idx:]
    
    # Extract program links directly without requiring closing tag
    pattern = r'<a href="(/program/\d+[^"]*)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, content_from_sync)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} movies')
    
    for program_url, title in matches:
        # Clean title - remove "فيلم" prefix
        title = re.sub(r'^فيلم\s+', '', title).strip()
        
        full_url = f'{site.url}{program_url}'
        
        # Check if it's a movie (no ep parameter) or series (has ep parameter)
        if '?ep=' in program_url:
            # This is actually a series, skip in movies
            continue
        
        # Use addDownLink for playable video items
        basics.addDownLink(title, full_url, 'shoofmax.PlayVid', DEFAULT_POSTER)
    
    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    utils.kodilog(f'{site.title}: Getting TV shows from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return
    
    # Find the start of synchronous-page-content
    idx = html.find('class="synchronous-page-content"')
    
    if idx < 0:
        utils.kodilog(f'{site.title}: No synchronous-page-content found')
        utils.eod(content='tvshows')
        return
    
    # Extract from this point forward (HTML may be truncated, so don't rely on closing tag)
    content_from_sync = html[idx:]
    
    # Extract program links directly without requiring closing tag
    pattern = r'<a href="(/program/\d+[^"]*)"[^>]*>([^<]+)</a>'
    matches = re.findall(pattern, content_from_sync)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} series')
    
    for program_url, title in matches:
        # Clean title - remove "مسلسل" prefix
        title = re.sub(r'^مسلسل\s+', '', title).strip()
        
        # Remove query parameters for cleaner URL to series page
        base_url = program_url.split('?')[0]
        full_url = f'{site.url}{base_url}'
        
        site.add_dir(
            title,
            full_url,
            'getEpisodes',
            DEFAULT_POSTER
        )
    
    utils.eod(content='tvshows')


@site.register()
def getEpisodes(url):
    """Get episodes for a series"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='episodes')
        return
    
    # Extract series title from page
    title_match = re.search(r'<title>([^<]+)</title>', html)
    series_title = ''
    if title_match:
        series_title = title_match.group(1).replace(' الحلقة', '').replace('الحلقة', '').strip()
        series_title = re.sub(r'^مسلسل\s+', '', series_title).strip()
    
    # Extract episode selector
    selector = re.search(r'<select class="episode-control-select"[^>]*>(.*?)</select>', html, re.DOTALL)
    
    if not selector:
        utils.kodilog(f'{site.title}: No episode selector found')
        utils.eod(content='episodes')
        return
    
    # Extract episode options
    pattern = r'<option[^>]*value="(\d+)"'
    episodes = re.findall(pattern, selector.group(1))
    
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')
    
    for ep_num in episodes:
        ep_title = f'{series_title} - الحلقة {ep_num}' if series_title else f'الحلقة {ep_num}'
        ep_url = f'{url}?ep={ep_num}'
        
        # Use addDownLink for playable video items
        basics.addDownLink(ep_title, ep_url, 'shoofmax.PlayVid', DEFAULT_POSTER)
    
    utils.eod(content='episodes')


@site.register()
def PlayVid(url, name=''):
    """Extract and play video"""
    utils.kodilog(f'{site.title}: Playing video from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'فشل تحميل الصفحة', icon=site.image)
        return
    
    # Extract origin_link
    origin_match = re.search(r'var origin_link = "([^"]+)"', html)
    if not origin_match:
        utils.kodilog(f'{site.title}: No origin_link found')
        utils.notify(site.title, 'لم يتم العثور على رابط الفيديو', icon=site.image)
        return
    
    origin_link = origin_match.group(1)
    utils.kodilog(f'{site.title}: Found origin_link: {origin_link}')
    
    # Extract src object
    src_pattern = r'var src = \{([^}]+)\}'
    src_match = re.search(src_pattern, html, re.DOTALL)
    
    if not src_match:
        utils.kodilog(f'{site.title}: No src object found')
        utils.notify(site.title, 'لم يتم العثور على مصدر الفيديو', icon=site.image)
        return
    
    src_content = src_match.group(1)
    
    # Try to extract HLS first (best quality)
    hls_match = re.search(r'hls:\s*origin_link\s*\+\s*"([^"]+)"', src_content)
    if hls_match:
        hls_path = hls_match.group(1)
        video_url = f'{origin_link}{hls_path}'
        utils.kodilog(f'{site.title}: Found HLS: {video_url}')
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
        return
    
    # Fallback to MP4
    mp4_matches = re.findall(r'origin_link\s*\+\s*"([^"]+\.mp4)"', src_content)
    if mp4_matches:
        # Use the higher quality MP4 (last one usually)
        video_url = f'{origin_link}{mp4_matches[-1]}'
        utils.kodilog(f'{site.title}: Found MP4: {video_url}')
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
        return
    
    utils.kodilog(f'{site.title}: No video sources found')
    utils.notify(site.title, 'لم يتم العثور على رابط قابل للتشغيل', icon=site.image)
