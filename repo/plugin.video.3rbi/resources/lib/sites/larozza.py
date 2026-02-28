# -*- coding: utf-8 -*-
"""
Larozza Site Module
https://larozza.xyz/
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('larozza', 'Larozza', url=None, image='sites/larozza.png')

# Categories discovered from homepage - mapped to unified names for category_mapper
CATEGORIES = [
    ('Arabic Movies', 'arabic-movies33'),
    ('English Movies', 'all_movies_13'),
    ('Indian Movies', 'indian-movies9'),
    ('Dubbed Movies', '7-aflammdblgh'),
    ('Anime Movies', 'anime-movies-7'),
    ('Ramadan TV Shows', 'ramadan-2026'),
    ('Arabic TV Shows', 'arabic-series46'),
    ('Turkish TV Shows', 'turkish-3isk-seriess47'),
    ('TV Programs', 'tv-programs12'),
]


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon
    
    utils.kodilog(f'{site.title}: Main menu')
    
    # Add categories with unified names for proper icon mapping
    for name, cat_id in CATEGORIES:
        url = f'{site.url}/category.php?cat={cat_id}'
        icon = get_category_icon(name)
        site.add_dir(name, url, 'getVideos', icon)
    
    # Search
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    
    utils.eod()


@site.register()
def search():
    """Search for content"""
    utils.kodilog(f'{site.title}: Search')
    
    search_text = utils.get_search_input()
    if search_text:
        search_url = f'{site.url}/search.php?keywords={utils.quote_plus(search_text)}'
        getVideos(search_url)


@site.register()
def getVideos(url):
    """Get videos listing (movies and episodes)"""
    utils.kodilog(f'{site.title}: Getting videos from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='videos')
        return
    
    # Pattern tested in terminal - works for both category and search pages
    pattern = r'<li class="col-xs-6[^>]*>.*?<a href="(https://larozza\.xyz/video\.php\?vid=[^"]+)"[^>]+title="([^"]+)"[^>]*>.*?<img[^>]+data-echo="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} videos')
    
    for video_url, title, image in matches:
        # Clean title - remove common prefixes
        title = title.strip()
        title = re.sub(r'^(فيلم|مسلسل)\s+', '', title)
        title = re.sub(r'\s+(مترجم|HD|اون لاين).*$', '', title)
        title = title.strip()
        
        if title:
            # Use add_dir to navigate to links page (not playable directly)
            site.add_dir(title, video_url, 'getLinks', image)
    
    # Pagination - look for next page link with &raquo; or page number
    # Pattern 1: Link with &raquo; (»)
    next_match = re.search(r'<a[^>]+href="([^"]*page=\d+[^"]*)"[^>]*>&raquo;', html, re.IGNORECASE)
    
    # Pattern 2: Look for "التالي" (Next in Arabic)
    if not next_match:
        next_match = re.search(r'<a[^>]+href="([^"]*page=\d+[^"]*)"[^>]*>التالي', html, re.IGNORECASE)
    
    # Pattern 3: Find current page and look for next page number
    if not next_match:
        current_page = 1
        page_match = re.search(r'page=(\d+)', url)
        if page_match:
            current_page = int(page_match.group(1))
        
        # Look for next page link
        next_page_pattern = rf'href="([^"]*page={current_page + 1}[^"]*)"'
        next_match = re.search(next_page_pattern, html)
    
    if next_match:
        next_url = next_match.group(1)
        if not next_url.startswith('http'):
            next_url = f'{site.url}/{next_url}'
        utils.kodilog(f'{site.title}: Next page URL: {next_url}')
        site.add_dir('Next Page', next_url, 'getVideos', addon_image(site.img_next))
    
    utils.eod(content='videos')


@site.register()
def getLinks(url, name=''):
    """Extract video links from page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    headers = {'User-Agent': utils.USER_AGENT}
    html = utils.getHtml(url, headers=headers)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Extract video ID
    vid_match = re.search(r'vid=([a-zA-Z0-9]+)', url)
    if not vid_match:
        utils.notify(site.title, 'لم يتم العثور على معرف الفيديو', icon=site.image)
        utils.eod(content='videos')
        return
    
    video_id = vid_match.group(1)
    
    # Get embed page to find streaming URL
    embed_url = f'{site.url}/embed.php?vid={video_id}'
    utils.kodilog(f'{site.title}: Fetching embed page: {embed_url}')
    
    embed_html = utils.getHtml(embed_url, headers=headers)
    
    if not embed_html:
        utils.notify(site.title, 'لم يتم تحميل صفحة التضمين', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Find iframe sources in embed page
    iframe_pattern = r'<iframe[^>]+src="([^"]+)"'
    iframes = re.findall(iframe_pattern, embed_html)
    
    utils.kodilog(f'{site.title}: Found {len(iframes)} iframes')
    
    hoster_manager = get_hoster_manager()
    
    for iframe_url in iframes:
        # Skip ad-related iframes
        if 'ads' in iframe_url.lower() or 'Date.now()' in iframe_url:
            utils.kodilog(f'{site.title}: Skipping ad iframe: {iframe_url[:50]}')
            continue
        
        iframe_url = iframe_url.strip()
        utils.kodilog(f'{site.title}: Processing iframe: {iframe_url}')
        
        # Format link with resolver icons
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            iframe_url,
            site.title,
            name,
            quality='HD'
        )
        
        utils.kodilog(f'{site.title}: Label={label}, should_skip={should_skip}')
        
        if not should_skip:
            utils.kodilog(f'{site.title}: Adding link to list')
            basics.addDownLink(label, iframe_url, 'larozza.PlayVid', site.image)
            utils.kodilog(f'{site.title}: Link added successfully')
        else:
            # If filtered, still add with basic label (user may want to try)
            hoster_name = iframe_url.split('/')[2] if '/' in iframe_url else 'Unknown'
            basic_label = f'{site.title} | {hoster_name}'
            utils.kodilog(f'{site.title}: Adding unfiltered link: {basic_label}')
            basics.addDownLink(basic_label, iframe_url, 'larozza.PlayVid', site.image)
    
    utils.kodilog(f'{site.title}: Calling eod()')
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
