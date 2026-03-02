# -*- coding: utf-8 -*-
"""
Shhid4u Site Module
https://shhid4u.net/
"""

import re
import json
import html as html_module
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('shhid4u', 'Shahid4U', url=None, image='sites/shhid4u.png')


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon
    
    utils.kodilog(f'{site.title}: Main menu')
    
    # Movies
    site.add_dir('English Movies', f'{site.url}/category/افلام-اجنبي', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Indian Movies', f'{site.url}/category/افلام-هندي', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Anime Movies', f'{site.url}/category/افلام-انمي', 'getMovies', get_category_icon('Anime Movies'))
    site.add_dir('Asian Movies', f'{site.url}/category/افلام-اسيوية', 'getMovies', get_category_icon('Asian Movies'))
    site.add_dir('Turkish Movies', f'{site.url}/category/افلام-تركية', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Arabic Movies', f'{site.url}/category/افلام-عربي', 'getMovies', get_category_icon('Arabic Movies'))
    
    # TV Shows
    site.add_dir('English TV Shows', f'{site.url}/category/مسلسلات-اجنبي', 'getEpisodes', get_category_icon('English TV Shows'))
    site.add_dir('Cartoon TV Shows', f'{site.url}/category/مسلسلات-انمي', 'getEpisodes', get_category_icon('Cartoon TV Shows'))
    site.add_dir('Turkish TV Shows', f'{site.url}/category/مسلسلات-تركية', 'getEpisodes', get_category_icon('Turkish TV Shows'))
    site.add_dir('Asian TV Shows', f'{site.url}/category/مسلسلات-اسيوية', 'getEpisodes', get_category_icon('Asian TV Shows'))
    site.add_dir('Dubbed Movies', f'{site.url}/category/مسلسلات-مدبلجة', 'getEpisodes', get_category_icon('Dubbed Movies'))
    site.add_dir('Arabic TV Shows', f'{site.url}/category/مسلسلات-عربي', 'getEpisodes', get_category_icon('Arabic TV Shows'))
    site.add_dir('Indian TV Shows', f'{site.url}/category/مسلسلات-هندية', 'getEpisodes', get_category_icon('Indian TV Shows'))
    
    # Other
    site.add_dir('TV Programs', f'{site.url}/category/برامج-تلفزيونية', 'getEpisodes', get_category_icon('TV Programs'))
    site.add_dir('WWE', f'{site.url}/category/عروض-مصارعة', 'getEpisodes', get_category_icon('WWE'))
    site.add_dir('Ramadan TV Shows', f'{site.url}/category/مسلسلات-رمضان-2026', 'getEpisodes', get_category_icon('Ramadan TV Shows'))
    
    # Search
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
            search_url = f'{site.url}/?s={utils.quote_plus(query)}'
            # Search returns mixed content (movies + episodes)
            getMixed(search_url)
    else:
        utils.eod(content='tvshows')


@site.register()
def getMovies(url, page=1):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    # Handle None page value from URL dispatcher
    if page is None:
        page = 1
    
    # Add pagination parameter
    if page > 1:
        url = f'{url}?page={page}' if '?' not in url else f'{url}&page={page}'
    
    headers = {'User-Agent': utils.USER_AGENT}
    # Use _getHtml directly to bypass cache (site has dynamic content)
    html = utils._getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='movies')
        return
    
    # Debug: log HTML length and check for show-card
    utils.kodilog(f'{site.title}: HTML length={len(html)}, show-card count={html.count("show-card")}')
    
    # Pattern: show-card anchor + background-image (style may have space after colon)
    pattern = r'<a\s[^>]*href="([^"]+)"[^>]*class="show-card"[^>]*style="background-image:\s*url\(([^)]+)\)[^>]*>([\s\S]*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    if not matches:
        pattern = r'<a\s[^>]*class="show-card"[^>]*href="([^"]+)"[^>]*style="background-image:\s*url\(([^)]+)\)[^>]*>([\s\S]*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    for item_url, image, card_html in matches:
        # Only process film URLs
        if '/film/' not in item_url:
            continue
        
        # Try to extract title from card content first, fall back to URL slug
        title_m = re.search(r'<(?:h3|p)[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<|<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<', card_html)
        if title_m:
            title = (title_m.group(1) or title_m.group(2) or '').strip()
        else:
            slug = item_url.rstrip('/').split('/')[-1]
            title = html_module.unescape(slug).replace('-', ' ').replace('_', ' ')
        
        # Clean title
        title = title.strip()
        title = re.sub(r'^فيلم\s+', '', title)
        
        # Extract year if present
        year = ''
        year_match = re.search(r'(\d{4})', title)
        if year_match:
            year = year_match.group(1)
        
        if title:
            site.add_dir(title, item_url, 'getLinks', image, year=year, media_type='movie')
    
    # Pagination
    if matches:
        next_page = page + 1
        site.add_dir('الصفحة التالية', url.split('?')[0], 'getMovies', addon_image(site.img_next), page=next_page)
    
    utils.eod(content='movies')


