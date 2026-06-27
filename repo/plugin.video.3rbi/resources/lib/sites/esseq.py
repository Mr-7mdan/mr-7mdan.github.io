# -*- coding: utf-8 -*-
"""
Esseq (قصة عشق) Site Module
https://new.eishq.net/
"""

import re
import base64
import json
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('esseq', 'Esseq', url=None, image='sites/esseq.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    """Main menu"""
    # Site now primarily shows latest episodes on homepage
    site.add_dir('Latest Episodes', site.url + '/', 'getEpisodes', get_category_icon('Ramadan TV Shows'))
    site.add_dir('Series', site.url + '/video/series/', 'getTVShows', get_category_icon('TV Shows'))
    site.add_dir('Search', '', 'search', get_category_icon('Search'))
    
    utils.eod()

@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return
    
    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    
    search_url = f'{site.url}/?s={search_text}'
    getMovies(search_url)

@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='movies')
        return
    
    # Esseq items live in a block-post wrapper; image is in data-img
    pattern = r'class="block-post">\s*<a href="([^"]+)" title="([^"]+)".*?data-img="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} items')
    
    if matches:
        for movie_url, title, image in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Clean image URL
            full_image = image.strip()
            
            if title:
                site.add_dir(title, movie_url, 'getLinks', full_image,
                           year=year, media_type='movie')
    
    # Pagination - site uses custom &rsaquo; next link with single quotes
    next_match = re.search(r"<a[^>]+href='([^']+)'[^>]*>\s*&rsaquo;\s*</a>", html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))

    utils.eod(content='movies')

@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    utils.kodilog(f'{site.title}: Getting series from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: ERROR - No HTML received from {url}')
        utils.eod(content='tvshows')
        return
    
    utils.kodilog(f'{site.title}: Received {len(html)} bytes of HTML')
    
    # Series cards live in block-post; poster is a background-image on .imgSer
    pattern = r'class="block-post">\s*<a href="([^"]+)" title="([^"]+)".*?background-image:\s*url\(([^\)]+)\)'
    matches = re.findall(pattern, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} raw items')
    
    seen_titles = set()
    
    if matches:
        for series_url, title, image in matches:
            # Clean title
            title = title.strip()
            # Strip "- قصة عشق" from title
            title = re.sub(r'\s*-\s*قصة عشق\s*$', '', title)
            title = re.sub(r'مشاهدة|مسلسل|مترجم|مترجمة|اون لاين|HD|كامل|كاملة', '', title).strip()
            
            # Extract year
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            # Strip episode suffix to get show title for deduplication
            show_title = re.split(r'\s*(?:الحلقة|حلقة)\s*\d+', title)[0].strip()
            show_title = re.sub(r'\s+', ' ', show_title).strip()
            
            if not show_title or show_title in seen_titles:
                continue
            seen_titles.add(show_title)
            
            # Clean image URL
            full_image = image.strip()
            
            # Convert episode URL to series/season URL to show all seasons
            # URLs like /series/name-sb1-ep-01/ should become /series/name-s01/
            season_url = series_url
            if '/ep-' in series_url:
                # Convert to season URL by removing episode part
                season_url = re.sub(r'-ep-\d+/$', '/', series_url)
                season_url = re.sub(r'/sb(\d+)/', r'/s0\1/', season_url)  # sb1 -> s01
                season_url = re.sub(r'/de-(\d+)/', r'/s0\1/', season_url)  # de-01 -> s01
            
            # Series pages go to getSeasons to show season selector
            site.add_dir(show_title, season_url, 'getSeasons', full_image,
                       year=year, media_type='tvshow')
    
    # Pagination - site uses custom pagination with class='inactive'
    next_match = re.search(r"<a[^>]+href='([^']+)'[^>]*>\s*&rsaquo;\s*</a>", html)
    if next_match:
        next_url = next_match.group(1)
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')

