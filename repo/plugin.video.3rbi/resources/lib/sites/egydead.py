# -*- coding: utf-8 -*-
"""
EgyDead Site Module
https://egydead.rip / https://w.egydead.live
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('egydead', 'EgyDead', url=None, image='sites/egydead.png')

@site.register(default_mode=True)
def Main():
    """Main menu"""
    # Movies categories
    site.add_dir('أفلام أجنبي', site.url + '/category/english-movies/', 'getMovies', site.image)
    site.add_dir('أفلام عربي', site.url + '/category/افلام-عربي/', 'getMovies', site.image)
    site.add_dir('أفلام تركية', site.url + '/category/افلام-تركية/', 'getMovies', site.image)
    site.add_dir('أفلام أسيوية', site.url + '/category/افلام-اسيوية/', 'getMovies', site.image)
    site.add_dir('أفلام مدبلجة', site.url + '/category/افلام-اجنبية-مدبلجة/', 'getMovies', site.image)
    site.add_dir('أفلام كرتون', site.url + '/category/افلام-كرتون/', 'getMovies', site.image)
    site.add_dir('أفلام هندية', site.url + '/category/افلام-هندية/', 'getMovies', site.image)
    site.add_dir('أفلام وثائقية', site.url + '/category/افلام-وثائقية/', 'getMovies', site.image)
    
    # Series categories
    site.add_dir('مسلسلات أجنبي', site.url + '/series-category/english-series/', 'getTVShows', site.image)
    site.add_dir('مسلسلات عربي', site.url + '/series-category/arabic-series/', 'getTVShows', site.image)
    site.add_dir('مسلسلات تركية', site.url + '/series-category/turkish-series/', 'getTVShows', site.image)
    site.add_dir('مسلسلات أسيوية', site.url + '/series-category/asian-series/', 'getTVShows', site.image)
    site.add_dir('مسلسلات لاتينية', site.url + '/series-category/latino-series/', 'getTVShows', site.image)
    site.add_dir('مسلسلات كرتون', site.url + '/series-category/cartoon-series/', 'getTVShows', site.image)
    
    # Search
    site.add_dir('بحث', '', 'search', site.image)
    
    utils.eod()

@site.register()
def search():
    """Search for content via AJAX endpoint"""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod()
        return
    
    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    
    # EgyDead uses AJAX endpoint for search
    search_url = site.url + '/wp-content/themes/egydeadc-taq/Ajax/live-search.php'
    post_data = f'search={search_text}'
    
    html = utils.getHtml(search_url, headers={'User-Agent': utils.USER_AGENT}, data=post_data, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No search results')
        utils.eod()
        return
    
    # Pattern for AJAX search results (liveItem)
    pattern = r'<div class="liveItem">\s*<a href="([^"]+)">\s*<img src="([^"]+)">\s*<h3>([^<]+)</h3>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} search results')
    
    if matches:
        for result_url, image, title in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مسلسل|انمي|مترجم|مترجمة|مدبلج|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Full-size image
            full_image = re.sub(r'-\d+x\d+', '', image)
            
            if title:
                # Route based on URL type
                if '/season/' in result_url or '/serie/' in result_url:
                    # TV show - show seasons first
                    site.add_dir(title, result_url, 'getSeasons', full_image,
                               year=year, media_type='tvshow')
                else:
                    # Movie - show video links
                    site.add_dir(title, result_url, 'getLinks', full_image,
                               year=year, media_type='movie')
    else:
        utils.notify(site.title, 'لا توجد نتائج', icon=site.image)
    
    utils.eod()

@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod()
        return
    
    # Pattern for movieItem - works for movies, series, and search
    pattern = r'<li class="movieItem">\s*<a href="([^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<h1 class="BottomTitle">([^<]+)</h1>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} movies')
    
    if matches:
        for movie_url, image, title in matches:
            # Skip episodes in movie listings
            if '/episode/' in movie_url:
                continue
            
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Try to get full-size image (remove thumbnail suffix)
            full_image = re.sub(r'-\d+x\d+', '', image)
            
            if title:
                # Detect if URL is for a series/season (route to getSeasons) or movie (route to getLinks)
                if '/season/' in movie_url or '/series/' in movie_url:
                    # This is a TV show - show seasons first
                    site.add_dir(title, movie_url, 'getSeasons', full_image, 
                               year=year, media_type='tvshow')
                else:
                    # This is a movie - show video links
                    site.add_dir(title, movie_url, 'getLinks', full_image, 
                               year=year, media_type='movie')
    
    # Pagination
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    utils.kodilog(f'{site.title}: Getting series from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod()
        return
    
    # Same pattern as movies
    pattern = r'<li class="movieItem">\s*<a href="([^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<h1 class="BottomTitle">([^<]+)</h1>'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} series')
    
    seen_titles = set()
    
    items_added = 0
    items_skipped_empty = 0
    items_skipped_duplicate = 0
    
    if matches:
        for series_url, image, title in matches:
            # Clean title
            original_title = title
            title = title.strip()
            title = re.sub(r'مشاهدة|مسلسل|انمي|مترجمة|مدبلجة|اون لاين|HD|كاملة', '', title).strip()
            title = re.sub(r'مترجم|مدبلج|كامل', '', title).strip()
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Extract episode number
            ep_num = ''
            ep_match = re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', title, re.IGNORECASE)
            if ep_match:
                ep_num = ep_match.group(1)
            
            # Convert Arabic season numbers to S notation
            title = re.sub(r'الموسم الأول', 'S1', title)
            title = re.sub(r'الموسم الثاني', 'S2', title)
            title = re.sub(r'الموسم الثالث', 'S3', title)
            title = re.sub(r'الموسم الرابع', 'S4', title)
            title = re.sub(r'الموسم الخامس', 'S5', title)
            title = re.sub(r'الموسم السادس', 'S6', title)
            title = re.sub(r'الموسم السابع', 'S7', title)
            title = re.sub(r'الموسم الثامن', 'S8', title)
            title = re.sub(r'الموسم التاسع', 'S9', title)
            title = re.sub(r'الموسم العاشر', 'S10', title)
            title = re.sub(r'الموسم الحادي عشر', 'S11', title)
            title = re.sub(r'الموسم الثاني عشر', 'S12', title)
            title = re.sub(r'الموسم الثالث عشر', 'S13', title)

            
            # Check if title became empty after cleaning
            if not title:
                items_skipped_empty += 1
                utils.kodilog(f'{site.title}: Empty title after cleaning: {original_title[:50]}')
                continue
            
            # Deduplicate by title
            if title in seen_titles:
                items_skipped_duplicate += 1
                continue
            seen_titles.add(title)
            
            # Try to get full-size image
            full_image = re.sub(r'-\d+x\d+', '', image)
            
            # Route based on URL type
            # Series categories can contain: seasons, episodes, or TV show pages
            if '/season/' in series_url:
                # Season page → getEpisodes
                site.add_dir(title, series_url, 'getEpisodes', full_image,
                           year=year, media_type='season')
            elif '/episode/' in series_url:
                # Direct episode → getLinks
                site.add_dir(title, series_url, 'getLinks', full_image,
                           year=year, episode=ep_num, media_type='episode')
            else:
                # TV show page → getSeasons
                site.add_dir(title, series_url, 'getSeasons', full_image,
                           year=year, media_type='tvshow')
            items_added += 1
    
    utils.kodilog(f'{site.title}: Added {items_added} items (skipped: {items_skipped_empty} empty, {items_skipped_duplicate} duplicates)')
    
    # Pagination
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getSeasons(url, name=''):
    """Get seasons for a TV show"""
    utils.kodilog(f'{site.title}: Getting seasons from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod()
        return
    
    # Extract main content only (before related-posts section)
    main_content_match = re.search(r'(.*?)<div[^>]*class="[^"]*related-posts', html, re.DOTALL | re.IGNORECASE)
    content = main_content_match.group(1) if main_content_match else html
    
    # Extract all items from main content
    pattern = r'<li class="movieItem">\s*<a href="([^"]+)"[^>]*>.*?<img src="([^"]+)"[^>]*>.*?<h1 class="BottomTitle">([^<]+)</h1>'
    all_items = re.findall(pattern, content, re.DOTALL)
    
    # Filter for seasons only (exclude current page and non-season URLs)
    seasons = [(u, i, t) for u, i, t in all_items if '/season/' in u and u != url]
    
    utils.kodilog(f'{site.title}: Found {len(seasons)} seasons')
    
    if seasons:
        for season_url, season_image, season_title in seasons:
            # Clean title
            season_title = season_title.strip()

            season_title = re.sub(r'مشاهدة|مسلسل|انمي|مترجمة|مدبلجة|اون لاين|HD|كاملة', '', season_title).strip()
            season_title = re.sub(r'مترجم|مدبلج|كامل', '', season_title).strip()
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', season_title)
            if year_match:
                year = year_match.group(1)
                season_title = season_title.replace(year, '').strip()
            
            # Full-size image
            full_image = re.sub(r'-\d+x\d+', '', season_image)
            
            if season_title:
                # Seasons route to getEpisodes
                site.add_dir(season_title, season_url, 'getEpisodes', full_image,
                           year=year, media_type='season')
    
    utils.eod()

@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a season"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod()
        return
    
    # Extract episodes-list section only (before seasons-list)
    episodes_section = re.search(r'<div class="episodes-list">(.*?)</div>\s*(?:<div class="seasons-list">|$)', html, re.DOTALL | re.IGNORECASE)
    
    if not episodes_section:
        utils.kodilog(f'{site.title}: No episodes-list section found')
        utils.eod()
        return
    
    # Pattern for episodes (simple <li><a> structure in episodes-list)
    pattern = r'<li>\s*<a href="([^"]+)"[^>]*>([^<]+)</a>\s*</li>'
    episodes = re.findall(pattern, episodes_section.group(1), re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')
    
    if episodes:
        for ep_url, ep_title in episodes:
            # Clean episode title
            ep_title = ep_title.strip()
            
            ep_title = re.sub(r'مشاهدة|مسلسل|انمي|مترجمة|مدبلجة|اون لاين|HD|كاملة', '', ep_title).strip()
            ep_title = re.sub(r'مترجم|مدبلج|كامل', '', ep_title).strip()
            # Extract episode number
            ep_num = ''
            ep_match = re.search(r'(?:حلقه|الحلقة|Episode|EP)\s*(\d+)', ep_title, re.IGNORECASE)
            if ep_match:
                ep_num = ep_match.group(1)
            
            # Use site image as placeholder (episodes don't have individual images)
            if ep_title:
                # All items from episodes-list go to getLinks
                site.add_dir(ep_title, ep_url, 'getLinks', site.image,
                           episode=ep_num, media_type='episode')
    
    # Pagination for episodes
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getEpisodes', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    """Extract video links from page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    # EgyDead requires POST with View=1 parameter to get video links
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, data='View=1', site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod()
        return
    
    hoster_manager = get_hoster_manager()
    
    # Pattern 1: data-link attribute
    server_pattern1 = r'<li data-link="([^"]+)"'
    servers1 = re.findall(server_pattern1, html)
    
    # Pattern 2: ser-link class
    server_pattern2 = r'class="ser-link" href="([^"]+)"'
    servers2 = re.findall(server_pattern2, html)
    
    # Combine both patterns
    all_servers = servers1 + servers2
    
    utils.kodilog(f'{site.title}: Found {len(all_servers)} servers')
    
    for i, server_url in enumerate(all_servers, 1):
        server_url = server_url.strip()
        
        # Fix protocol if needed
        if server_url.startswith('//'):
            server_url = 'https:' + server_url
        
        server_name = f'Server {i}'
        
        # Format link with resolver icons
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            server_url,
            site.title,
            name,
            quality=server_name
        )
        
        if not should_skip:
            basics.addDownLink(label, server_url, f'{site.name}.PlayVid', site.image)
    
    if not all_servers:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
    utils.eod()

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
