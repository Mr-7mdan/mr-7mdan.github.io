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
    site.add_dir('Movies', site.url + '/category/filmler/', 'getMovies', get_category_icon('Movies'))
    site.add_dir('Complete Series', site.url + '/category/arsiv/', 'getTVShows', get_category_icon('Complete Series'))
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
    
    # Esseq uses background-image in style attribute
    pattern = r'<a href="([^"]+)"[^>]*>.*?background-image:url\(([^\)]+)\).*?<div class="title">([^<]+)</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    if matches:
        for movie_url, image, title in matches:
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
    pattern = r'<a href="([^"]+)"[^>]*>.*?background-image:url\(([^\)]+)\).*?<div class="title">([^<]+)</div>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')
    
    seen_titles = set()
    
    if matches:
        for series_url, image, title in matches:
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
    pattern = r'<a href="(https://qeseh\.net/[^"]*episode[^"]+)"[^>]*>.*?background-image:url\(([^\)]+)\).*?<div class="title">([^<]+)</div>'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} episodes')
    
    if matches:
        for ep_url, ep_image, ep_title in matches:
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
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Find the watch URL with base64 encoded JSON
    watch_url_match = re.search(r'https://qesen\.net/watch\?post=([^"\'&\s]+)', html)
    
    if not watch_url_match:
        utils.notify(site.title, 'لم يتم العثور على روابط المشاهدة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Decode base64 JSON
    encoded_data = watch_url_match.group(1)
    
    try:
        decoded_json = base64.b64decode(encoded_data).decode('utf-8')
        data = json.loads(decoded_json)
        
        utils.kodilog(f'{site.title}: Decoded watch data')
        
        hoster_manager = get_hoster_manager()
        servers_added = 0
        
        # Skip Dailymotion - blocked by Cloudflare
        # Keep for reference if Cloudflare bypass is added later
        
        # Add servers from JSON
        if 'servers' in data:
            for server_info in data['servers']:
                server_name = server_info.get('name', 'Unknown')
                server_id = server_info.get('id', '')
                
                if not server_id:
                    continue
                
                # Map server names to actual video hosts
                server_url = None
                
                if server_name.lower() == 'ok':
                    # OK.ru video platform - working with existing resolver
                    server_url = f'https://ok.ru/videoembed/{server_id}'
                elif server_name.lower() in ['arab hd', 'arabhd']:
                    # Arab HD returns empty array - API broken, skip
                    utils.kodilog(f'{site.title}: Skipping Arab HD (broken API)')
                    continue
                elif server_name.lower() == 'estream':
                    # estream returns tracking pixel only - broken, skip
                    utils.kodilog(f'{site.title}: Skipping estream (broken)')
                    continue
                else:
                    # Unknown server - log and skip
                    utils.kodilog(f'{site.title}: Unknown server type: {server_name}')
                    continue
                
                if server_url:
                    label, should_skip = utils.format_resolver_link(
                        hoster_manager,
                        server_url,
                        site.title,
                        name,
                        quality=server_name
                    )
                    
                    if not should_skip:
                        basics.addDownLink(label, server_url, f'{site.name}.PlayVid', site.image)
                        servers_added += 1
        
        utils.kodilog(f'{site.title}: Added {servers_added} servers')
        
        if servers_added == 0:
            utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
    except Exception as e:
        utils.kodilog(f'{site.title}: Error decoding watch data: {e}')
        utils.notify(site.title, 'خطأ في فك تشفير البيانات', icon=site.image)
    
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