@site.register()
def getSeasons(url, name=''):
    """Get seasons for a series"""
    utils.kodilog(f'{site.title}: Getting seasons from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='tvshows')
        return
    
    # Check if page has season selector
    seasons = re.findall(r'<li[^>]*data-season="([^"]+)"[^>]*>([^<]+)</li>', html)
    
    if seasons:
        utils.kodilog(f'{site.title}: Found {len(seasons)} seasons')
        
        # Extract series image
        poster_match = re.search(r'background-image:\s*url\(([^\)]+)\)', html)
        series_image = poster_match.group(1) if poster_match else site.image
        
        for season_id, season_name in seasons:
            season_name = season_name.strip()
            # Create season URL by appending season ID
            season_url = url.rstrip('/') + f'?season={season_id}'
            site.add_dir(season_name, season_url, 'getEpisodes', series_image, media_type='season')
    else:
        # No seasons selector, show episodes directly
        utils.kodilog(f'{site.title}: No seasons found, showing episodes')
        getEpisodes(url, name)
    
    utils.eod(content='tvshows')

@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series or season"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod(content='episodes')
        return
    
    # Series/season detail pages list episodes as <a class="epNum" ...>
    pattern = r'class="epNum"[^>]*href="([^"]+)"[^>]*title="([^"]+)"'
    matches = re.findall(pattern, html)

    if matches:
        utils.kodilog(f'{site.title}: Found {len(matches)} episodes')
        for ep_url, ep_title in matches:
            ep_title = ep_title.strip()
            ep_title = re.sub(r'\s*-\s*قصة عشق\s*$', '', ep_title)

            ep_num = ''
            ep_match = re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', ep_title, re.IGNORECASE)
            if ep_match:
                ep_num = ep_match.group(1)

            if ep_title:
                site.add_dir(ep_title, ep_url, 'getLinks', site.image,
                           episode=ep_num, media_type='episode')
    else:
        # Homepage "Latest Episodes" feed - article block-post cards with data-img
        home_pattern = r'class="block-post">\s*<a href="([^"]+)" title="([^"]+)".*?data-img="([^"]+)"'
        home_matches = re.findall(home_pattern, html, re.DOTALL)
        utils.kodilog(f'{site.title}: Found {len(home_matches)} latest episodes')

        for ep_url, ep_title, ep_img in home_matches:
            ep_title = ep_title.strip()
            ep_title = re.sub(r'\s*-\s*قصة عشق\s*$', '', ep_title)

            ep_num = ''
            ep_match = re.search(r'(?:الحلقة|حلقة|Episode|EP)\s*(\d+)', ep_title, re.IGNORECASE)
            if ep_match:
                ep_num = ep_match.group(1)

            if ep_title:
                site.add_dir(ep_title, ep_url, 'getLinks', ep_img.strip(),
                           episode=ep_num, media_type='episode')

    # Pagination - &rsaquo; next link (single quotes)
    next_match = re.search(r"<a[^>]+href='([^']+)'[^>]*>\s*&rsaquo;\s*</a>", html)
    if next_match:
        site.add_dir('Next Page', next_match.group(1), 'getEpisodes', addon_image(site.img_next))

    utils.eod(content='episodes')

@site.register()
def getLinks(url, name=''):
    """Extract video links from episode/movie page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)

    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    hoster_manager = get_hoster_manager()
    servers_added = 0

    # Embed links are stored inside a base64-encoded JSON "watch" form param,
    # e.g. {"v": "https://v.vidsp.net/embed-xxx.html", "uqload": "https://uqload.is/e/yyy"}
    video_links = []
    for val in re.findall(r'name="watch"\s+value="([^"]+)"', html):
        try:
            data = json.loads(base64.b64decode(val).decode('utf-8'))
        except Exception:
            continue
        if isinstance(data, dict):
            for v in data.values():
                if isinstance(v, str) and v.strip().lower().startswith('http'):
                    video_links.append(v.strip())

    # Fallback: direct external host links anywhere on the page
    if not video_links:
        link_pattern = r'href="([^"]+(?:vidsp|ok\.ru|uqload|voe|dood|streamtape|mixdrop)[^"]+)"'
        video_links = re.findall(link_pattern, html, re.IGNORECASE)

    utils.kodilog(f'{site.title}: Found {len(video_links)} potential video links')

    seen = set()
    if video_links:
        for video_url in video_links:
            video_url = video_url.strip()

            if not video_url or video_url in seen:
                continue
            seen.add(video_url)

            # Skip social media links
            if any(x in video_url.lower() for x in ['facebook', 'twitter', 'instagram', 'youtube', 'google']):
                continue

            # Server name from the embed host
            server_name = re.sub(r'^https?://(www\.)?', '', video_url).split('/')[0]

            label, should_skip = utils.format_resolver_link(
                hoster_manager,
                video_url,
                site.title,
                name,
                quality=server_name
            )

            if not should_skip:
                basics.addDownLink(label, video_url, f'{site.name}.PlayVid', site.image)
                servers_added += 1

    utils.kodilog(f'{site.title}: Added {servers_added} servers')
    
    if servers_added == 0:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
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
