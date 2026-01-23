# -*- coding: utf-8 -*-
"""
Cima4u Site Module
https://cima4u.info
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image, aksvicon
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('cima4u', 'Cima4u', url=None, image='sites/cima4u.png')

@site.register(default_mode=True)
def Main():
    """Main menu"""
    # Movies
    site.add_dir('أفلام أجنبية', site.url + '/category/افلام-اجنبي/', 'getMovies', site.image)
    site.add_dir('أفلام عربية', site.url + '/category/افلام-عربى/', 'getMovies', site.image)
    site.add_dir('أفلام هندية', site.url + '/category/افلام-هندى/', 'getMovies', site.image)
    site.add_dir('أفلام تركية', site.url + '/category/افلام-تركى/', 'getMovies', site.image)
    site.add_dir('أفلام كرتون', site.url + '/category/افلام-كرتون/', 'getMovies', site.image)
    
    # Series
    site.add_dir('مسلسلات أجنبية', site.url + '/category/مسلسلات-اجنبي/', 'getSeries', site.image)
    site.add_dir('مسلسلات عربية', site.url + '/category/مسلسلات-عربية/', 'getSeries', site.image)
    site.add_dir('مسلسلات تركية', site.url + '/category/مسلسلات-تركية/', 'getSeries', site.image)
    site.add_dir('مسلسلات آسيوية', site.url + '/category/مسلسلات-اسيوية/', 'getSeries', site.image)
    site.add_dir('مسلسلات هندية', site.url + '/category/مسلسلات-هندية/', 'getSeries', site.image)
    site.add_dir('مسلسلات كرتون', site.url + '/category/مسلسلات-كرتون/', 'getSeries', site.image)
    site.add_dir('مسلسلات رمضان 2025', site.url + '/category/مسلسلات-رمضان-2025/', 'getSeries', site.image)
    
    # Other
    site.add_dir('برامج تلفزيونية', site.url + '/category/برامج-تليفزيونية/', 'getSeries', site.image)
    site.add_dir('مصارعة حرة', site.url + '/category/مصارعة-حرة/', 'getSeries', site.image)
    
    # Search
    site.add_dir('بحث', '', 'search', site.image)
    
    utils.eod()

@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if search_text:
        search_url = site.url + '/?s=' + search_text
        getMovies(search_url)

@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog('Cima4u: Getting movies from: {}'.format(url))
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    
    if not html:
        utils.kodilog('Cima4u: No HTML received')
        utils.eod()
        return
    
    # Try pattern 1: Regular listings with data-image
    pattern1 = r'<li class="MovieBlock">.*?<a href="([^"]+)".*?data-image="([^"]+)".*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'
    matches = re.findall(pattern1, html, re.DOTALL)
    
    # Try pattern 2: Search results with background-image style
    # More explicit: href must be immediately after <a, before other content
    if not matches:
        pattern2 = r'<li class="MovieBlock">\s*<a href="([^"]+)"[^>]*>\s*<div class="Thumb">.*?background-image:url\(([^\)]+)\).*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'
        matches = re.findall(pattern2, html, re.DOTALL)
    
    utils.kodilog('Cima4u: Found {} movies'.format(len(matches)))
    
    if matches:
        added = 0
        for movie_url, image, title in matches:
            # Log raw extracted data
            utils.kodilog('Cima4u: Raw title: [{}], URL: {}'.format(repr(title[:50] if title else 'NONE'), movie_url[:60]))
            
            # Skip if no title or image
            if not title or not title.strip():
                utils.kodilog('Cima4u: Skipped - empty title')
                continue
                
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مترجم|اون لاين|HD|مدبلج', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            utils.kodilog('Cima4u: Clean title: [{}]'.format(title))
            
            if title:  # Only add if we have a valid title
                site.add_dir(title, movie_url, 'getLinks', image, year=year, media_type='movie')
                added += 1
            else:
                utils.kodilog('Cima4u: Skipped - title empty after cleaning')
        
        utils.kodilog('Cima4u: Added {} out of {} movies'.format(added, len(matches)))
    
    # Pagination
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getSeries(url):
    """Get series listing"""
    utils.kodilog('Cima4u: Getting series from: {}'.format(url))
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    
    if not html:
        utils.kodilog('Cima4u: No HTML received')
        utils.eod()
        return
    
    # Try pattern 1: Regular listings with data-image
    pattern1 = r'<li class="MovieBlock">.*?<a href="([^"]+)".*?data-image="([^"]+)".*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'
    matches = re.findall(pattern1, html, re.DOTALL)
    
    # Try pattern 2: Search results with background-image style
    # More explicit: href must be immediately after <a, before other content
    if not matches:
        pattern2 = r'<li class="MovieBlock">\s*<a href="([^"]+)"[^>]*>\s*<div class="Thumb">.*?background-image:url\(([^\)]+)\).*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'
        matches = re.findall(pattern2, html, re.DOTALL)
    
    utils.kodilog('Cima4u: Found {} series'.format(len(matches)))
    
    seen_titles = set()
    
    if matches:
        for series_url, image, title in matches:
            # Skip if no title
            if not title or not title.strip():
                continue
                
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|مسلسل|مترجمة|اون لاين|HD|مدبلج|كاملة|الحلقة|حلقة', '', title).strip()
            
            # Convert season numbers
            title = _convert_season_arabic_to_english(title)
            
            # Remove episode numbers to group by show
            title = re.split(r'الحلقة|حلقة|E\d+', title)[0].strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Deduplicate and validate
            if title and title not in seen_titles:
                seen_titles.add(title)
                site.add_dir(title, series_url, 'getEpisodes', image, year=year, media_type='tvshow')
    
    # Pagination
    next_match = re.search(r'<a class="next page-numbers" href="([^"]+)"', html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getSeries', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series"""
    utils.kodilog('Cima4u: Getting episodes from: {}'.format(url))
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    
    # Check if this is a show page with episodes list
    episodes_pattern = r'<a[^>]+href="([^"]+)"[^>]*>([^<]*)<em>([^<]+)</em>'
    episodes = re.findall(episodes_pattern, html)
    
    if episodes:
        # This is a show page with episode list
        for ep_url, ep_text, ep_num in episodes:
            ep_num = ep_num.strip()
            title = '{} E{}'.format(name, ep_num)
            title = _convert_season_arabic_to_english(title)
            
            # Get thumbnail from page
            thumb_match = re.search(r'data-image="([^"]+)"', html)
            thumb = thumb_match.group(1) if thumb_match else site.image
            
            site.add_dir(title, ep_url, 'getLinks', thumb, media_type='episode')
    else:
        # This might be a single episode page, just show it
        getLinks(url, name)
        return
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    """Extract video links from page"""
    utils.kodilog('Cima4u: Getting links from: {}'.format(url))
    
    # Cima4u uses ?wat=1 (not watch=1) for the watch page
    watch_url = url.replace('?watch=1', '?wat=1') if '?watch=' in url else url + '?wat=1'
    
    html = utils.getHtml(watch_url, headers={'User-Agent': utils.USER_AGENT})
    
    if not html:
        utils.notify('Cima4u', 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod()
        return
    
    hoster_manager = get_hoster_manager()
    
    # Pattern: <a class="sever_link" data-embed="URL">SERVER_NAME</a>
    server_pattern = r'<a[^>]+class="[^"]*sever_link[^"]*"[^>]+data-embed="([^"]+)"[^>]*>([^<]*)</a>'
    servers = re.findall(server_pattern, html)
    
    utils.kodilog('Cima4u: Found {} servers'.format(len(servers)))
    
    for embed_url, server_name in servers:
        embed_url = embed_url.strip()
        server_name = server_name.strip() or 'Server'
        
        # Format link with resolver icons
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            embed_url,
            'Cima4u',
            name,
            quality=server_name
        )
        
        if not should_skip:
            basics.addDownLink(label, embed_url, 'cima4u.PlayVid', site.image)
    
    if not servers:
        utils.notify('Cima4u', 'لم يتم العثور على روابط', icon=site.image)
    
    utils.eod()

