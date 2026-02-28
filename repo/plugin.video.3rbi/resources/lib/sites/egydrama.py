# -*- coding: utf-8 -*-
"""
EgyDrama Site Module
https://v.egydrama.com/
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('egydrama', 'EgyDrama', url=None, image='sites/egydrama.png')


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon
    
    # TV Shows
    site.add_dir('Ramadan TV Shows', site.url + '/category.php?cat=ramadan-2026', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + '/category.php?cat=arabic-series', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + '/category.php?cat=series-turkish-2022', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('English TV Shows', site.url + '/category.php?cat=series-english-2023', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('Indian TV Shows', site.url + '/category.php?cat=indian-series', 'getTVShows', get_category_icon('Indian TV Shows'))
    site.add_dir('Korean TV Shows', site.url + '/category.php?cat=koryan-series', 'getTVShows', get_category_icon('Korean TV Shows'))
    site.add_dir('Cartoon TV Shows', site.url + '/category.php?cat=animation-series-2023', 'getTVShows', get_category_icon('Cartoon TV Shows'))
    
    # Movies
    site.add_dir('Arabic Movies', site.url + '/category.php?cat=aflam-3araby', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('English Movies', site.url + '/category.php?cat=english-movies', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Indian Movies', site.url + '/category.php?cat=indian-movies', 'getMovies', get_category_icon('Indian Movies'))
    
    # Search
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    
    utils.eod()


@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if search_text:
        search_url = site.url + '/?s=' + search_text
        getTVShows(search_url)


@site.register()
def getTVShows(url):
    """Get TV shows by deduplicating flattened episodes"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting TV shows from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='tvshows')
        return
    
    # Pattern for video items with data-echo for lazy-loaded images
    episode_pattern = r'<li class="col-xs-6[^>]*>.*?<a href="([^"]*watch[^"]*)"[^>]*>.*?data-echo="([^"]+)"[^>]*alt="([^"]+)"'
    episode_matches = re.findall(episode_pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(episode_matches)} items')
    
    # Deduplicate episodes into shows
    shows = {}
    for ep_url, img, title in episode_matches:
        original_title = title
        title = utils.cleantext(title)
        
        # Extract show name by removing episode/season markers
        # First, normalize Arabic numerals to standard digits for processing
        arabic_numerals = '٠١٢٣٤٥٦٧٨٩'
        standard_numerals = '0123456789'
        title_normalized = title
        for ar, std in zip(arabic_numerals, standard_numerals):
            title_normalized = title_normalized.replace(ar, std)
        
        # Clean common prefixes
        show_name = re.sub(r'^\s*مسلسل\s+', '', title_normalized).strip()
        show_name = re.sub(r'\s*مترجم\s*', ' ', show_name).strip()
        show_name = re.sub(r'\s*مدبلج\s*', ' ', show_name).strip()
        show_name = re.sub(r'\s*مشاهدة\s*', ' ', show_name).strip()
        show_name = re.sub(r'\s*اون لاين\s*', ' ', show_name).strip()
        
        # Remove season markers - various formats
        # "الموسم 1", "م1", "S1", "S01", " season 1", etc.
        show_name = re.sub(r'\s+الموسم\s*\d+', '', show_name).strip()
        show_name = re.sub(r'\s+م\d+', '', show_name).strip()
        show_name = re.sub(r'\s+[Ss]\d+\s*$', '', show_name).strip()
        
        # Remove episode markers - handle "الحلقة" and typos like "اللقة"
        # Also handle "الحلقة 1", "ح1", "الحلقة الاولى", etc.
        show_name = re.sub(r'\s+الحلقة\s+\d+.*$', '', show_name).strip()
        show_name = re.sub(r'\s+اللقة\s+\d+.*$', '', show_name).strip()  # Handle typo
        show_name = re.sub(r'\s+ح\d+.*$', '', show_name).strip()
        
        # Remove episode number words (ordinal numbers in Arabic)
        # This pattern removes from episode word to end of string
        show_name = re.sub(r'\s+(الحلقة|اللقة|حلقة)\s+(الاولى|الثانية|الثالثة|الرابعة|الخامسة|السادسة|السابعة|الثامنة|التاسعة|العاشرة|الحادية عشر|الثانية عشر|الثالثة عشر|الرابعة عشر|الخامسة عشر|السادسة عشر|السابعة عشر|الثامنة عشر|التاسعة عشر|العشرون|الحادية والعشرون|الثانية والعشرون|الثالثة والعشرون|الرابعة والعشرون|الخامسة والعشرون|السادسة والعشرون|السابعة والعشرون|الثامنة والعشرون|التاسعة والعشرون|الثلاثون|التاسعة والأربعون|الحادية والأربعون|الثانية والأربعون|الثالثة والأربعون|الرابعة والأربعون|الخامسة والأربعون|السادسة والأربعون|السابعة والأربعون|الثامنة والأربعون|التاسعة والأربعون|الخمسون|الحادية والخمسون|الثانية والخمسون|الثالثة والخمسون|الرابعة والخمسون|الخامسة والخمسون|السادسة والخمسون|السابعة والخمسون|الثامنة والخمسون|التاسعة والخمسون|الستون|الحادية والستون|الثانية والستون|الثالثة والستون|الرابعة والستون|الخامسة والستون|السادسة والستون|السابعة والستون|الثامنة والستون|التاسعة والستون|السبعون|الحادية والسبعون|الثانية والسبعون|الثالثة والسبعون|الرابعة والسبعون|الخامسة والسبعون|السادسة والسبعون|السابعة والسبعون|الثامنة والسبعون|التاسعة والسبعون|الثمانون|الحادية والثمانون|الثانية والثمانون|الثالثة والثمانون|الرابعة والثمانون|الخامسة والثمانون|السادسة والثمانون|السابعة والثمانون|الثامنة والثمانون|التاسعة والثمانون|التسعون|الحادية والتسعون|الثانية والتسعون|الثالثة والتسعون|الرابعة والتسعون|الخامسة والتسعون|السادسة والتسعون|السابعة والتسعون|الثامنة والتسعون|التاسعة والتسعون|المائة|الحادية والمائة|الثانية والمائة|الثالثة والمائة|الرابعة والمائة|الخامسة والمائة|السادسة والمائة|السابعة والمائة|الثامنة والمائة|التاسعة والمائة|الحادية عشرة والمائة|الثانية عشرة والمائة|الثالثة عشرة والمائة|الرابعة عشرة والمائة|الخامسة عشرة والمائة|السادسة عشرة والمائة|السابعة عشرة والمائة|الثامنة عشرة والمائة|التاسعة عشرة والمائة|العشرون والمائة|الحادية والعشرون والمائة|الثانية والعشرون والمائة|الثالثة والعشرون والمائة|الرابعة والعشرون والمائة|الخامسة والعشرون والمائة|السادسة والعشرون والمائة|السابعة والعشرون والمائة|الثامنة والعشرون والمائة|التاسعة والعشرون والمائة|الثلاثون والمائة|الحادية والثلاثون والمائة|الثانية والثلاثون والمائة|الثالثة والثلاثون والمائة|الرابعة والثلاثون والمائة|الخامسة والثلاثون والمائة|السادسة والثلاثون والمائة|السابعة والثلاثون والمائة|الثامنة والثلاثون والمائة|التاسعة والثلاثون والمائة|الاربعون والمائة|الحادية والاربعون والمائة|الثانية والاربعون والمائة|الثالثة والاربعون والمائة|الرابعة والاربعون والمائة|الخامسة والاربعون والمائة|السادسة والاربعون والمائة|السابعة والاربعون والمائة|الثامنة والاربعون والمائة|التاسعة والاربعون والمائة|الخمسون والمائة|الحادية والخمسون والمائة|الثانية والخمسون والمائة|الثالثة والخمسون والمائة|الرابعة والخمسون والمائة|الخامسة والخمسون والمائة|السادسة والخمسون والمائة|السابعة والخمسون والمائة|الثامنة والخمسون والمائة|التاسعة والخمسون والمائة|الستون والمائة|الحادية والستون والمائة|الثانية والستون والمائة|الثالثة والستون والمائة|الرابعة والستون والمائة|الخامسة والستون والمائة|السادسة والستون والمائة|السابعة والستون والمائة|الثامنة والستون والمائة|التاسعة والستون والمائة|السبعون والمائة|الحادية والسبعون والمائة|الثانية والسبعون والمائة|الثالثة والسبعون والمائة|الرابعة والسبعون والمائة|الخامسة والسبعون والمائة|السادسة والسبعون والمائة|السابعة والسبعون والمائة|الثامنة والسبعون والمائة|التاسعة والسبعون والمائة|الثمانون والمائة|الحادية والثمانون والمائة|الثانية والثمانون والمائة|الثالثة والثمانون والمائة|الرابعة والثمانون والمائة|الخامسة والثمانون والمائة|السادسة والثمانون والمائة|السابعة والثمانون والمائة|الثامنة والثمانون والمائة|التاسعة والثمانون والمائة|التسعون والمائة|الحادية والتسعون والمائة|الثانية والتسعون والمائة|الثالثة والتسعون والمائة|الرابعة والتسعون والمائة|الخامسة والتسعون والمائة|السادسة والتسعون والمائة|السابعة والتسعون والمائة|الثامنة والتسعون والمائة|التاسعة والتسعون والمائة|المائتان|الثالثمائة|الرابعمائة|الخامسمائة|السادسمائة|السابعمائة|الثامنمائة|التاسعمائة).*', '', show_name).strip()
        
        # Remove any remaining parenthetical content
        show_name = re.sub(r'\s*\([^)]*\)\s*', ' ', show_name).strip()
        
        # NOTE: Do NOT remove trailing numbers - they might be season numbers like "مدينة البعيدة 2"
        # The episode patterns above with \$ anchor already handle episode numbers properly
        
        # Clean up multiple spaces
        show_name = re.sub(r'\s+', ' ', show_name).strip()
        
        if show_name and show_name not in shows:
            # Make image URL absolute
            if img.startswith('//'):
                img = 'https:' + img
            elif not img.startswith('http'):
                img = site.url.rstrip('/') + '/' + img
            
            shows[show_name] = {'url': ep_url, 'img': img, 'original': original_title}
            utils.kodilog(f'{site.title}: Dedup: "{original_title}" -> "{show_name}" | URL: {ep_url}')
    
    # Add deduplicated shows
    for show_name, data in shows.items():
        utils.kodilog(f'{site.title}: Adding show dir: "{show_name}" -> URL: {data["url"]}')
        site.add_dir(show_name, data['url'], 'getSeasons', data['img'], media_type='tvshow')
    
    # Pagination
    current_page = re.search(r'[&?]page=(\d+)', url)
    current = int(current_page.group(1)) if current_page else 1
    next_page_num = current + 1
    
    next_match = re.search(rf'<a[^>]+href="([^"]*page={next_page_num}[^"]*)"', html)
    if next_match:
        next_url = next_match.group(1)
        if not next_url.startswith('http'):
            next_url = site.url.rstrip('/') + '/' + next_url
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')


