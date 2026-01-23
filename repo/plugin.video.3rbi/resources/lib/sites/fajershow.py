# -*- coding: utf-8 -*-
"""
FajerShow (alfajertv) Site Module
"""

import re
from resources.lib import utils
from resources.lib.basics import addon, addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager, extract_iframe_sources

site = SiteBase('fajershow', 'FajerShow', url=None, image='sites/alfajertv.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    site.add_dir('Search', site.url, 'search', get_category_icon('Search'))
    site.add_dir('English Movies', site.url + '/genre/english-movies/', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('Arabic Movies', site.url + '/genre/arabic-movies/', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('Turkish Movies', site.url + '/genre/turkish-movies/', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('Indian Movies', site.url + '/genre/indian-movies/', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('Cartoon Movies', site.url + '/genre/animation/', 'getMovies', get_category_icon('Cartoon Movies'))
    site.add_dir('English TV Shows', site.url + '/genre/english-series/', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('Arabic TV Shows', site.url + '/genre/arabic-series/', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('Turkish TV Shows', site.url + '/genre/turkish-series/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('Indian TV Shows', site.url + '/genre/indian-series/', 'getTVShows', get_category_icon('Indian TV Shows'))
    site.add_dir('Theater', site.url + '/genre/plays/', 'getMovies', get_category_icon('Theater'))
    utils.eod()

@site.register()
def search():
    search_text = utils.get_search_input()
    if search_text:
        searchResults(site.url + '/?s=' + search_text)

@site.register()
def searchResults(url):
    html = utils.getHtml(url)
    
    # Pattern for search results - simpler and more robust
    pattern = r'<div class="result-item">.*?<a href="([^"]+)"><img src="([^"]+)" alt="([^"]+)".*?<span class="year">([^<]+)</span>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for item_url, img, title, year in entries:
        # Clean title
        clean_title = title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجمة","").replace("مترجم","").replace("برنامج","").replace("فيلم","").replace("والأخيرة","").replace("مدبلج للعربية","مدبلج").replace("والاخيرة","").replace("كاملة","").replace("حلقات كاملة","").replace("اونلاين","").replace("مباشرة","").replace("انتاج ","").replace("جودة عالية","").replace("كامل","").replace("HD","").replace("السلسلة الوثائقية","").replace("الفيلم الوثائقي","").replace("اون لاين","")
        clean_title = clean_title.strip()
        
        # Get high res image
        img = re.sub(r'-\d*x\d*\.', '.', img)
        
        # Determine if movie or TV show from URL
        if '/movies/' in item_url:
            site.add_dir(clean_title, item_url, 'getLinks', img, fanart=img,
                        year=year, media_type='movie', original_title=title)
        else:
            site.add_dir(clean_title, item_url, 'getSeasons', img, fanart=img,
                        year=year, media_type='tvshow', original_title=title)
    
    # Check for next page
    next_match = re.search(r'<link rel="next" href="(.+?)" />', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'searchResults', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getMovies(url):
    # Handle url as list or string
    if isinstance(url, list):
        url = url[0]
    html = utils.getHtml(url)
    
    # Pattern from matrix addon - exact match
    pattern = r'<img src="([^<]+)" alt="([^<]+)">.+?</div><a href="([^<]+)"><div class="see">.+?<span>([^<]+)</span> <span>.+?class="texto">(.+?)</div>'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for img, title, item_url, year, desc in entries:
        # Clean title - exact cleaning from matrix
        clean_title = title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجمة","").replace("مترجم","").replace("برنامج","").replace("فيلم","").replace("والأخيرة","").replace("مدبلج للعربية","مدبلج").replace("والاخيرة","").replace("كاملة","").replace("حلقات كاملة","").replace("اونلاين","").replace("مباشرة","").replace("انتاج ","").replace("جودة عالية","").replace("كامل","").replace("HD","").replace("السلسلة الوثائقية","").replace("الفيلم الوثائقي","").replace("اون لاين","")
        
        # Extract year from title if exists
        year_match = re.search(r'([0-9]{4})', clean_title)
        if year_match:
            year = str(year_match.group(0))
            clean_title = clean_title.replace(year, '')
        
        clean_title = clean_title.strip()
        
        # Get high res image - exact pattern from matrix
        img = re.sub(r'-\d*x\d*\.', '.', img)
        
        site.add_dir(clean_title, item_url, 'getLinks', img, desc=desc, fanart=img, 
                    year=year, media_type='movie', original_title=title)
    
    # Check for next page - exact pattern from matrix
    next_match = re.search(r'<link rel="next" href="(.+?)" />', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getMovies', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getTVShows(url):
    html = utils.getHtml(url)
    
    # Pattern from matrix addon - exact match
    pattern = r'<article id=".+?" class="item tvshows "><div class="poster"><img src="([^<]+)" alt="([^<]+)"><div class="rating"><span class="icon-star2"></span>([^<]+)</div><div class="mepo"> </div><a href="(.+?)"><div class="see">'
    
    entries = re.findall(pattern, html, re.DOTALL)
    
    for img, title, rating, item_url in entries:
        # Clean title - exact cleaning from matrix
        clean_title = title.replace("مشاهدة","").replace("مسلسل","").replace("انمي","").replace("مترجمة","").replace("مترجم","").replace("برنامج","").replace("فيلم","").replace("والأخيرة","").replace("مدبلج للعربية","مدبلج").replace("والاخيرة","").replace("كاملة","").replace("حلقات كاملة","").replace("اونلاين","").replace("مباشرة","").replace("انتاج ","").replace("جودة عالية","").replace("كامل","").replace("HD","").replace("السلسلة الوثائقية","").replace("الفيلم الوثائقي","").replace("اون لاين","")
        
        # Extract year
        year = None
        year_match = re.search(r'([0-9]{4})', clean_title)
        if year_match:
            year = str(year_match.group(0))
            clean_title = clean_title.replace(year, '')
        
        clean_title = clean_title.strip()
        
        # Get high res image - exact pattern from matrix
        img = re.sub(r'-\d*x\d*\.', '.', img)
        
        site.add_dir(clean_title, item_url, 'getSeasons', img, fanart=img,
                    year=year, media_type='tvshow', original_title=title)
    
    # Check for next page - exact pattern from matrix
    next_match = re.search(r'<link rel="next" href="(.+?)" />', html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getTVShows', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getSeasons(url):
    html = utils.getHtml(url)
    
    # Extract show info
    title_match = re.search(r'<h1[^>]*>([^<]+)</h1>', html)
    show_title = utils.cleantext(title_match.group(1)) if title_match else None
    
    # Extract year
    year = None
    if show_title:
        year_match = re.search(r'(\d{4})', show_title)
        if year_match:
            year = year_match.group(1)
    
    # Pattern for episodes from matrix addon - exact match
    pattern = r"<div class='imagen'><a href='([^']+)'><img src='([^']+)'></a></div><div class='numerando'>([^<]+)</div><div class='episodiotitle'><a href='.+?'>([^<]+)</a>"
    
    entries = re.findall(pattern, html)
    
    if entries:
        # Has episodes - list them
        for ep_url, ep_img, ep_num, ep_title in entries:
            # Format from matrix: S1E5 format ("1 - 5" becomes "S1E5")
            display_title = show_title + ' S' + ep_num.replace("- ", "E") if show_title else ep_title
            
            # Parse season and episode number for metadata
            season_num = None
            episode_num = None
            if ' - ' in ep_num:
                parts = ep_num.split(' - ')
                season_num = int(parts[0]) if parts[0].isdigit() else None
                episode_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None
            
            # Get high res image - exact pattern from matrix
            ep_img = re.sub(r'-\d*x\d*\.', '.', ep_img)
            
            site.add_dir(display_title, ep_url, 'getLinks', ep_img, fanart=ep_img,
                       season=season_num, episode=episode_num, show_title=show_title,
                       year=year, media_type='episode')
    else:
        # No episodes found, might be a movie or direct content
        site.add_dir(show_title if show_title else 'Play', url, 'getLinks', site.image)
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    html = utils.getHtml(url)
    
    utils.kodilog('FajerShow: Extracting links from: {}'.format(url))
    
    # Extract player options
    # Pattern: id="player-option-X" data-type="TYPE" data-post="POST_ID" data-nume="NUME"
    pattern = r'id="player-option-\d+" data-type="([^"]+)" data-post="([^"]+)" data-nume="([^"]+)"'
    players = re.findall(pattern, html)
    
    utils.kodilog('FajerShow: Found {} player options'.format(len(players)))
    
    hoster_manager = get_hoster_manager()
    
    for data_type, post_id, nume in players:
        # Make AJAX request to get player URL
        ajax_url = site.url + '/wp-admin/admin-ajax.php'
        
        # POST data must be a dictionary for utils.postHtml
        post_data = {
            'action': 'doo_player_ajax',
            'post': post_id,
            'nume': nume,
            'type': data_type
        }
        
        headers = {
            'User-Agent': utils.USER_AGENT,
            'Referer': url,
            'Host': 'show.alfajertv.com',
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        ajax_response = utils.postHtml(ajax_url, post_data, headers)
        
        # Extract iframe source
        iframe_match = re.search(r"<iframe.+?src='([^']+)'", ajax_response)
        if iframe_match:
            iframe_url = iframe_match.group(1)
            iframe_url = iframe_url.replace('%2F', '/').replace('%3A', ':')
            
            # Remove wrapper parameters
            iframe_url = re.sub(r'https://show\.alfajertv\.com/jwplayer/\?source=', '', iframe_url)
            iframe_url = re.sub(r'&type=mp4', '', iframe_url)
            iframe_url = iframe_url.split('&id')[0]
            
            utils.kodilog('FajerShow: Found hoster URL: {}'.format(iframe_url[:100]))
            
            # Format link with icon and check filtering
            label, should_skip = utils.format_resolver_link(
                hoster_manager,
                iframe_url,
                'FajerShow',
                name if name else 'Video'
            )
            
            if should_skip:
                utils.kodilog('FajerShow: Filtered out: {}'.format(iframe_url[:100]))
                continue
            
            # Add link WITHOUT resolving - resolution happens when user clicks (in PlayVid)
            site.add_download_link(label, iframe_url, 'PlayVid', site.image, desc=name,
                                  fanart=site.image, landscape=site.image)
    
    utils.eod()

@site.register()
def PlayVid(url, name=''):
    """Play video - resolve hoster URL on-demand when user clicks"""
    hoster_manager = get_hoster_manager()
    
    utils.kodilog('FajerShow: Attempting to resolve: {}'.format(url[:100]))
    
    # Try to resolve the hoster
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        utils.kodilog('FajerShow: Resolved to: {}'.format(video_url[:100]))
    else:
        # If no resolver found, try playing the URL directly
        utils.kodilog('FajerShow: No resolver found, trying direct playback')
        video_url = url
    
    utils.playvid(video_url, name, site.image)