@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    utils.kodilog('Cima4u: Resolving URL: {}'.format(url[:100]))
    
    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result and result.get('url'):
        video_url = result['url']
        utils.kodilog('Cima4u: Playing: {}'.format(video_url[:100]))
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify('Cima4u', 'فشل تشغيل الفيديو', icon=site.image)

def _convert_season_arabic_to_english(title):
    """Convert Arabic season numbers to English format"""
    replacements = {
        'الموسم الأول': 'S1', 'الموسم الاول': 'S1',
        'الموسم الثاني': 'S2', 'الموسم الثانى': 'S2',
        'الموسم الثالث': 'S3',
        'الموسم الرابع': 'S4',
        'الموسم الخامس': 'S5',
        'الموسم السادس': 'S6',
        'الموسم السابع': 'S7',
        'الموسم الثامن': 'S8',
        'الموسم التاسع': 'S9',
        'الموسم العاشر': 'S10',
        'الموسم الحادي عشر': 'S11',
        'الموسم الثاني عشر': 'S12',
        'الموسم الثالث عشر': 'S13',
        'الموسم الرابع عشر': 'S14',
        'الموسم الخامس عشر': 'S15',
        'الموسم': 'S',
        'موسم': 'S'
    }
    
    for arabic, english in replacements.items():
        title = title.replace(arabic, english)
    
    return title
