# -*- coding: utf-8 -*-
"""
Asia2TV Site Module
"""

import re
from resources.lib import utils
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager, extract_iframe_sources

site = SiteBase('asia2tv', 'Asia2TV', url=None, image='sites/asia2tv.png')

@site.register(default_mode=True)
def Main():
    site.add_dir('Search Movies', site.url, 'searchMovies', site.image)
    site.add_dir('Search Series', site.url, 'searchSeries', site.image)
    site.add_dir('أفلام آسيوية', site.url + 'category/asian-movies/', 'getMovies', site.image)
    site.add_dir('مسلسلات آسيوية', site.url + 'category/asian-drama/', 'getTVShows', site.image)
    site.add_dir('مسلسلات كورية', site.url + 'category/asian-drama/korean/', 'getTVShows', site.image)
    site.add_dir('مسلسلات صينية', site.url + 'category/asian-drama/chinese-taiwanese/', 'getTVShows', site.image)
    site.add_dir('مسلسلات يابانية', site.url + 'category/asian-drama/japanese/', 'getTVShows', site.image)
    site.add_dir('مسلسلات تايلاندية', site.url + 'category/asian-drama/thai/', 'getTVShows', site.image)
    site.add_dir('برامج ترفيهية', site.url + 'category/asian-drama/kshow/', 'getTVShows', site.image)
    utils.eod()

@site.register()
def searchMovies():
    search_text = utils.get_search_input()
    if search_text:
        getMovies(site.url + '?s=' + search_text)

@site.register()
def searchSeries():
    search_text = utils.get_search_input()
    if search_text:
        getTVShows(site.url + '?s=' + search_text)

