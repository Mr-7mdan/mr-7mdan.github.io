# -*- coding: utf-8 -*-
"""
ShoofVOD Site Module
"""

import re
from resources.lib import utils
from resources.lib.basics import addon, addon_image, aksvicon
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager, extract_iframe_sources

site = SiteBase('shoofvod', 'ShoofVOD', url=None, image='sites/shoofvod.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon
    
    site.add_dir('Search', site.url, 'search', get_category_icon('Search'))
    site.add_dir('Ramadan TV Shows', site.url + '/Cat-145-1', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    site.add_dir('English Movies', site.url + '/al_751319_1', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Arabic Movies', site.url + '/Cat-100-1', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Turkish Movies', site.url + '/Cat-48-1', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Indian Movies', site.url + '/Cat-132-1', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Anime Movies', site.url + '/Cat-57-1', 'getMovies', get_category_icon('Anime Movies'))
    site.add_dir('Documentary Movies', site.url + '/Cat-23-1', 'getMovies', get_category_icon('Documentary Movies'))
    site.add_dir('Arabic TV Shows', site.url + '/Cat-98-1', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + '/Cat-128-1', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Turkish TV Shows (Dubbed)', site.url + '/Cat-129-1', 'getTVShows', get_category_icon('Turkish TV Shows (Dubbed)'))
    site.add_dir('Indian TV Shows', site.url + '/Cat-130-1', 'getTVShows', get_category_icon('Indian TV Shows'))
    site.add_dir('Cartoon TV Shows', site.url + '/Cat-56-1', 'getTVShows', get_category_icon('Cartoon TV Shows'))
    site.add_dir('TV Programs', site.url + '/Cat-39-1', 'getTVShows', get_category_icon('TV Programs'))
    site.add_dir('Theater', site.url + '/Cat-44-1', 'getEpisodes', get_category_icon('Theater'))
    utils.eod()

@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        getMovies(site.url + '/Search/' + search_text)

@site.register()
def getMovies(url):
    html = utils.getHtml(url)
    
    # Pattern for movie entries
    # Format: <div class="col-md-3 col-sm-4 col-xs-4 col-xxs-6 item">...
    pattern = r'<div class="col-md-3 col-sm-4 col-xs-4 col-xxs-6 item">.+?<a href="([^"]+)">.+?<img src="([^"]+)" class.+?<div class="title"><h4>([^<]+)</h4></div>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for item_url, img, title in entries:
        # Clean title
        clean_title = utils.cleantext(title)
        clean_title = re.sub(r'(مشاهدة|مترجمة|مترجم|فيلم|مسلسل|مدبلج)', '', clean_title)
        clean_title = clean_title.replace('-', ' ').strip()
        
        # Extract year
        year = None
        year_match = re.search(r'(\d{4})', clean_title)
        if year_match:
            year = year_match.group(1)
            clean_title = clean_title.replace(year, '')
        
        clean_title = clean_title.strip()
        if year:
            clean_title += ' ({})'.format(year)
        
        full_url = site.url + item_url
        
        site.add_dir(clean_title, full_url, 'getLinks', img, fanart=img,
                    year=year, media_type='movie', original_title=title)
    
    # Check for next page
    next_match = re.search(r'<a href="([^"]+)" title="التالي">', html)
    if next_match:
        next_url = site.url + next_match.group(1)
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')

@site.register()
def getTVShows(url):
    html = utils.getHtml(url)
    
    # Pattern for TV show entries
    pattern = r'<div class="col-md-3 col-sm-4 col-xs-4 col-xxs-6 item">.+?<a href="([^"]+)">.+?<img src="([^"]+)" class.+?<div class="title"><h4>([^<]+)</h4></div>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for item_url, img, title in entries:
        # Clean title
        clean_title = utils.cleantext(title)
        clean_title = re.sub(r'(مشاهدة|مترجمة|مترجم|مسلسل|مدبلج)', '', clean_title)
        clean_title = clean_title.replace('-', ' ').strip()
        
        # Extract year
        year = None
        year_match = re.search(r'(\d{4})', clean_title)
        if year_match:
            year = year_match.group(1)
            clean_title = clean_title.replace(year, '')
        
        clean_title = clean_title.strip()
        
        full_url = site.url + item_url
        
        site.add_dir(clean_title, full_url, 'getEpisodes', img, fanart=img,
                    year=year, media_type='tvshow', original_title=title)
    
    # Check for next page
    next_match = re.search(r'<a href="([^"]+)" title="التالي">', html)
    if next_match:
        next_url = site.url + next_match.group(1)
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')

@site.register()
def getEpisodes(url):
    html = utils.getHtml(url)
    
    # Extract show info
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None
    if show_title:
        show_title = re.sub(r'(مشاهدة|مسلسل|مترجم|مترجمة)', '', show_title).strip()
    
    # Extract year
    year = None
    if show_title:
        year_match = re.search(r'(\d{4})', show_title)
        if year_match:
            year = year_match.group(1)
            show_title = show_title.replace(year, '').strip()
    
    # Pattern for episodes
    # ShoofVOD lists episodes in a different format
    pattern = r'<a href="([^"]+)" class="fullEpisode">.+?<span class="title">([^<]+)</span>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    if entries:
        for ep_url, ep_title in entries:
            # Clean episode title
            clean_title = utils.cleantext(ep_title)
            clean_title = re.sub(r'(مشاهدة|الحلقة|حلقة)', '', clean_title)
            clean_title = clean_title.replace('-', ' ').strip()
            
            # Try to extract episode number
            episode_num = None
            ep_match = re.search(r'(\d+)', clean_title)
            if ep_match:
                episode_num = int(ep_match.group(1))
            
            # Build display title
            if show_title and episode_num:
                display_title = '{} E{}'.format(show_title, str(episode_num).zfill(2))
            else:
                display_title = clean_title if clean_title else ep_title
            
            full_url = site.url + ep_url
            
            site.add_dir(display_title, full_url, 'getLinks', site.image,
                       episode=episode_num, show_title=show_title, year=year,
                       media_type='episode')
    else:
        # No episodes found, might be a movie or single video
        utils.kodilog('ShoofVOD: No episodes pattern matched, trying direct playback')
        site.add_dir(show_title if show_title else 'Play', url, 'getLinks', site.image)
    
    utils.eod(content='episodes')

@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url)
    
    utils.kodilog('ShoofVOD: Extracting links from: {}'.format(url))
    
    # Multi-step extraction from matrix addon
    # Step 1: Extract the var url
    url_pattern = r'var url = "([^<]+)" +'
    url_match = re.search(url_pattern, html)
    
    if url_match:
        partial_url = url_match.group(1)
        # Step 2: Fetch the full URL
        full_url = site.url + partial_url
        html = utils.getHtml(full_url)
    
    # Step 3: Extract iframe src
    iframe_pattern = r'<iframe src="(.+?)"'
    iframe_match = re.search(iframe_pattern, html)
    
    iframe_sources = []
    
    if iframe_match:
        iframe_url = iframe_match.group(1)
        # Add protocol if missing
        if iframe_url.startswith('//'):
            iframe_url = 'http:' + iframe_url
        
        # Step 4: Fetch iframe content
        headers = {'User-Agent': utils.USER_AGENT, 'Referer': site.url}
        html = utils.getHtml(iframe_url, headers=headers)
        
        # Step 5: Extract source src
        source_pattern = r'<source src="(.+?)" type='
        iframe_sources = re.findall(source_pattern, html)
    
    utils.kodilog('ShoofVOD: Found {} sources'.format(len(iframe_sources)))
    
    hoster_manager = get_hoster_manager()
    
    for source_url in iframe_sources:
        # Add protocol if missing
        if source_url.startswith('//'):
            source_url = 'http:' + source_url
        # Clean URL
        source_url = source_url.replace('&#038;', '&')
        
        utils.kodilog('ShoofVOD: Found source URL: {}'.format(source_url[:100]))
        
        # Format link with icon and check filtering
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            source_url,
            'ShoofVOD',
            name if name else 'Video'
        )
        
        if should_skip:
            utils.kodilog('ShoofVOD: Filtered out: {}'.format(source_url[:100]))
            continue
        
        # Add link WITHOUT resolving - resolution happens in PlayVid
        site.add_download_link(label, source_url, 'PlayVid', site.image, desc=name,
                              fanart=site.image, landscape=site.image)
    
    if not iframe_sources:
        utils.notify('ShoofVOD', 'No video sources found', aksvicon)
    
    utils.eod(content='videos')

@site.register()
def PlayVid(url, name=''):
    """Play video - resolve hoster URL on-demand when user clicks"""
    hoster_manager = get_hoster_manager()
    
    utils.kodilog('ShoofVOD: Attempting to resolve: {}'.format(url[:100]))
    
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        utils.kodilog('ShoofVOD: Resolved to: {}'.format(video_url[:100]))
    else:
        utils.kodilog('ShoofVOD: No resolver found, trying direct playback')
        video_url = url
    
    utils.playvid(video_url, name, site.image)
