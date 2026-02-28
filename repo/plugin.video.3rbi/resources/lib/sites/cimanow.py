# -*- coding: utf-8 -*-
"""
CimaNow Site Module
https://cimanow.cc/
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('cimanow', 'CimaNow', url=None, image='sites/cimanow.png')


@site.register(default_mode=True)
def Main():
    """Main menu"""
    # Movies
    site.add_dir('أفلام عربية', site.url + '/category/افلام-عربية/', 'getMovies', get_category_icon('Arabic Movies'))
    site.add_dir('أفلام أجنبية', site.url + '/category/افلام-اجنبية/', 'getMovies', get_category_icon('English Movies'))
    site.add_dir('أفلام تركية', site.url + '/category/افلام-تركية/', 'getMovies', get_category_icon('Turkish Movies'))
    site.add_dir('أفلام هندية', site.url + '/category/افلام-هندية/', 'getMovies', get_category_icon('Indian Movies'))
    site.add_dir('أفلام كرتون', site.url + '/category/افلام-انيميشن/', 'getMovies', get_category_icon('Cartoon Movies'))
    
    # TV Shows
    site.add_dir('مسلسلات عربية', site.url + '/category/مسلسلات-عربية/', 'getTVShows', get_category_icon('Arabic TV Shows'))
    site.add_dir('مسلسلات أجنبية', site.url + '/category/مسلسلات-اجنبية/', 'getTVShows', get_category_icon('English TV Shows'))
    site.add_dir('مسلسلات تركية', site.url + '/category/مسلسلات-تركية/', 'getTVShows', get_category_icon('Turkish TV Shows'))
    site.add_dir('مسلسلات كرتون', site.url + '/category/مسلسلات-انيميشن/', 'getTVShows', get_category_icon('Cartoon TV Shows'))
    
    # Other Categories
    site.add_dir('برامج تلفزيونية', site.url + '/category/البرامج-التلفزيونية/', 'getTVShows', get_category_icon('TV Programs'))
    site.add_dir('مسرحيات', site.url + '/category/مسرحيات/', 'getMovies', get_category_icon('Theater'))
    
    # Ramadan
    site.add_dir('مسلسلات رمضان 2026', site.url + '/category/رمضان-2026/', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    site.add_dir('مسلسلات رمضان 2025', site.url + '/category/رمضان-2025/', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    site.add_dir('مسلسلات رمضان 2024', site.url + '/category/رمضان-2024/', 'getTVShows', get_category_icon('Ramadan TV Shows'))
    
    # Search
    site.add_dir('بحث', '', 'search', get_category_icon('Search'))
    
    utils.eod()


@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='movies')
        return
    
    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    
    # Regular search with GET
    search_url = site.url + '/?s=' + utils.quote(search_text)
    html = utils.getHtml(search_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No search results')
        utils.eod(content='movies')
        return
    
    # Search results have different structure: <a href="URL"> with <li aria-label="title">TITLE</li> and <img src="...">
    # Pattern: <a href="URL">...<li aria-label="year">YEAR</li>...<li aria-label="title">TITLE</li>...<img src="IMAGE">
    pattern = r'<a href="([^"]+)"[^>]*>.*?<li aria-label="year">([^<]*)</li>.*?<li aria-label="title">([^<]+)</li>.*?<img[^>]*src="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} search results')
    
    if matches:
        for result_url, year, title, image in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مسلسل|انمي|مترجم|مترجمة|مدبلج|كامل|كاملة|اون لاين|HD', '', title).strip()
            
            # Year already extracted from pattern
            year = year.strip() if year else ''
            
            if title:
                # Route based on URL type - series use /selary/ in URL
                if '/selary/' in result_url or '/serie' in result_url or '/مسلسلات' in result_url:
                    site.add_dir(title, result_url, 'getEpisodes', image, year=year, media_type='tvshow')
                else:
                    site.add_dir(title, result_url, 'getLinks', image, year=year, media_type='movie')
    else:
        utils.notify(site.title, 'لا توجد نتائج', icon=site.image)
    
    utils.eod(content='movies')


@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='movies')
        return
    
    # Two-step parsing: extract articles first, then parse each one
    articles = re.findall(r'<article[^>]*aria-label="post"[^>]*>(.*?)</article>', html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(articles)} movies')
    
    for article in articles:
        # Extract href
        href_match = re.search(r'<a href="([^"]+)"', article)
        movie_url = href_match.group(1) if href_match else ''
        
        # Extract year
        year_match = re.search(r'<li aria-label="year">([^<]+)</li>', article)
        year = year_match.group(1).strip() if year_match else ''
        
        # Extract title
        title_match = re.search(r'<li aria-label="title">\s*([^<]+)', article)
        title = title_match.group(1).strip() if title_match else ''
        
        # Extract image data-src
        img_match = re.search(r'data-src="([^"]+)"', article)
        image = img_match.group(1) if img_match else ''
        
        # Clean title
        title = re.sub(r'مشاهدة|فيلم|مسلسل|انمي|مترجم|مترجمة|مدبلج|كامل|كاملة|اون لاين|HD', '', title).strip()
        
        if title and movie_url:
            site.add_dir(title, movie_url, 'getLinks', image, year=year, media_type='movie')
    
    # Pagination - look for /page/2/ link on first page, or increment page number
    current_page = 1
    page_match = re.search(r'/page/(\d+)/?$', url)
    if page_match:
        current_page = int(page_match.group(1))
    
    next_page = current_page + 1
    next_url = None
    
    # Find link to next page
    page_pattern = f'/page/{next_page}/'
    next_match = re.search(f'<a[^>]+href="([^"]*{page_pattern}[^"]*)"', html)
    if next_match:
        next_url = next_match.group(1)
    elif current_page == 1:
        # First page might not have /page/1/ in URL, construct next
        base_url = url.rstrip('/')
        next_url = base_url + '/page/2/'
    
    if next_url:
        site.add_dir('الصفحة التالية', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    utils.kodilog(f'{site.title}: Getting TV shows from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return
    
    # Two-step parsing: extract articles first, then parse each one
    articles = re.findall(r'<article[^>]*aria-label="post"[^>]*>(.*?)</article>', html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(articles)} TV shows')
    
    for article in articles:
        # Extract href
        href_match = re.search(r'<a href="([^"]+)"', article)
        series_url = href_match.group(1) if href_match else ''
        
        # Extract year
        year_match = re.search(r'<li aria-label="year">([^<]+)</li>', article)
        year = year_match.group(1).strip() if year_match else ''
        
        # Extract title
        title_match = re.search(r'<li aria-label="title">\s*([^<]+)', article)
        title = title_match.group(1).strip() if title_match else ''
        
        # Extract image data-src
        img_match = re.search(r'data-src="([^"]+)"', article)
        image = img_match.group(1) if img_match else ''
        
        # Clean title
        title = re.sub(r'مشاهدة|فيلم|مسلسل|انمي|مترجم|مترجمة|مدبلج|كامل|كاملة|اون لاين|HD', '', title).strip()
        
        if title and series_url:
            site.add_dir(title, series_url, 'getEpisodes', image, year=year, media_type='tvshow')
    
    # Pagination - look for /page/2/ link on first page, or increment page number
    current_page = 1
    page_match = re.search(r'/page/(\d+)/?$', url)
    if page_match:
        current_page = int(page_match.group(1))
    
    next_page = current_page + 1
    next_url = None
    
    # Find link to next page
    page_pattern = f'/page/{next_page}/'
    next_match = re.search(f'<a[^>]+href="([^"]*{page_pattern}[^"]*)"', html)
    if next_match:
        next_url = next_match.group(1)
    elif current_page == 1:
        # First page might not have /page/1/ in URL, construct next
        base_url = url.rstrip('/')
        next_url = base_url + '/page/2/'
    
    if next_url:
        site.add_dir('الصفحة التالية', next_url, 'getTVShows', addon_image(site.img_next))
    
    utils.eod(content='tvshows')


@site.register()
def getEpisodes(url):
    """Get episodes for a series"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='episodes')
        return
    
    # Check for seasons section first
    seasons_section = re.search(r'<section aria-label="seasons">(.*?)</section>', html, re.DOTALL)
    
    if seasons_section:
        # Extract season links
        season_html = seasons_section.group(1)
        season_links = re.findall(r'<a href="([^"]+)"[^>]*>([^<]+)<em>\(([^)]+)\)</em></a>', season_html)
        
        # If multiple seasons, show them as list
        if len(season_links) > 1:
            utils.kodilog(f'{site.title}: Found {len(season_links)} seasons')
            for season_url, season_title, ep_count in season_links:
                season_title = season_title.strip()
                site.add_dir(f'{season_title} ({ep_count})', season_url, 'getEpisodes', site.image, media_type='season')
            utils.eod(content='seasons')
            return
        
        # Single season - continue to episodes
        utils.kodilog(f'{site.title}: Single season found, loading episodes')
    
    # Episodes are in <ul id="eps"> with <li><a href="URL">...<em>EP_NUM</em></a></li>
    eps_section = re.search(r'<ul[^>]*id="eps"[^>]*>(.*?)</ul>', html, re.DOTALL)
    
    if not eps_section:
        utils.kodilog(f'{site.title}: No episodes section found, treating as direct link')
        getLinks(url)
        return
    
    eps_html = eps_section.group(1)
    
    # Extract episode links: <a href="URL">...<em>NUMBER</em></a>
    episodes = re.findall(r'<a[^>]*href="([^"]+)"[^>]*>.*?<em>(\d+)</em>', eps_html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')
    
    if episodes:
        # Sort episodes by number (ascending - Episode 1, 2, 3...)
        episodes.sort(key=lambda x: int(x[1]))
        for ep_url, ep_num in episodes:
            site.add_dir(f'الحلقة {ep_num}', ep_url, 'getLinks', site.image, episode=ep_num, media_type='episode')
    else:
        utils.kodilog(f'{site.title}: No episodes found, treating as direct link')
        getLinks(url)
        return
    
    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Extract video links from page"""
    import base64
    
    # Ensure URL ends with /watching/
    if not url.endswith('/watching/'):
        url = url.rstrip('/') + '/watching/'
    
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return
    
    hoster_manager = get_hoster_manager()
    
    # Decode cimanow_HTML_encoder obfuscated content
    # Format: base64 segments separated by dots, each decodes to a number which is ASCII code + offset
    page = html
    offset = 87653  # The offset used by cimanow
    
    encoded_match = re.search(r"var hide_my_HTML_\s*=\s*(.+?);", html, re.DOTALL)
    if encoded_match:
        encoded_raw = encoded_match.group(1)
        # Extract all base64 segments
        segments_raw = re.findall(r'([A-Za-z0-9+/]{6,})', encoded_raw)
        
        decoded = ''
        for seg in segments_raw:
            try:
                padded = seg + '=' * (4 - len(seg) % 4) if len(seg) % 4 else seg
                decoded_bytes = base64.b64decode(padded)
                num = int(decoded_bytes.decode('utf-8'))
                char_code = num - offset
                if 0 <= char_code < 0x110000:
                    decoded += chr(char_code)
            except:
                pass
        
        if decoded:
            page = decoded
            utils.kodilog(f'{site.title}: Decoded {len(page)} chars')
    
    found_servers = False
    
    # Pattern 1: Iframe embeds (like vkvideo.ru)
    iframe_pattern = r'<iframe[^>]*src="([^"]+)"'
    iframes = re.findall(iframe_pattern, page)
    utils.kodilog(f'{site.title}: Found {len(iframes)} iframes')
    
    for iframe_url in iframes:
        if iframe_url.startswith('//'):
            iframe_url = 'https:' + iframe_url
        if iframe_url.startswith('http'):
            found_servers = True
            hoster_name = iframe_url.split('/')[2] if '/' in iframe_url else 'Embed'
            basics.addDownLink(hoster_name, iframe_url, f'{site.name}.PlayVid', site.image)
    
    # Pattern 2: AJAX servers via data-id and data-index
    data_id_match = re.search(r'data-id="([^"]+)"', page)
    if data_id_match:
        data_id = data_id_match.group(1)
        data_indices = re.findall(r'data-index="([^"]+)"', page)
        utils.kodilog(f'{site.title}: Found {len(data_indices)} AJAX servers with id={data_id}')
        
        for data_index in data_indices:
            ajax_url = f"{site.url}/wp-content/themes/Cima%20Now%20New/core.php?action=switch&index={data_index}&id={data_id}"
            found_servers = True
            basics.addDownLink(f'Server {data_index}', ajax_url, f'{site.name}.PlayVid', site.image)
    
    # Pattern 3: Download links with server names
    dl_pattern = r'<a href="([^"]+)"[^>]*><i[^>]*class="[^"]*download[^"]*"[^>]*></i>([^<]+)<p'
    dl_matches = re.findall(dl_pattern, page)
    utils.kodilog(f'{site.title}: Found {len(dl_matches)} download servers')
    
    for server_url, server_name in dl_matches:
        server_url = server_url.strip()
        server_name = server_name.strip().replace('</i>', '') or 'Server'
        if server_url.startswith('//'):
            server_url = 'https:' + server_url
        
        found_servers = True
        label, should_skip = utils.format_resolver_link(
            hoster_manager, server_url, site.title, name, quality=server_name
        )
        if not should_skip:
            basics.addDownLink(label, server_url, f'{site.name}.PlayVid', site.image)
    
    # Pattern 4: Direct download links
    direct_pattern = r'<a href="([^"]+)"[^>]*><i class="fa fa-download">'
    direct_links = re.findall(direct_pattern, page)
    
    for link_url in direct_links:
        if link_url.startswith('//'):
            link_url = 'https:' + link_url
        if link_url.startswith('http'):
            found_servers = True
            hoster_name = link_url.split('/')[2] if '/' in link_url else 'Download'
            basics.addDownLink(hoster_name, link_url, f'{site.name}.PlayVid', site.image)
    
    if not found_servers:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=''):
    """Resolve and play video"""
    import urllib.parse
    utils.kodilog(f'{site.title}: Resolving URL: {url[:100]}')
    
    hoster_manager = get_hoster_manager()
    
    # Handle AJAX endpoint (core.php) that returns iframe directly
    if 'core.php' in url and 'action=switch' in url:
        utils.kodilog(f'{site.title}: Fetching AJAX endpoint')
        ajax_html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
        
        if ajax_html:
            # Extract iframe URL from response
            iframe_match = re.search(r'<iframe[^>]*src="([^"]+)"', ajax_html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                if iframe_url.startswith('//'):
                    iframe_url = 'https:' + iframe_url
                utils.kodilog(f'{site.title}: Extracted iframe: {iframe_url[:100]}')
                
                # Fetch iframe content with referer (required to avoid 403)
                iframe_html = utils.getHtml(iframe_url, headers={'User-Agent': utils.USER_AGENT, 'Referer': site.url})
                
                if iframe_html:
                    # Extract MP4 URLs from Playerjs config
                    mp4_urls = re.findall(r'(/uploads/[^\"]+\.mp4)', iframe_html)
                    
                    if mp4_urls:
                        # Get iframe domain for full URL
                        iframe_domain = iframe_url.split('/e/')[0]
                        
                        # Find highest quality (1080p > 720p > 480p > 360p)
                        best_url = None
                        for quality in ['1080p', '720p', '480p', '360p']:
                            for mp4 in mp4_urls:
                                if f'-{quality}.mp4' in mp4:
                                    best_url = iframe_domain + mp4
                                    break
                            if best_url:
                                break
                        
                        if best_url:
                            # URL encode the path (spaces, brackets, etc.)
                            encoded_url = urllib.parse.quote(best_url, safe=':/')
                            utils.kodilog(f'{site.title}: Playing MP4: {encoded_url[:100]}')
                            
                            # Play with headers (Referer required to avoid 403)
                            vp = utils.VideoPlayer(name, False)
                            vp.play_from_direct_link(encoded_url + f'|Referer={site.url}&User-Agent={utils.USER_AGENT}')
                            return
                    
                    # Fallback: try to resolve through hoster manager
                    utils.kodilog(f'{site.title}: No MP4 found, trying hoster resolver')
                    result = hoster_manager.resolve(iframe_url, referer=site.url)
                    if result and result.get('url'):
                        video_url = result['url']
                        vp = utils.VideoPlayer(name, False)
                        vp.play_from_direct_link(video_url)
                        return
                
                utils.notify(site.title, 'لم يتم العثور على رابط الفيديو', icon=site.image)
                return
            else:
                utils.notify(site.title, 'لم يتم العثور على رابط الفيديو', icon=site.image)
                return
    
    # Fix protocol-relative URLs
    if url.startswith('//'):
        url = 'https:' + url
    
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result and result.get('url'):
        video_url = result['url']
        utils.kodilog(f'{site.title}: Playing: {video_url[:100]}')
        
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.notify(site.title, 'فشل تشغيل الفيديو', icon=site.image)