@site.register()
def getMovies(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
    
    # Pattern for movie entries - from postmovie-photo structure
    pattern = r'<div class="postmovie-photo">\s*<a href="([^"]+)" title="([^"]+)"'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    # Extract images separately since many items don't have them
    img_pattern = r'<div class="box-item">.*?<a href="([^"]+)".*?<img[^>]+src="([^"]+)"'
    img_dict = {url: img for url, img in re.findall(img_pattern, html, re.DOTALL)}
    
    for item_url, title in entries:
        img = img_dict.get(item_url, site.image)
        # Clean title - remove Arabic words and keep English
        clean_title = title.replace('فيلم', '').replace('مترجم', '').replace('مدبلج', '').strip()
        # Keep only English characters and spaces
        clean_title = re.sub(r'[^\x00-\x7F\s]+', ' ', clean_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        # Extract year
        year = None
        year_match = re.search(r'(\d{4})', clean_title)
        if year_match:
            year = year_match.group(1)
        
        if year:
            clean_title += ' ({})'.format(year)
        
        # Fix image URL
        if img.startswith('//'):
            img = 'https:' + img
        # Remove dimension suffix for high-res image (e.g., -238x320.jpg -> .jpg)
        img = re.sub(r'-\d+x\d+\.', '.', img)
        
        # Movies go to getEpisodes (which will then go to getLinks if no episodes)
        site.add_dir(clean_title, item_url, 'getEpisodes', img,
                    year=year, media_type='movie', original_title=title)
    
    # Check for next page - matrix uses 'next page-numbers'
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getMovies', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getTVShows(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
    
    # Pattern for TV show entries - from postmovie-photo structure
    pattern = r'<div class="postmovie-photo">\s*<a href="([^"]+)" title="([^"]+)"'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    # Extract images separately since many items don't have them
    img_pattern = r'<div class="box-item">.*?<a href="([^"]+)".*?<img[^>]+src="([^"]+)"'
    img_dict = {url: img for url, img in re.findall(img_pattern, html, re.DOTALL)}
    
    for item_url, title in entries:
        img = img_dict.get(item_url, site.image)
        # Clean title - remove Arabic words and keep English
        clean_title = title.replace('مسلسل', '').replace('مترجم', '').replace('مدبلج', '').strip()
        # Keep only English characters and spaces
        clean_title = re.sub(r'[^\x00-\x7F\s]+', ' ', clean_title).strip()
        clean_title = re.sub(r'\s+', ' ', clean_title)
        
        # Extract year
        year = None
        year_match = re.search(r'(\d{4})', clean_title)
        if year_match:
            year = year_match.group(1)
        
        # Fix image URL
        if img.startswith('//'):
            img = 'https:' + img
        # Remove dimension suffix for high-res image (e.g., -238x320.jpg -> .jpg)
        img = re.sub(r'-\d+x\d+\.', '.', img)
        
        site.add_dir(clean_title, item_url, 'getEpisodes', img,
                    year=year, media_type='tvshow', original_title=title)
    
    # Check for next page - matrix uses 'next page-numbers'
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getTVShows', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getEpisodes(url):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
    
    # Extract show title from page
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None
    if show_title:
        show_title = show_title.replace('مسلسل', '').replace('مترجم', '').strip()
        show_title = re.sub(r'[^\x00-\x7F\s]+', ' ', show_title).strip()
        show_title = re.sub(r'\s+', ' ', show_title)
    
    # Extract show poster/image from page - look in single-poster or meta tags
    show_img = site.image
    # Try meta og:image first
    img_match = re.search(r'<meta property="og:image" content="([^"]+)"', html)
    if not img_match:
        # Try any img tag in the content
        img_match = re.search(r'<img[^>]+src="([^"]+)"', html)
    if img_match:
        show_img = img_match.group(1)
        if show_img.startswith('//'):
            show_img = 'https:' + show_img
        # Remove dimension suffix for high-res image
        show_img = re.sub(r'-\d+x\d+\.', '.', show_img)
    
    # Extract year
    year = None
    if show_title:
        year_match = re.search(r'(\d{4})', show_title)
        if year_match:
            year = year_match.group(1)
            show_title = show_title.replace(year, '').strip()
    
    # Matrix pattern: narrow down HTML to episode-list section first
    episode_section_match = re.search(r'id="episode-list"(.+?)<div class="heading">', html, re.DOTALL)
    if episode_section_match:
        episode_html = episode_section_match.group(1)
    else:
        episode_html = html
    
    # Pattern for episodes - matrix pattern
    episode_pattern = r'<a href="([^"]+)".+?class="titlepisode">(.+?)</div>'
    
    entries = re.findall(episode_pattern, episode_html, re.DOTALL)
    
    if entries:
        for ep_url, ep_title in entries:
            # Clean episode title
            clean_title = utils.cleantext(ep_title)
            
            # Extract episode number - matrix way
            if 'الحلقة' in ep_title:
                ep_num_match = re.search(r'الحلقة\s*(\d+)', ep_title)
                if ep_num_match:
                    episode_num = int(ep_num_match.group(1))
                    display_title = 'E{:02d} {}'.format(episode_num, show_title if show_title else '')
                else:
                    display_title = clean_title
                    episode_num = None
            else:
                display_title = clean_title
                episode_num = None
            
            site.add_dir(display_title.strip(), ep_url, 'getLinks', show_img,
                       episode=episode_num, show_title=show_title, year=year, media_type='episode')
    else:
        # No episodes, treat as movie/single video  
        utils.kodilog('Asia2TV: No episodes found, treating as movie')
        site.add_dir(show_title if show_title else 'Play', url, 'getLinks', show_img,
                   year=year, media_type='movie')
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
    
    utils.kodilog('Asia2TV: Extracting links from: {}'.format(url))
    
    # Matrix pattern: data-server attribute
    server_pattern = r'data-server="([^"]+)"'
    iframe_sources = re.findall(server_pattern, html)
    
    utils.kodilog('Asia2TV: Found {} data-server sources'.format(len(iframe_sources)))
    
    if not iframe_sources:
        # Fallback: look for iframe sources
        iframe_pattern = r'<iframe[^>]+(?:src|data-src)="([^"]+)"'
        iframe_sources = re.findall(iframe_pattern, html)
        utils.kodilog('Asia2TV: Found {} iframe sources'.format(len(iframe_sources)))
    
    if not iframe_sources:
        utils.kodilog('Asia2TV: No sources found')
        if 'قريباً' in html:
            utils.notify('Asia2TV', 'Soon - No Links Yet')
        else:
            utils.notify('Asia2TV', 'No video sources found')
        return
    
    hoster_manager = get_hoster_manager()
    
    for source_url in iframe_sources:
        # Clean URL
        source_url = source_url.strip()
        source_url = source_url.replace('&#038;', '&').replace('&amp;', '&')
        
        # Skip if it's not a valid URL
        if not source_url.startswith(('http://', 'https://', '//')):
            continue
        
        # Add protocol if missing
        if source_url.startswith('//'):
            source_url = 'https:' + source_url
        
        utils.kodilog('Asia2TV: Found source URL: {}'.format(source_url[:100]))
        
        # Format link with icon and check filtering
        label, should_skip = utils.format_resolver_link(
            hoster_manager, 
            source_url, 
            'Asia2TV',
            name if name else 'Video'
        )
        
        if should_skip:
            utils.kodilog('Asia2TV: Filtered out: {}'.format(source_url[:100]))
            continue
        
        # Add link WITHOUT resolving - resolution happens in PlayVid
        site.add_download_link(label, source_url, 'PlayVid', site.image, desc=name,
                              fanart=site.image, landscape=site.image)
    
    if not iframe_sources:
        utils.notify('Asia2TV', 'No video sources found')
    
    utils.eod()

@site.register()
def PlayVid(url, name=''):
    """Play video - resolve hoster URL on-demand when user clicks"""
    hoster_manager = get_hoster_manager()
    
    utils.kodilog('Asia2TV: Attempting to resolve: {}'.format(url[:100]))
    
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        headers = result.get('headers', {})
        
        # Append headers to URL in Kodi format
        if headers:
            header_str = '|' + '&'.join(['{}={}'.format(k, v) for k, v in headers.items()])
            video_url = video_url + header_str
        
        utils.kodilog('Asia2TV: Resolved to: {}'.format(video_url[:100]))
    else:
        utils.kodilog('Asia2TV: No resolver found, trying direct playback')
        video_url = url
    
    utils.playvid(video_url, name, site.image)
