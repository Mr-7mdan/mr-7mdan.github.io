# -*- coding: utf-8 -*-
"""
Daktna Site Module
"""

import re
from resources.lib import utils
from resources.lib.basics import addon, addon_image, aksvicon
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager, extract_iframe_sources

site = SiteBase('daktna', 'Daktna', url=None, image='sites/daktna.png')

def _convert_arabic_seasons(title):
    """Convert Arabic season names to S01, S02 format"""
    title = title.replace("الموسم العاشر","S10").replace("الموسم الحادي عشر","S11").replace("الموسم الثاني عشر","S12").replace("الموسم الثالث عشر","S13").replace("الموسم الرابع عشر","S14").replace("الموسم الخامس عشر","S15").replace("الموسم السادس عشر","S16").replace("الموسم السابع عشر","S17").replace("الموسم الثامن عشر","S18").replace("الموسم التاسع عشر","S19").replace("الموسم العشرون","S20").replace("الموسم الحادي و العشرون","S21").replace("الموسم الثاني و العشرون","S22").replace("الموسم الثالث و العشرون","S23").replace("الموسم الرابع والعشرون","S24").replace("الموسم الخامس و العشرون","S25").replace("الموسم السادس والعشرون","S26").replace("الموسم السابع والعشرون","S27").replace("الموسم الثامن والعشرون","S28").replace("الموسم التاسع والعشرون","S29").replace("الموسم الثلاثون","S30").replace("الموسم الحادي و الثلاثون","S31").replace("الموسم الثاني والثلاثون","S32").replace("الموسم الاول","S1").replace("الموسم الثاني","S2").replace("الموسم الثالث","S3").replace("الموسم الرابع","S4").replace("الموسم الخامس","S5").replace("الموسم السادس","S6").replace("الموسم السابع","S7").replace("الموسم الثامن","S8").replace("الموسم التاسع","S9").replace("الموسم","S").replace("موسم","S").replace("S ","S")
    return title