@site.register()
def getMovies(url):
    """Get movies listing (no deduplication needed)"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='movies')
        return
    
    # Pattern for video items
    movie_pattern = r'<li class="col-xs-6[^>]*>.*?<a href="([^"]*watch[^"]*)"[^>]*>.*?data-echo="([^"]+)"[^>]*alt="([^"]+)"'
    movie_matches = re.findall(movie_pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(movie_matches)} movies')
    
    for mov_url, img, title in movie_matches:
        title = utils.cleantext(title)
        title = re.sub(r'فيلم|مترجم|مشاهدة|اون لاين', '', title).strip()
        
        # Make image URL absolute
        if img.startswith('//'):
            img = 'https:' + img
        elif not img.startswith('http'):
            img = site.url.rstrip('/') + '/' + img
        
        if title:
            site.add_dir(title, mov_url, 'getLinks', img, media_type='movie')
    
    # Pagination
    current_page = re.search(r'[&?]page=(\d+)', url)
    current = int(current_page.group(1)) if current_page else 1
    next_page_num = current + 1
    
    next_match = re.search(rf'<a[^>]+href="([^"]*page={next_page_num}[^"]*)"', html)
    if next_match:
        next_url = next_match.group(1)
        if not next_url.startswith('http'):
            next_url = site.url.rstrip('/') + '/' + next_url
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')


@site.register()
def getSeasons(url, name=''):
    """Parse seasons from episode page"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting seasons from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='seasons')
        return
    
    # Extract actual show title from the page (to fix site data issues)
    title_match = re.search(r'<h1[^>]*>(.*?)</h1>', html)
    if title_match:
        actual_title = title_match.group(1)
        actual_title = re.sub(r'<[^>]+>', '', actual_title)  # Remove HTML tags
        actual_title = utils.cleantext(actual_title)
        # Clean up the title
        actual_title = re.sub(r'مسلسل|مترجم|مدبلج|مشاهدة|اون لاين', '', actual_title).strip()
        # Remove episode info to get show name
        actual_title = re.sub(r'\s+الحلقة\s+.*', '', actual_title).strip()
        utils.kodilog(f'{site.title}: Actual show title from page: {actual_title}')
    
    # Extract poster from pm_video_data
    thumb_match = re.search(r'thumb_url\s*:\s*["\']([^"\']+)["\']', html)
    poster_url = thumb_match.group(1) if thumb_match else site.image
    
    # Parse season divs: <div id="Season1" class="tabcontent">
    season_pattern = r'<div[^>]*id="(Season\d+)"[^>]*class="[^"]*tabcontent[^"]*"'
    season_matches = re.findall(season_pattern, html)
    
    utils.kodilog(f'{site.title}: Found {len(season_matches)} season divs')
    
    if season_matches:
        for season_id in season_matches:
            # Extract season number from Season1, Season2, etc.
            season_num = re.search(r'Season(\d+)', season_id)
            if season_num:
                season_name = f'موسم {season_num.group(1)}'
            else:
                season_name = season_id
            
            # Encode season ID in URL as query parameter
            # This ensures it gets passed to getEpisodes via the URL
            url_with_season = url + ('&' if '?' in url else '?') + 'season_id=' + season_id
            
            # Pass both URL (with season encoded) and season_id
            site.add_dir(season_name, url_with_season, 'getEpisodes', poster_url, 
                        season=season_id, media_type='season')
    else:
        # No seasons found, might be a single season - go directly to links
        utils.kodilog(f'{site.title}: No seasons found, going directly to links')
        getLinks(url, name)
        return
    
    utils.eod(content='seasons')