@site.register()
def getEpisodes(url, page=1):
    """Get episodes listing (series categories show episodes directly)"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    # Handle None page value from URL dispatcher
    if page is None:
        page = 1
    
    # Add pagination parameter
    if page > 1:
        url = f'{url}?page={page}' if '?' not in url else f'{url}&page={page}'
    
    headers = {'User-Agent': utils.USER_AGENT}
    # Use _getHtml directly to bypass cache (site has dynamic content)
    html = utils._getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='episodes')
        return
    
    # Pattern: show-card anchor + background-image (style may have space after colon)
    pattern = r'<a\s[^>]*href="([^"]+)"[^>]*class="show-card"[^>]*style="background-image:\s*url\(([^)]+)\)[^>]*>([\s\S]*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    if not matches:
        pattern = r'<a\s[^>]*class="show-card"[^>]*href="([^"]+)"[^>]*style="background-image:\s*url\(([^)]+)\)[^>]*>([\s\S]*?)</a>'
        matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    for item_url, image, card_html in matches:
        # Only process episode URLs
        if '/episode/' not in item_url:
            continue
        
        # Try to extract title from card content first, fall back to URL slug
        title_m = re.search(r'<(?:h3|p)[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<|<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<', card_html)
        if title_m:
            title = (title_m.group(1) or title_m.group(2) or '').strip()
        else:
            slug = item_url.rstrip('/').split('/')[-1]
            title = html_module.unescape(slug).replace('-', ' ').replace('_', ' ')
        
        # Clean title
        title = title.strip()
        title = re.sub(r'^مسلسل\s+', '', title)
        
        if title:
            site.add_dir(title, item_url, 'getLinks', image, media_type='episode')
    
    # Pagination
    if matches:
        next_page = page + 1
        site.add_dir('الصفحة التالية', url.split('?')[0], 'getEpisodes', addon_image(site.img_next), page=next_page)
    
    utils.eod(content='episodes')


@site.register()
def getMixed(url, page=1):
    """Get mixed content from search results"""
    utils.kodilog(f'{site.title}: Getting mixed content from: {url}')
    
    # Handle None page value from URL dispatcher
    if page is None:
        page = 1
    
    # Add pagination parameter
    if page > 1:
        url = f'{url}&page={page}' if '?s=' in url else f'{url}?page={page}'
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod()
        return
    
    # Pattern for show-card with background-image (space after colon optional)
    pattern = r'<a\s[^>]*href="([^"]+)"[^>]*class="show-card"[^>]*style="background-image:\s*url\(([^)]+)\)[^>]*>([\s\S]*?)</a>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    for item_url, image, card_html in matches:
        title_m = re.search(r'<(?:h3|p)[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<|<span[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)<', card_html)
        if title_m:
            title = (title_m.group(1) or title_m.group(2) or '').strip()
        else:
            slug = item_url.rstrip('/').split('/')[-1]
            title = html_module.unescape(slug).replace('-', ' ')
        title = title.strip()
        
        # Route based on URL type
        if '/film/' in item_url:
            # Movie
            title = re.sub(r'^فيلم\s+', '', title)
            site.add_dir(title, item_url, 'getLinks', image, media_type='movie')
        elif '/episode/' in item_url:
            # Episode
            title = re.sub(r'^مسلسل\s+', '', title)
            site.add_dir(title, item_url, 'getLinks', image, media_type='episode')
    
    # Pagination
    if matches:
        next_page = page + 1
        # Preserve search query in pagination
        base_url = url.split('&page=')[0] if '&page=' in url else url.split('?page=')[0] if '?page=' in url else url
        site.add_dir('الصفحة التالية', base_url, 'getMixed', addon_image(site.img_next), page=next_page)
    
    utils.eod()


@site.register()
def getLinks(url, name=''):
    """Extract video links from watch page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    # First, get the content page to find watch link
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Find watch URL
    watch_match = re.search(r'<a href="([^"]+)" class="btn watch"', html)
    
    if watch_match:
        watch_url = watch_match.group(1)
    else:
        # Try direct watch URL construction
        if '/film/' in url:
            watch_url = url.replace('/film/', '/watch/')
        elif '/episode/' in url:
            watch_url = url.replace('/episode/', '/watch/')
        else:
            watch_url = url + '/watch'
    
    utils.kodilog(f'{site.title}: Watch URL: {watch_url}')
    
    # Fetch watch page
    watch_html = utils.getHtml(watch_url, headers=headers, site_name=site.name)
    
    if not watch_html:
        utils.notify(site.title, 'لم يتم تحميل صفحة المشاهدة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Extract servers JSON
    servers_match = re.search(r"servers=JSON\.parse\('(\[.*?\])'\)", watch_html, re.DOTALL)
    
    if not servers_match:
        utils.kodilog(f'{site.title}: No servers JSON found')
        utils.notify(site.title, 'لم يتم العثور على سيرفرات', icon=site.image)
        utils.eod(content='videos')
        return
    
    try:
        # Parse JSON (handle escaped characters)
        servers_json = servers_match.group(1).replace(r'\/', '/').replace(r'\u0026', '&')
        servers = json.loads(servers_json)
        
        utils.kodilog(f'{site.title}: Found {len(servers)} servers')
        
        hoster_manager = get_hoster_manager()
        
        for server in servers:
            server_name = server.get('name', 'Server')
            embed_url = server.get('url', '')
            
            if not embed_url:
                continue
            
            # Format link with resolver icons
            label, should_skip = utils.format_resolver_link(
                hoster_manager,
                embed_url,
                site.title,
                name,
                quality=server_name
            )
            
            if not should_skip:
                basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)
        
        if not servers:
            utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
    except json.JSONDecodeError as e:
        utils.kodilog(f'{site.title}: JSON parse error: {e}')
        utils.notify(site.title, 'خطأ في قراءة بيانات السيرفرات', icon=site.image)
    
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