def _convert_arabic_season_episode(title):
    """Convert Arabic season and episode names to S01E01 format"""
    # First convert seasons
    title = _convert_arabic_seasons(title)
    # Then convert episodes
    title = title.replace("الحلقة","E")
    return title

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    site.add_dir('Search', site.url, 'search', get_category_icon('Search'))
    site.add_dir('Ramadan TV Shows', site.url + '/list/series/', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + '/list/series/', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + '/list/series-turkish/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    utils.eod()

@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        searchShows(site.url + '/?s=' + search_text)

@site.register()
def searchShows(url):
    html = utils.getHtml(url)
    
    # Pattern for search results
    pattern = r'<div class="thumb"><a href="(.+?)"><img src=.+?alt="(.+?)" data-src="(.+?)" class="'
    
    entries = re.findall(pattern, html)
    
    seen_titles = []
    for item_url, title, img in entries:
        # Clean title - exact cleaning from matrix
        clean_title = title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجم للعربية","").replace("مترجمة","").replace("مترجم","").replace("مشاهده","").replace("برنامج","").replace("مترجمة","").replace("فيلم","").replace("اون لاين","").replace("WEB-DL","").replace("BRRip","").replace("720p","").replace("HD-TC","").replace("HDRip","").replace("HD-CAM","").replace("DVDRip","").replace("BluRay","").replace("1080p","").replace("WEBRip","").replace("WEB-dl","").replace("مترجم ","").replace("مشاهدة وتحميل","").replace("اون لاين","")
        
        # Convert Arabic season/episode - exact from matrix
        clean_title = _convert_arabic_season_episode(clean_title)
        
        # Extract show title and episode - matrix format
        show_name = clean_title.split('الحلقة')[0]
        ep_title = clean_title.replace("الحلقة", "E")
        
        # Parse episode number
        episode_num = None
        if 'E' in ep_title:
            ep_parts = ep_title.split('E')
            if len(ep_parts) > 1:
                ep_num_str = ep_parts[1].split('ال')[0]
                try:
                    episode_num = int(ep_num_str)
                except:
                    pass
        
        # Extract year
        year_val = None
        year_match = re.search(r'([0-9]{4})', ep_title)
        if year_match:
            year_val = str(year_match.group(0))
            ep_title = ep_title.replace(year_val, '')
        
        # Format: E05 Show Name
        if episode_num:
            display_title = 'E{} {}'.format(str(episode_num).zfill(2), show_name.strip())
        else:
            display_title = ep_title
        
        # Parse season from show_name if present
        season_num = None
        season_match = re.search(r'S(\d+)', show_name)
        if season_match:
            season_num = int(season_match.group(1))
        
        # Check if this is an episode or a show
        if 'الحلقة' in title and episode_num:
            # It's an episode
            site.add_dir(display_title, item_url, 'getLinks', img, fanart=img,
                       season=season_num, episode=episode_num, show_title=show_name,
                       year=year_val, media_type='episode')
        else:
            # It's a show
            site.add_dir(clean_title, item_url, 'getEpisodes', img, fanart=img,
                       year=year_val, media_type='tvshow', original_title=title)
    
    # Check for next page
    next_match = re.search(r'rel="next" href="([^"]+)">', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'searchShows', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getTVShows(url):
    html = utils.getHtml(url)
    
    # Pattern from matrix addon - exact match
    pattern = r'<div class="thumb"><a href="(.+?)"><img src=.+?alt="(.+?)" data-src="(.+?)" class="'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    seen_titles = set()
    
    for item_url, title, img in entries:
        # Clean title - exact cleaning from matrix
        clean_title = title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجمة","").replace("مترجم للعربية","").replace("مترجم","").replace("مشاهده","").replace("برنامج","").replace("مترجمة","").replace("فيلم","").replace("اون لاين","").replace("WEB-DL","").replace("BRRip","").replace("720p","").replace("HD-TC","").replace("HDRip","").replace("HD-CAM","").replace("DVDRip","").replace("BluRay","").replace("1080p","").replace("WEBRip","").replace("WEB-dl","").replace("مترجم ","").replace("مشاهدة وتحميل","").replace("اون لاين","")
        
        # Convert Arabic season names to English format
        clean_title = _convert_arabic_seasons(clean_title)
        
        # Remove episode info to get show title
        show_title = clean_title.split('الحلقة')[0].strip()
        
        # Extract year
        year = None
        year_match = re.search(r'([0-9]{4})', show_title)
        if year_match:
            year = str(year_match.group(0))
            show_title = show_title.replace(year, '')
        
        show_title = show_title.strip()
        
        # Deduplicate shows
        if show_title not in seen_titles:
            seen_titles.add(show_title)
            
            site.add_dir(show_title, item_url, 'getEpisodes', img, fanart=img,
                       year=year, media_type='tvshow', original_title=title)
    
    # Check for next page - exact pattern from matrix
    next_match = re.search(r'rel="next" href="([^<]+)">', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getTVShows', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getEpisodes(url):
    html = utils.getHtml(url)
    
    # Extract show title from page
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None
    if show_title:
        show_title = re.sub(r'(مشاهدة|مسلسل|انمي|مترجم|مترجمة)', '', show_title).strip()
        show_title = _convert_arabic_seasons(show_title)
    
    # Extract year
    year = None
    if show_title:
        year_match = re.search(r'([0-9]{4})', show_title)
        if year_match:
            year = str(year_match.group(0))
            show_title = show_title.replace(year, '').strip()
    
    # Extract category URL - matrix pattern
    category_pattern = r'class="tags">.+?href="(.+?)" >'
    category_match = re.search(category_pattern, html, re.DOTALL)
    
    if category_match:
        category_url = category_match.group(1)
        if category_url.startswith('//'):
            category_url = 'https:' + category_url
        # Fetch episodes from category page
        html = utils.getHtml(category_url)
    
    # Pattern for episodes - matrix pattern
    pattern = r'<div class="thumb"><a href="(.+?)"><img src=.+?alt="(.+?)" data-src="(.+?)" class="'
    
    entries = re.findall(pattern, html)
    
    for ep_url, ep_title, ep_img in entries:
        # Clean episode title - exact cleaning from matrix
        clean_title = ep_title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجمة","").replace("مترجم للعربية","").replace("مترجم","").replace("مشاهده","").replace("برنامج","").replace("مترجمة","").replace("فيلم","").replace("اون لاين","").replace("WEB-DL","").replace("BRRip","").replace("720p","").replace("HD-TC","").replace("HDRip","").replace("HD-CAM","").replace("DVDRip","").replace("BluRay","").replace("1080p","").replace("WEBRip","").replace("WEB-dl","").replace("مترجم ","").replace("مشاهدة وتحميل","").replace("اون لاين","")
        
        # Convert Arabic season/episode - exact from matrix
        clean_title = _convert_arabic_season_episode(clean_title)
        
        # Extract episode number
        episode_num = None
        if 'E' in clean_title:
            ep_parts = clean_title.split('E')
            if len(ep_parts) > 1:
                ep_num_str = ep_parts[1].split('ال')[0]
                try:
                    episode_num = int(ep_num_str)
                except:
                    pass
        
        # Extract season number
        season_num = None
        season_match = re.search(r'S(\d+)', clean_title)
        if season_match:
            season_num = int(season_match.group(1))
        
        # Build display title
        if episode_num and show_title:
            if season_num:
                display_title = '{} S{}E{}'.format(show_title, str(season_num).zfill(2), str(episode_num).zfill(2))
            else:
                display_title = '{} E{}'.format(show_title, str(episode_num).zfill(2))
        else:
            display_title = clean_title
        
        site.add_dir(display_title, ep_url, 'getLinks', ep_img, fanart=ep_img,
                   season=season_num, episode=episode_num, show_title=show_title,
                   year=year, media_type='episode')
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url)
    
    utils.kodilog('Daktna: Extracting links from: {}'.format(url))
    
    # Extract the external page URL - matrix pattern
    external_pattern = r'target="_blank" href="(.+?)" rel="nofollow">'
    external_match = re.search(external_pattern, html)
    
    if external_match:
        external_url = external_match.group(1)
        if external_url.startswith('//'):
            external_url = 'https:' + external_url
        
        # Fetch external page
        headers = {
            'User-Agent': utils.USER_AGENT,
            'Referer': site.url
        }
        html = utils.getHtml(external_url, headers=headers)
    
    # Extract video sources - matrix pattern
    source_pattern = r'data-src="([^<]+)">'
    iframe_sources = re.findall(source_pattern, html)
    
    utils.kodilog('Daktna: Found {} sources'.format(len(iframe_sources)))
    
    hoster_manager = get_hoster_manager()
    
    for source_url in iframe_sources:
        # Add protocol if missing
        if source_url.startswith('//'):
            source_url = 'http:' + source_url
        # Clean URL
        iframe_url = source_url.replace('&#038;', '&')
        
        utils.kodilog('Daktna: Found hoster URL: {}'.format(iframe_url[:100]))
        
        # Format link with icon and check filtering
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            iframe_url,
            'Daktna',
            name if name else 'Video'
        )
        
        if should_skip:
            utils.kodilog('Daktna: Filtered out: {}'.format(iframe_url[:100]))
            continue
        
        # Add link WITHOUT resolving - resolution happens in PlayVid
        site.add_download_link(label, iframe_url, 'PlayVid', site.image, desc=name,
                              fanart=site.image, landscape=site.image)
    
    if not iframe_sources:
        utils.notify('Daktna', 'No video sources found', aksvicon)
    
    utils.eod()

@site.register()
def PlayVid(url, name=''):
    """Play video - resolve hoster URL on-demand when user clicks"""
    hoster_manager = get_hoster_manager()
    
    utils.kodilog('Daktna: Attempting to resolve: {}'.format(url[:100]))
    
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        utils.kodilog('Daktna: Resolved to: {}'.format(video_url[:100]))
    else:
        utils.kodilog('Daktna: No resolver found, trying direct playback')
        video_url = url
    
    utils.playvid(video_url, name, site.image)

def _convert_arabic_seasons(title):
    """Convert Arabic season/episode names to English format"""
    replacements = [
        ('الموسم العاشر', 'S10'),
        ('الموسم الحادي عشر', 'S11'),
        ('الموسم الثاني عشر', 'S12'),
        ('الموسم الثالث عشر', 'S13'),
        ('الموسم الرابع عشر', 'S14'),
        ('الموسم الخامس عشر', 'S15'),
        ('الموسم الاول', 'S1'),
        ('الموسم الثاني', 'S2'),
        ('الموسم الثالث', 'S3'),
        ('الموسم الرابع', 'S4'),
        ('الموسم الخامس', 'S5'),
        ('الموسم السادس', 'S6'),
        ('الموسم السابع', 'S7'),
        ('الموسم الثامن', 'S8'),
        ('الموسم التاسع', 'S9'),
        ('الموسم', 'S'),
        ('موسم', 'S'),
        ('الحلقة', 'E'),
    ]
    
    for arabic, english in replacements:
        title = title.replace(arabic, english)
    
    # Clean up spacing
    title = re.sub(r'S\s+', 'S', title)
    title = re.sub(r'E\s+', 'E', title)
    
    return title
