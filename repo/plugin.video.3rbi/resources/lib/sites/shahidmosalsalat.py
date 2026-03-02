# -*- coding: utf-8 -*-
"""
ShahidMosalsalat Site Module
https://v5.shahidmosalsalat.business

Flow: Category → TV Shows (deduplicated) → Episodes Page → getLinks
"""

import re
from resources.lib import utils
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from six.moves import urllib_parse

site = SiteBase('shahidmosalsalat', 'Shahid Mosalsalat', url=None, image='sites/ShahidMosalsalat.png')


@site.register(default_mode=True)
def Main():
    """Main menu - extracted from homepage navigation"""
    from resources.lib.category_mapper import get_category_icon
    
    # Search
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    
    # TV Shows - Arabic
    site.add_dir('Arabic Series', site.url + '/category.php?cat=3-arabic-series3', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Egyptian Series', site.url + '/category.php?cat=2-arabic-series-egyptian', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Levantine Series', site.url + '/category.php?cat=moslsalt-shamy', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Gulf Series', site.url + '/category.php?cat=moslsalt-kalegy', 'getTVShows', get_category_icon('Arabic TV Shows'))
    
    # TV Shows - Foreign
    site.add_dir('Turkish Series', site.url + '/category.php?cat=1-series-turkish-2025', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Turkish Dubbed', site.url + '/category.php?cat=turkish-dubbed-series', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Foreign Series 2026', site.url + '/category.php?cat=1-series-english-2025', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('Foreign Dubbed', site.url + '/category.php?cat=dubbed-foreign-series', 'getTVShows', get_category_icon('English TV Shows'))
    
    # Movies
    site.add_dir('Arabic Movies', site.url + '/category.php?cat=5-aflam-3araby1', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Indian Movies', site.url + '/category.php?cat=2-indian-movies3', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('English Movies', site.url + '/category.php?cat=3-english-movies3', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Asian Movies', site.url + '/category.php?cat=asian-movies', 'getMovies', get_category_icon('Asian Movies'))
    site.add_dir('Turkish Movies', site.url + '/category.php?cat=turkish-movies', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Foreign Dubbed Movies', site.url + '/category.php?cat=dubbed-foreign-movies', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Indian Dubbed Movies', site.url + '/category.php?cat=dubbed-indian-movies', 'getMovies', get_category_icon('Indian Movies'))
    
    # Ramadan
    site.add_dir('Ramadan 2026', site.url + '/category.php?cat=ramadan-2026', 'getTVShows', get_category_icon('Ramadan'))
    
    utils.eod()


@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if search_text:
        search_url = site.url + '/search.php?keywords=' + urllib_parse.quote(search_text)
        # Search returns mixed results - use getTVShows which handles both
        getTVShows(search_url, is_search=True)


@site.register()
def getTVShows(url, is_search=False):
    """Get TV shows listing
    
    Category pages show flattened episodes. We deduplicate by show name
    and pass the first episode URL which contains all episodes.
    """
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    # Extract category from URL for filtering
    cat_match = re.search(r'cat=([^&]+)', url)
    current_cat = cat_match.group(1) if cat_match else ''
    
    utils.kodilog(f'{site.title}: Getting TV shows from: {url}, cat={current_cat}')
    html = utils._getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='tvshows')
        return

    # Search results page: links are watch.php?vid= episode links with title= attribute
    # Deduplicate by show name (strip episode markers) and emit one folder per show
    if is_search:
        ep_links = re.findall(r'href="(https?://[^"]+watch\.php\?vid=[^"]+)"[^>]+title="([^"]+)"', html)
        utils.kodilog(f'{site.title}: Search found {len(ep_links)} episode links')
        seen = {}
        for ep_url, title in ep_links:
            title = utils.cleantext(title)
            show_name = re.sub(r'\s*ح\s*\d+\s*', ' ', title).strip()
            show_name = re.sub(r'\s*م\s*\d+\s*', ' ', show_name).strip()
            show_name = re.sub(r'\s+', ' ', show_name).strip()
            if not show_name:
                continue
            if show_name not in seen:
                seen[show_name] = ep_url
        for show_name, ep_url in seen.items():
            site.add_dir(show_name, ep_url, 'getEpisodes', site.image, media_type='tvshow')
        utils.eod(content='tvshows')
        return

    # Pattern 1: series-mini-icon (proper series with posters) - always include these
    series_pattern = r'<div class="series-mini-icon[^>]*>.*?<a href="([^"]+)"[^>]+title="([^"]+)"[^>]*>.*?<img[^>]+src="([^"]+)"'
    series_matches = re.findall(series_pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(series_matches)} series with posters')
    
    for item_url, title, img in series_matches:
        title = utils.cleantext(title)
        title = re.sub(r'مسلسل|مترجم|اون لاين', '', title).strip()
        
        if img.startswith('//'):
            img = 'https:' + img
        elif not img.startswith('http'):
            img = site.url.rstrip('/') + '/' + img
        
        # Direct to episodes page
        site.add_dir(title, item_url, 'getEpisodes', img, media_type='tvshow')
    
    # Pattern 2: icon-link1 (flattened episodes) - filter by category to avoid duplicates
    # Only parse the main mosalsal-footer section, not recommended sections
    footer_match = re.search(r'<div class="mosalsal-footer" id="mosalsal-footer">(.*?)</div>\s*</div>\s*<br', html, re.DOTALL)
    if footer_match:
        footer_html = footer_match.group(1)
    else:
        footer_html = html  # Fallback to full HTML
    
    # Extract episodes with posters from style attribute
    # Pattern: icon-link1 with --bg-image in style attribute (flexible attribute order)
    episode_pattern = r'<a href="([^"]+)" class="icon-link1[^"]*"[^>]*data-vid="([^"]+)"[^>]*data-categories="([^"]*)"[^>]*title="([^"]+)"[^>]*style="[^"]*--bg-image: url\(&quot;([^"]+?)&quot;\)[^"]*"[^>]*>([^<]+)</a>'
    episode_matches = re.findall(episode_pattern, footer_html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(episode_matches)} episodes in footer')
    
    # Deduplicate by show name, filtering by category
    seen_shows = {}
    
    for ep_url, vid, categories, title, poster_url, text in episode_matches:
        # Filter by category if we have one
        if current_cat and categories:
            # Check if current category is in the data-categories
            cat_list = categories.split(',')
            # Map URL category to data-category
            cat_mapping = {
                '3-arabic-series3': ['ramadan30', 'ramadan15', 'egypt', 'shami', 'gulf'],
                '2-arabic-series-egyptian': ['egypt'],
                'moslsalt-shamy': ['shami'],
                'moslsalt-kalegy': ['gulf'],
                '1-series-turkish-2025': ['turkish', 'sub', 'dub'],
                'turkish-dubbed-series': ['turkish', 'dub'],
            }
            relevant_cats = cat_mapping.get(current_cat, [current_cat])
            if not any(c in cat_list for c in relevant_cats):
                continue
        
        title = utils.cleantext(title)
        
        # Strip episode/season markers to get show name
        show_name = re.sub(r'\s*ح\d+\s*', ' ', title).strip()
        show_name = re.sub(r'\s*م\d+\s*', ' ', show_name).strip()
        show_name = re.sub(r'\s+', ' ', show_name).strip()
        
        if not show_name:
            show_name = title
        
        if show_name not in seen_shows:
            seen_shows[show_name] = {
                'url': ep_url,
                'poster': poster_url,  # Store poster from first episode
                'count': 1
            }
        else:
            seen_shows[show_name]['count'] += 1
    
    # Add deduplicated shows with posters
    for show_name, data in seen_shows.items():
        count = data['count']
        display_title = f"{show_name} ({count} حلقات)" if count > 1 else show_name
        
        # Use poster from data (extracted from style attribute)
        poster = data.get('poster', site.image)
        
        # Make poster URL absolute if needed
        if poster and poster != site.image:
            if poster.startswith('//'):
                poster = 'https:' + poster
            elif not poster.startswith('http'):
                poster = site.url.rstrip('/') + '/' + poster
        
        site.add_dir(display_title, data['url'], 'getEpisodes', poster, media_type='tvshow')
    
    # Pagination
    next_match = re.search(r'<a[^>]+href="([^"]*page=\d+[^"]*)"[^>]*>&raquo;</a>', html)
    if not next_match:
        current_page = re.search(r'[&?]page=(\d+)', url)
        current = int(current_page.group(1)) if current_page else 1
        next_match = re.search(rf'<a[^>]+href="([^"]*[&?]page={current+1}[^"]*)"', html)
    
    if next_match:
        next_url = next_match.group(1)
        if not next_url.startswith('http'):
            next_url = site.url.rstrip('/') + '/' + next_url
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')


@site.register()
def getMovies(url):
    """Get movies listing - same structure as episodes on this site"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    # Use _getHtml directly to bypass cache (site has dynamic content)
    html = utils._getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='movies')
        return
    
    # Movies use icon-link1 pattern (same as episodes)
    movie_pattern = r'<a href="([^"]+)" class="icon-link1"[^>]+data-vid="([^"]+)"[^>]+title="([^"]+)"[^>]*>([^<]+)</a>'
    movie_matches = re.findall(movie_pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(movie_matches)} movie items')
    
    if movie_matches:
        for mov_url, vid, title, text in movie_matches:
            title = utils.cleantext(title)
            # Clean movie title
            title = re.sub(r'فيلم|مترجم|اون لاين|مشاهدة', '', title).strip()
            
            # Extract year if present
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            display_title = title if title else text.strip()
            
            site.add_dir(display_title, mov_url, 'getLinks', site.image, 
                        year=year, media_type='movie')
    
    # Pagination
    current_page = re.search(r'page=(\d+)', url)
    current = int(current_page.group(1)) if current_page else 1
    next_page_link = re.search(rf'<a[^>]+href="([^"]*page={current+1}[^"]*)"', html)
    
    if next_page_link:
        next_url = next_page_link.group(1)
        if not next_url.startswith('http'):
            next_url = site.url.rstrip('/') + '/' + next_url
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')


@site.register()
def getEpisodes(url):
    """Get all episodes from a show page
    
    Episode pages contain all episodes as icon-link1 elements.
    Each episode link goes directly to getLinks for playback.
    """
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    html = utils._getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='episodes')
        return
    
    # Extract show title
    show_title = ''
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    if title_match:
        show_title = utils.cleantext(title_match.group(1))
        show_title = re.sub(r'مسلسل|مترجم|مشاهدة|حلقة|الحلقة', '', show_title).strip()
        show_title = re.sub(r'\s*ح\d+\s*', ' ', show_title).strip()
    
    # Extract all episodes
    episode_pattern = r'<a href="([^"]+)" class="icon-link1"[^>]+data-vid="([^"]+)"[^>]+title="([^"]+)"[^>]*>([^<]+)</a>'
    episode_matches = re.findall(episode_pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(episode_matches)} episodes')
    
    for ep_url, vid, title, text in episode_matches:
        # Extract episode number
        ep_num_match = re.search(r'ح(\d+)', text) or re.search(r'ح(\d+)', title)
        ep_num = ep_num_match.group(1) if ep_num_match else ''
        
        # Build display title
        if ep_num:
            display_title = f'{show_title} - حلقة {ep_num}' if show_title else f'حلقة {ep_num}'
        else:
            display_title = utils.cleantext(title) if title else text.strip()
        
        # Each episode goes directly to getLinks
        site.add_dir(display_title, ep_url, 'getLinks', site.image, 
                    episode=ep_num, media_type='episode')
    
    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract video links from watch page"""
    # Ensure absolute URL
    if not url.startswith('http'):
        url = site.url.rstrip('/') + '/' + url
    
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    html = utils._getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'No video links found', icon=site.image)
        utils.eod(content='videos')
        return
    
    # Extract poster from pm_video_data
    thumb_match = re.search(r'thumb_url\s*:\s*["\']([^"\']+)["\']', html)
    poster_url = thumb_match.group(1) if thumb_match else site.image
    
    # Extract uniq_id (used for cross-site embed)
    uniq_match = re.search(r'uniq_id\s*:\s*["\']([^"\']+)["\']', html)
    uniq_id = uniq_match.group(1) if uniq_match else None
    
    hoster_manager = get_hoster_manager()
    
    # Method 1: Use egydrama.com embed (same video ID works there)
    if uniq_id:
        egydrama_embed = f'https://v.egydrama.com/embed.php?vid={uniq_id}'
        utils.kodilog(f'{site.title}: Trying egydrama embed: {egydrama_embed}')
        
        # Fetch egydrama embed page to get actual iframes
        embed_html = utils._getHtml(egydrama_embed, headers={'User-Agent': utils.USER_AGENT})
        
        if embed_html:
            # Extract iframe sources from egydrama embed
            iframe_sources = re.findall(r'<iframe[^>]+src="([^"]+)"', embed_html)
            utils.kodilog(f'{site.title}: Found {len(iframe_sources)} iframes from egydrama')
            
            for iframe_src in iframe_sources:
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
    
    # Method 2: Try original embed_url as fallback
    embed_match = re.search(r'embed_url\s*:\s*["\']([^"\']+)["\']', html)
    if embed_match:
        embed_url = embed_match.group(1).replace('&amp;', '&')
        utils.kodilog(f'{site.title}: Found original embed URL: {embed_url}')
        
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            embed_url,
            site.title,
            name,
            quality='Embed'
        )
        
        if not should_skip:
            site.add_download_link(label, embed_url, 'PlayVid', poster_url, 
                                  desc=name, quality='Embed')
    
    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    utils.kodilog(f'{site.title}: Resolving URL: {url[:100]}')
    
    # Check if it's a direct MP4 URL
    if url.endswith('.mp4'):
        utils.kodilog(f'{site.title}: Direct MP4 URL')
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(url)
        return
    
    # Otherwise use hoster manager to resolve
    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result and result.get('url'):
        video_url = result['url']
        
        utils.kodilog(f'{site.title}: Resolved to: {video_url[:100]}')
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'Failed to resolve video', icon=site.image)
