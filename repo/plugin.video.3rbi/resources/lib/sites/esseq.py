# -*- coding: utf-8 -*-
"""
Esseq (قصة عشق) Site Module
https://qeseh.net/
"""

import re
import base64
import json
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('esseq', 'Esseq', url=None, image='sites/esseq.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    """Main menu"""
    # Site now primarily shows latest episodes on homepage
    site.add_dir('Latest Episodes', site.url + '/', 'getEpisodes', get_category_icon('Ramadan TV Shows'))
    site.add_dir('Series', site.url + '/series/', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    
    utils.eod()

@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return
    
    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    
    search_url = f'{site.url}/?s={search_text}'
    getMovies(search_url)

@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='movies')
        return
    
    # Esseq uses data-img attribute
    pattern = r'<a href="([^"]+)" title="([^"]+)"[^>]*>.*?data-img="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    if matches:
        for movie_url, title, image in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Clean image URL
            full_image = image.strip()
            
            if title:
                site.add_dir(title, movie_url, 'getLinks', full_image,
                           year=year, media_type='movie')
    
    # Pagination
    next_match = re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')

@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    utils.kodilog(f'{site.title}: Getting series from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='tvshows')
        return
    
    # Same pattern as movies
    pattern = r'<a href="([^"]+)" title="([^"]+)"[^>]*>.*?data-img="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')
    
    seen_titles = set()
    
    if matches:
        for series_url, title, image in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|مسلسل|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Strip episode suffix to get show title for deduplication
            show_title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
            show_title = re.sub(r'\s+', ' ', show_title).strip()
            
            if not show_title or show_title in seen_titles:
                continue
            seen_titles.add(show_title)
            
            # Clean image URL
            full_image = image.strip()
            
            # Series pages go directly to getEpisodes
            site.add_dir(show_title, series_url, 'getEpisodes', full_image,
                       year=year, media_type='tvshow')
    
    # Pagination
    next_match = re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')

@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='episodes')
        return
    
    # Episodes use same pattern
    pattern = r'<a href="([^"]+)" title="([^"]+)"[^>]*>.*?data-img="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} episodes')
    
    if matches:
        for ep_url, ep_title, ep_image in matches:
            # Skip non-episode links
            if '/video/' not in ep_url:
                continue
                
            # Clean title
            ep_title = ep_title.strip()
            ep_title = re.sub(r'مشاهدة|مسلسل|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', ep_title).strip()
            
            # Extract episode number
            ep_num = ''
            ep_match = re.search(r'episode[- ](\d+)', ep_url, re.IGNORECASE)
            if ep_match:
                ep_num = ep_match.group(1)
            elif re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', ep_title, re.IGNORECASE):
                ep_match = re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', ep_title, re.IGNORECASE)
                ep_num = ep_match.group(1)
            
            # Clean image URL
            full_image = ep_image.strip()
            
            if ep_title:
                site.add_dir(ep_title, ep_url, 'getLinks', full_image,
                           episode=ep_num, media_type='episode')
    
    # Pagination for episodes (if any)
    next_match = re.search(r'<link[^>]+rel="next"[^>]+href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getEpisodes', addon_image(site.img_next))
    
    utils.eod(content='episodes')

@site.register()
def getLinks(url, name=''):
    """Extract video links from episode/movie page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    # Fetch downloads page
    download_url = url + '?do=downloads' if '?do=' not in url else url
    html = utils.getHtml(download_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Extract video links from downloads page
    hoster_manager = get_hoster_manager()
    servers_added = 0
    
    # Pattern: Find external video host links
    link_pattern = r'href="([^"]+(?:vidsp|ok\.ru|uqload|voe|dood|streamtape)[^"]+)"'
    video_links = re.findall(link_pattern, html, re.IGNORECASE)
    
    utils.kodilog(f'{site.title}: Found {len(video_links)} potential video links')
    
    if video_links:
        for video_url in video_links:
            video_url = video_url.strip()
            
            # Skip social media links
            if any(x in video_url.lower() for x in ['facebook', 'twitter', 'instagram', 'youtube', 'google']):
                continue
            
            # Extract server name from URL
            server_name = 'Server'
            if 'vidsp' in video_url:
                server_name = 'VidSP'
            elif 'ok.ru' in video_url:
                server_name = 'OK.ru'
            elif 'uqload' in video_url:
                server_name = 'Uqload'
            elif 'voe' in video_url:
                server_name = 'Voe'
            elif 'dood' in video_url:
                server_name = 'Dood'
            elif 'streamtape' in video_url:
                server_name = 'Streamtape'
            
            label, should_skip = utils.format_resolver_link(
                hoster_manager,
                video_url,
                site.title,
                name,
                quality=server_name
            )
            
            if not should_skip:
                basics.addDownLink(label, video_url, f'{site.name}.PlayVid', site.image)
                servers_added += 1
    
    utils.kodilog(f'{site.title}: Added {servers_added} servers')
    
    if servers_added == 0:
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