@site.register()
def getEpisodes(url, season='', name=''):
    """Parse episodes from season tab on episode page"""
    # Extract season_id from URL if present (added by getSeasons)
    season_id_match = re.search(r'season_id=([^&]+)', url)
    if season_id_match:
        season = season_id_match.group(1)
        # Remove season_id from URL to clean it up
        url = re.sub(r'[?&]season_id=[^&]+', '', url)
    
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting episodes for season [{season}] from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='episodes')
        return
    
    # Extract poster
    thumb_match = re.search(r'thumb_url\s*:\s*["\']([^"\']+)["\']', html)
    poster_url = thumb_match.group(1) if thumb_match else site.image
    
    # Parse episodes from season div
    if season:
        # More robust pattern to find season div - handles different attribute orders
        # The div has id="Season1" class="tabcontent" and contains <ul class="s">
        season_div_pattern = rf'<div[^>]*id=["\']{re.escape(season)}["\'][^>]*class=["\'][^"\']*tabcontent[^"\']*["\'][^>]*>(.*?)</div>\s*<div'
        season_match = re.search(season_div_pattern, html, re.DOTALL)
        
        # If that fails, try alternative pattern (id and class in different order)
        if not season_match:
            season_div_pattern = rf'<div[^>]*id=["\']{re.escape(season)}["\'][^>]*>(.*?)</div>\s*<div'
            season_match = re.search(season_div_pattern, html, re.DOTALL)
        
        # If still fails, try simpler pattern without following div constraint
        if not season_match:
            season_div_pattern = rf'<div[^>]*id=["\']{re.escape(season)}["\'][^>]*>(.*?)</div>'
            season_match = re.search(season_div_pattern, html, re.DOTALL)
        
        utils.kodilog(f'{site.title}: Season div match found: {season_match is not None}')
        
        if season_match:
            season_html = season_match.group(1)
            # Find all <a> tags with href containing "watch.php"
            a_pattern = r'<a[^>]*href=["\']([^"\']*watch\.php[^"\']*)["\'][^>]*>'
            a_tags = re.findall(a_pattern, season_html)
            
            utils.kodilog(f'{site.title}: Found {len(a_tags)} episode links in {season}')
            
            # Also extract titles and episode numbers
            # Pattern matches: <a href="..." title="...">...<li>...<em>NUMBER</em>
            # Uses lookahead to handle any attribute order
            full_pattern = r'<a(?=[^>]*href=["\']([^"\']*watch\.php[^"\']*)["\'])(?=[^>]*title=["\']([^"\']+)["\'])[^>]*>.*?<li[^>]*>.*?<em>(\d+)</em>'
            episode_matches = re.findall(full_pattern, season_html, re.DOTALL)
            
            utils.kodilog(f'{site.title}: Found {len(episode_matches)} episodes with full details')
            
            episode_count = 0
            for ep_url, ep_title, ep_num in episode_matches:
                # Clean title
                display_title = utils.cleantext(ep_title)
                display_title = re.sub(r'مسلسل|مترجم|مشاهدة|اون لاين', '', display_title).strip()
                
                # Make URL absolute
                if not ep_url.startswith('http'):
                    ep_url = site.url.rstrip('/') + '/' + ep_url
                
                site.add_dir(display_title, ep_url, 'getLinks', poster_url, 
                            episode=ep_num, media_type='episode')
                episode_count += 1
            
            utils.kodilog(f'{site.title}: Added {episode_count} episodes')
        else:
            utils.kodilog(f'{site.title}: Could not find div for season {season}')
    
    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract video links from watch page"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'No video links found', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Extract poster from pm_video_data
    thumb_match = re.search(r'thumb_url\s*:\s*["\']([^"\']+)["\']', html)
    poster_url = thumb_match.group(1) if thumb_match else site.image
    
    # Extract uniq_id for embed
    uniq_match = re.search(r'uniq_id\s*:\s*["\']([^"\']+)["\']', html)
    uniq_id = uniq_match.group(1) if uniq_match else None
    
    hoster_manager = get_hoster_manager()
    
    # Fetch embed page to get actual iframes
    if uniq_id:
        embed_url = f'https://v.egydrama.com/embed.php?vid={uniq_id}'
        utils.kodilog(f'{site.title}: Fetching embed: {embed_url}')
        
        embed_html = utils.getHtml(embed_url, headers={'User-Agent': utils.USER_AGENT})
        
        if embed_html:
            # Extract iframe sources from embed page
            iframe_sources = re.findall(r'<iframe[^>]+src="([^"]+)"', embed_html)
            utils.kodilog(f'{site.title}: Found {len(iframe_sources)} iframes')
            
            # Filter out problematic/spam hosters
            blocked_hosters = ['vk.com', 'vkvd', 'ok.ru', 'odnoklassniki']
            filtered_sources = []
            for src in iframe_sources:
                if not any(blocked in src.lower() for blocked in blocked_hosters):
                    filtered_sources.append(src)
                    utils.kodilog(f'{site.title}: Adding source: {src[:80]}')
                else:
                    utils.kodilog(f'{site.title}: Skipping blocked hoster: {src[:60]}')
            
            utils.kodilog(f'{site.title}: Using {len(filtered_sources)} filtered sources')
            
            for iframe_src in filtered_sources:
                iframe_src = iframe_src.replace('&amp;', '&')
                
                label, should_skip = utils.format_resolver_link(
                    hoster_manager,
                    iframe_src,
                    site.title,
                    name,
                    quality='HD'
                )
                
                if not should_skip:
                    site.add_download_link(label, iframe_src, 'PlayVid', poster_url, 
                                          desc=name, quality='HD')
                else:
                    # Add anyway with direct label
                    hoster_name = iframe_src.split('/')[2] if '/' in iframe_src else 'Unknown'
                    site.add_download_link(hoster_name, iframe_src, 'PlayVid', poster_url, 
                                          desc=name, quality='HD')
    
    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    utils.kodilog(f'{site.title}: Resolving URL: {url[:100]}')
    
    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result and result.get('url'):
        video_url = result['url']
        
        utils.kodilog(f'{site.title}: Resolved to: {video_url[:100]}')
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'فشل تشغيل الفيديو', icon=site.image)
