# -*- coding: utf-8 -*-
"""
Qrmzi.tv Site Module
Turkish TV Shows streaming site
"""

import re
from urllib.parse import quote
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('qrmzi', 'Qrmzi', url=None, image='sites/qrmzi.png')


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon
    utils.kodilog(f'{site.title}: Main menu')
    
    site.add_dir('Turkish TV Shows', f'{site.url}/all-turkish-series/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    utils.eod(content='tvshows')


@site.register()
def search():
    """Search for content"""
    utils.kodilog(f'{site.title}: Search')
    
    search_text = utils.get_search_input()
    if search_text:
        search_url = f'{site.url}/?s={search_text}'
        getTVShows(search_url)
    else:
        utils.eod(content='tvshows')


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
    
    # Extract series from article blocks with poster images
    pattern = r'<a href="([^"]+)" title="([^"]+)"[^>]*>.*?<img[^>]*data-src="?([^" >]+)"?'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')
    
    seen_titles = set()
    
    for series_url, title, poster in matches:
        # Skip non-series URLs (e.g. site homepage link)
        if '/series/' not in series_url:
            continue
        # Clean title - remove "قرمزي" suffix if present
        title = re.sub(r'\s+قرمزي\s*$', '', title).strip()
        title = re.sub(r'مشاهدة|مسلسل|مدبلجلة|مترجمة|اون لاين|HD|كاملة', '', title).strip()
        title = re.sub(r'مترجم|مدبلج|كامل', '', title).strip()
        
        # Strip episode suffix to get show title for deduplication
        show_title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
        show_title = re.sub(r'\s+', ' ', show_title).strip()
        
        if not show_title or show_title in seen_titles:
            continue
        seen_titles.add(show_title)
        
        # Remove dimension suffix to get hi-res image (e.g., -470x255.jpg -> .jpg)
        poster = re.sub(r'-\d+x\d+\.', '.', poster)

        site.add_dir(
            show_title,
            series_url,
            'getEpisodes',
            poster
        )
    
    # Check for pagination
    next_page = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_page:
        site.add_dir(
            'الصفحة التالية',
            next_page.group(1),
            'getTVShows',
            addon_image(site.img_next)
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
    
    # Extract episode links with poster images
    pattern = r'<a href="(https://www\.qrmzi\.tv/episode/[^"]+)" title="([^"]+)"[^>]*>.*?<img[^>]*data-src="?([^" >]+)"?'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} episodes')
    
    # Process and sort episodes by number
    episodes = []
    for ep_url, ep_title, poster in matches:
        # Clean title - remove "قرمزي" suffix
        ep_title = re.sub(r'\s+قرمزي\s*$', '', ep_title).strip()
        ep_title = re.sub(r'مشاهدة|مسلسل|مدبلجلة|مترجمة|اون لاين|HD|كامل|كاملة', '', ep_title).strip()
        ep_title = re.sub(r'مترجم|مدبلج', '', ep_title).strip()
        
        # Extract episode number for sorting
        ep_num_match = re.search(r'(?:الحلقة|حلقة|Episode)\s*(\d+)', ep_title, re.IGNORECASE)
        ep_num = int(ep_num_match.group(1)) if ep_num_match else 0
        
        # Strip TV show name - keep only "Episode X"
        # Remove everything before and including the episode number word
        display_title = re.sub(r'.*?\s*(?:الحلقة|حلقة)\s*\d+', f'Episode {ep_num}', ep_title).strip()
        display_title = re.sub(r'Episode\s+(\d+).*', r'Episode \1', display_title).strip()
        
        # Remove dimension suffix to get hi-res image (e.g., -470x255.jpg -> .jpg)
        poster = re.sub(r'-\d+x\d+\.', '.', poster)
        
        episodes.append((ep_num, display_title, ep_url, poster))
    
    # Sort by episode number (lowest to highest)
    episodes.sort(key=lambda x: x[0])
    
    # Add sorted episodes
    for ep_num, display_title, ep_url, poster in episodes:
        site.add_dir(display_title, ep_url, 'PlayVid', poster, media_type='episode')
    
    utils.eod(content='episodes')


@site.register()
def PlayVid(url, name=''):
    """Extract server options and play video"""
    utils.kodilog(f'{site.title}: Playing video from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.notify('خطأ', 'لم يتم العثور على الصفحة', icon=site.image)
        return
    
    # Extract iframe source
    iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', html, re.IGNORECASE)
    
    if not iframe_match:
        utils.kodilog(f'{site.title}: No iframe found')
        utils.notify('خطأ', 'لم يتم العثور على الفيديو', icon=site.image)
        return
    
    iframe_url = iframe_match.group(1)
    utils.kodilog(f'{site.title}: Found iframe: {iframe_url}')
    
    # Fetch iframe page to extract server options
    iframe_html = utils.getHtml(iframe_url, headers=headers)
    
    if not iframe_html:
        utils.kodilog(f'{site.title}: No iframe HTML received')
        utils.notify('خطأ', 'لم يتم تحميل المشغل', icon=site.image)
        return
    
    # Extract server links from iframe player
    server_pattern = r'<a class="aplr-link[^"]*" href="([^"]+\?serv=\d+)"[^>]*>([^<]+)</a>'
    servers = re.findall(server_pattern, iframe_html)
    
    utils.kodilog(f'{site.title}: Found {len(servers)} servers')
    
    for server_url, server_name in servers:
        server_name = server_name.strip()
        if not server_name:  # Skip empty server names
            continue
        
        utils.kodilog(f'{site.title}: Adding server: {server_name} - {server_url}')
        
        # Add server directly without pre-filtering
        # The actual embed URL will be extracted in ResolveServer
        label = f'[{server_name}] {name}'
        basics.addDownLink(label, server_url, 'qrmzi.ResolveServer', site.image)
    
    if not servers:
        utils.notify('Qrmzi', 'لم يتم العثور على سيرفرات', icon=site.image)
    
    utils.eod(content='videos')


@site.register()
def ResolveServer(url, name=''):
    """Resolve and play from server URL"""
    utils.kodilog(f'{site.title}: Resolving server: {url}')
    
    from resources.lib.hoster_resolver import get_hoster_manager
    hoster_manager = get_hoster_manager()
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers)
    
    if not html:
        utils.notify('خطأ', 'لم يتم تحميل السيرفر', icon=site.image)
        return
    
    # Extract embed URLs from server page
    # Pattern 1: iframe src
    iframe_pattern = r'<iframe[^>]*src="([^"]+)"'
    iframe_match = re.search(iframe_pattern, html, re.IGNORECASE)
    
    if iframe_match:
        embed_url = iframe_match.group(1)
        utils.kodilog(f'{site.title}: Found iframe embed: {embed_url}')
        
        # Try to resolve the embed URL
        resolved = hoster_manager.resolve(embed_url)
        
        if resolved:
            utils.kodilog(f'{site.title}: Resolved to: {resolved}')
            
            # Extract URL and headers from dict if resolver returns dict
            if isinstance(resolved, dict):
                video_url = resolved.get('url', resolved)
                headers = resolved.get('headers', {})
                
                # Format URL with headers for Kodi: URL|Header1=value1&Header2=value2
                # URL-encode header values to avoid malformed URLs
                if headers:
                    header_parts = []
                    for k, v in headers.items():
                        # URL-encode the value to handle special characters
                        encoded_value = quote(str(v), safe='')
                        header_parts.append(f'{k}={encoded_value}')
                    header_string = '&'.join(header_parts)
                    video_url = f'{video_url}|{header_string}'
                    utils.kodilog(f'{site.title}: Added headers to URL')
                
                utils.kodilog(f'{site.title}: Final URL: {video_url[:150]}...')
            else:
                video_url = resolved
            
            utils.VideoPlayer(name, False).play_from_direct_link(video_url)
            return
        else:
            utils.kodilog(f'{site.title}: Resolver failed, trying direct playback')
            utils.VideoPlayer(name, False).play_from_direct_link(embed_url)
            return
    
    # Pattern 2: Direct video file URLs in JavaScript
    js_patterns = [
        r'file:\s*["\']([^"\'\']+)["\']',
        r'source:\s*["\']([^"\'\']+)["\']',
        r'src:\s*["\']([^"\'\']+\.m3u8[^"\'\']*)["\']',
    ]
    
    for pattern in js_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            video_url = match.group(1)
            utils.kodilog(f'{site.title}: Found direct video URL: {video_url}')
            utils.VideoPlayer(name, False).play_from_direct_link(video_url)
            return
    
    utils.kodilog(f'{site.title}: No playable URL found in server page')
    utils.notify('خطأ', 'لم يتم العثور على رابط الفيديو', icon=site.image)
