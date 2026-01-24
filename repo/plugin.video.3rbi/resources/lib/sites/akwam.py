from resources.lib.site_base import SiteBase
from resources.lib import utils
from resources.lib.basics import addon, addon_image, aksvicon
from resources.lib.hoster_resolver import get_hoster_manager
import re
import xbmc
import os

site = SiteBase(name='akwam', title='Akwam', url=None, image='sites/AKSV.png')

@site.register(default_mode=True)
def Main():
    from resources.lib.category_mapper import get_category_icon

    site.add_dir('Movies', '{0}/movies'.format(site.url), 'getMovies', _get_cat_icon('Movies'), fanart=site.image, landscape=site.image)
    site.add_dir('Series', '{0}/series'.format(site.url), 'getTVShows', _get_cat_icon('Series'), fanart=site.image, landscape=site.image)
    site.add_dir('TV Shows', '{0}/shows'.format(site.url), 'getTVShows', _get_cat_icon('TV Shows'), fanart=site.image, landscape=site.image)
    site.add_dir('Mix', '{0}/mix'.format(site.url), 'getMovies', _get_cat_icon('Mix'), fanart=site.image, landscape=site.image)
    site.add_dir('Search', '{0}/search'.format(site.url), 'Search', _get_cat_icon('Search'))
    utils.eod()

def _get_cat_icon(title):
    lower_title = title.lower()
    mapping = {
        'movies': 'Movies.png',
        'أفلام': 'Movies.png',
        'افلام': 'Movies.png',
        'series': 'TVShows.png',
        'tv shows': 'TVShows.png',
        'مسلسلات': 'TVShows.png',
        'search': 'Search.png',
        'بحث': 'Search.png',
        'mix': 'Genres.png',
        'cartoon': 'Cartoon.png',
        'كرتون': 'Cartoon.png',
        'anime': 'MoviesAnime.png',
        'انمي': 'MoviesAnime.png',
        'korean': 'MoviesKorean.png',
        'كوري': 'MoviesKorean.png',
        'reality': 'Programs.png',
        'برامج': 'Programs.png'
    }
    
    for key, icon in mapping.items():
        if key in lower_title:
            return addon_image(os.path.join('professional-icon-pack', icon))
            
    # Fallback to general category icon if it's a known icon string
    if title.startswith('addon-'):
        return addon_image(title)
        
    return addon_image(site.image)
    
def _get_high_res_img(url):
    if not url or 'http' not in url:
        return url
    return re.sub(r'/thumb/\d+x\d+/', '/', url)

def _get_plot(html):
    if not html:
        return ""
    # 1. Try meta description first (usually cleanest)
    match = re.search(r'<meta[^>]+name="description"[^>]+content="([^"]+)"', html)
    if not match:
        match = re.search(r'<meta[^>]+property="og:description"[^>]+content="([^"]+)"', html)
    
    if match:
        plot = utils.cleanhtml(match.group(1))
        plot = utils.cleantext(plot)
        # Remove common site prefixes if they exist
        plot = re.sub(r'^(مشاهدة|تحميل|اون لاين|اونلاين)\s*(و|)\s*', '', plot)
        return plot
        
    # 2. Fallback to widget-body
    match = re.search(r'قصة.*?<div class="widget-body">.*?<p>(.*?)</p>', html, re.DOTALL)
    if match:
        return utils.cleantext(utils.cleanhtml(match.group(1)))
        
    return ""

def _extract_year(title):
    """Extract year from title like 'Title (2024)'"""
    match = re.search(r'\((\d{4})\)', title)
    if match:
        return match.group(1)
    return None
    
def _clean_title(title, prefix=None):
    # Mapping Arabic ordinal numbers to numeric strings
    arabic_numbers = {
        'الأولى': '01', 'الاولى': '01', 'اولى': '01',
        'الثانية': '02', 'الثانيه': '02', 'الثايه': '02', 'ثانية': '02',
        'الثالثة': '03', 'الثالثه': '03', 'ثالثة': '03',
        'الرابعة': '04', 'الرابعه': '04', 'رابعة': '04',
        'الخامسة': '05', 'الخامسه': '05', 'خامسة': '05',
        'السادسة': '06', 'السادسه': '06', 'سادسة': '06',
        'السابعة': '07', 'السابعه': '07', 'سابعة': '07',
        'الثامنة': '08', 'الثامنه': '08', 'ثامنة': '08',
        'التاسعة': '09', 'التاسعه': '09', 'تاسعة': '09',
        'العاشرة': '10', 'العاشره': '10', 'عاشرة': '10',
        'الحادية عشر': '11', 'الثانية عشر': '12', 'الثالثة عشر': '13',
        'الرابعة عشر': '14', 'الخامسة عشر': '15', 'السادسة عشر': '16',
        'السابعة عشر': '17', 'الثامنة عشر': '18', 'التاسعة عشر': '19',
        'العشرون': '20'
    }
    
    # Shared Quality & Resolution Terms
    qualities = [
        'WEBRip', 'WEB-DL', 'WEBDL', 'Web-rip', 'Bluray', 'BDrip', 'BD-Rip', 
        'HDTV', 'DVDRIP', 'CAM', 'SCR', 'DVDSC', 'HC', 'HD-HC',
        '4k', '2160p', '1080p', '720p', '480p', '360p', '240p'
    ]
    
    name = utils.cleantext(title)
    
    # Global Replacements
    replacements = {
        'مترجمة': 'SUBBED', 'مترجم': 'SUBBED',
        'مدبلجة': 'Dubbed', 'مدبلج': 'Dubbed',
        'اونلاين': '', 'مشاهدة': '', 'تحميل': '', 'حصري': ''
    }
    for ar, en in replacements.items():
        name = name.replace(ar, en)
    
    # Strip Quality & Resolution Terms
    for q in qualities:
        # Use regex for case-insensitive whole word replacement
        name = re.sub(r'(?i)\b' + re.escape(q) + r'\b', '', name)
    
    # Transform Seasons/Episodes
    # Keywords: الحلقة, الحلقه, حلقة, حلقه, الموسم, موسم, الجزء, جزء
    pattern = r'(?:الحلقه|حلقه|الحلقة|حلقة|الموسم|موسم|الجزء|جزء)\s*([^\s]+)'
    
    def _repl_func(match):
        val = match.group(1).strip()
        number = ""
        if val.isdigit():
            number = "{:02d}".format(int(val))
        else:
            for ar_num, num in arabic_numbers.items():
                if ar_num in val:
                    number = num
                    break
        
        # Determine prefix if not explicitly passed
        current_prefix = prefix
        if not current_prefix:
            if any(k in match.group(0) for k in ['موسم', 'الموسم', 'الجزء', 'جزء']):
                current_prefix = "Season"
            else:
                current_prefix = "Episode"
        
        if number:
            res = "{} {}".format(current_prefix, number)
        else:
            res = "{} {}".format(current_prefix, val)
        
        if prefix:
            return res
        return name.replace(match.group(0), res)

    if prefix:
        # For directory lists (Seasons/Episodes list)
        match = re.search(pattern, name)
        if match:
            return _repl_func(match)
        # Fallback for list name if pattern fails
        return "{} {}".format(prefix, name)
    else:
        # For inline titles (e.g. Movie/Series names containing season info)
        name = re.sub(pattern, _repl_func, name)

    # Final cleanup of spaces and punctuation
    name = re.sub(r'\s+', ' ', name).strip()
    name = re.sub(r'^[-\s:|]+|[-\s:|]+$', '', name)
    return name

def _common_listing(url, next_mode, item_target_mode):
    html = utils.getHtml(url)
    
    # Regex to capture individual entry blocks
    entries = re.compile(r'<div class="entry-box entry-box-1">(.+?)</div>\s*</div>', re.DOTALL).findall(html)

    if not entries:
         utils.kodilog('AKSV: Main regex failed, trying fallback')
         entries = re.compile(r'<div class="entry-box(.*?)</h3', re.DOTALL).findall(html)
    
    utils.kodilog('AKSV: Found {} entries'.format(len(entries)))

    for entry in entries:
        try:
            url_match = re.search(r'href="([^"]+)"', entry)
            img_match = re.search(r'data-src="([^"]+)"', entry)
            title_match = re.search(r'class="entry-title[^"]*">.*?<a[^>]+>(.*?)</a>', entry, re.DOTALL)
            year_match = re.search(r'class="badge badge-pill badge-secondary[^"]*">(\d+)<', entry)
            quality_match = re.search(r'class="label quality">([^<]+)<', entry)
            
            if url_match:
                item_url = url_match.group(1)
                title = utils.cleantext(title_match.group(1)) if title_match else "Unknown"
                img = img_match.group(1) if img_match else ''
                img = _get_high_res_img(img)
                year = year_match.group(1) if year_match else ''
                quality = quality_match.group(1) if quality_match else ''
                
                # Try to extract plot/description from entry if available
                item_desc = ""
                # Try to find description/plot text in the entry
                desc_match = re.search(r'<p[^>]*class="[^"]*text[^"]*"[^>]*>([^<]+)</p>', entry)
                if desc_match:
                    item_desc = utils.cleantext(desc_match.group(1))
                
                # If no description, extract genres/badges as fallback
                if not item_desc:
                    tags = re.findall(r'class="badge badge-pill badge-light[^"]*">([^<]+)<', entry)
                    item_desc = ", ".join(tags) if tags else ""
                
                # Determine mode based on content type or target mode
                target_mode = item_target_mode
                is_series = '/series' in item_url or '/shows' in item_url
                if not target_mode:
                    if is_series:
                        target_mode = 'getSeasons'
                    else:
                        target_mode = 'getLinks'

                # Extract year from title if present in format (YYYY)
                extracted_year = _extract_year(title)
                if not year and extracted_year:
                    year = extracted_year
                
                # Clean title and prepare display title
                clean_title = _clean_title(title)
                original_title = clean_title
                full_title = clean_title
                if year:
                    full_title += " ({})".format(year)
                
                # Strip quality from badge if in restricted list
                show_quality = True
                if quality:
                    qualities = ['WEBRip', 'WEB-DL', 'WEBDL', 'Web-rip', 'Bluray', 'BDrip', 'BD-Rip', 'HDTV', 'DVDRIP', 'CAM', 'SCR', 'DVDSC', 'HC', 'HD-HC', '4k', '2160p', '1080p', '720p', '480p', '360p']
                    if any(q.lower() == quality.lower() for q in qualities):
                        show_quality = False
                    
                    if show_quality:
                        full_title += " [COLOR yellow]{}[/COLOR]".format(quality)

                # If it's a category/genre list (no image yet), use category icon
                if not img:
                    img = _get_cat_icon(title)

                item_img = img if img else site.image
                # Ensure it's a full path if it's a local icon
                if item_img.startswith('addon-'):
                    item_img = addon_image(item_img)
                
                # Determine media type
                media_type = 'tvshow' if is_series else 'movie'
                
                utils.kodilog('AKSV: Adding item - Title: {}, Desc: {}, Year: {}'.format(full_title[:50], item_desc[:50] if item_desc else 'None', year))
                    
                site.add_dir(full_title, item_url, target_mode, item_img, desc=item_desc, fanart=item_img, landscape=item_img,
                            year=year, media_type=media_type, original_title=original_title)
        except:
            pass

    # Pagination
    next_page = re.search(r'<a[^>]+href="([^"]+)"[^>]*rel="next"', html)
    if next_page:
        next_icon = addon_image(site.img_next)
        site.add_dir('Next Page', next_page.group(1), next_mode, next_icon)

    utils.eod()

@site.register()
def getMovies(url):
    _common_listing(url, 'getMovies', 'getLinks')

@site.register()
def getTVShows(url):
    _common_listing(url, 'getTVShows', 'getSeasons')

@site.register()
def getSeasons(url):
    html = utils.getHtml(url)
    plot = _get_plot(html)
    utils.kodilog('AKSV: Scraping seasons for {}'.format(url))
    
    # Extract show title and year from page title or meta tags
    show_title = None
    year = None
    title_match = re.search(r'<title>([^<|]+)', html)
    if title_match:
        page_title = utils.cleantext(title_match.group(1))
        show_title = _clean_title(page_title)
        year = _extract_year(page_title)
    
    # Isolate seasons section if it exists
    # Sections usually start with <div class="header-title">...</div>
    # Seasons header is "المواسم"
    seasons_block = ""
    header_matches = list(re.finditer(r'<div class="header-title">([^<]+)</div>', html))
    for i, match in enumerate(header_matches):
        if "المواسم" in match.group(1):
            start = match.end()
            end = header_matches[i+1].start() if i+1 < len(header_matches) else len(html)
            seasons_block = html[start:end]
            break
            
    if seasons_block:
        seasons = re.compile(r'href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(seasons_block)
        if seasons:
            seen = set()
            cleaned_seasons = []
            for s_url, s_name in seasons:
                if s_url not in seen and '/series/' in s_url:
                    name = _clean_title(s_name, "Season")
                    # Extract season number from name like "Season 01"
                    season_num_match = re.search(r'Season\s+(\d+)', name)
                    season_num = int(season_num_match.group(1)) if season_num_match else None
                    cleaned_seasons.append((name, s_url, season_num))
                    seen.add(s_url)
            
            # Sort ascending by season number
            cleaned_seasons.sort(key=lambda x: x[0])
            
            for name, s_url, season_num in cleaned_seasons:
                icon = addon_image(site.image)
                site.add_dir(name, s_url, 'getEpisodes', icon, desc=plot, fanart=icon, landscape=icon,
                           season=season_num, show_title=show_title, year=year, media_type='season')
            
            utils.eod()
            return

    # Fallback/Direct Listing: assuming it's a season-specific series entry
    utils.kodilog('AKSV: No seasons section found, trying to list episodes directly')
    getEpisodes(url, html, plot, show_title, year)
    utils.eod()

@site.register()
def getEpisodes(url, html=None, plot=None, show_title=None, year=None):
    if not html:
        html = utils.getHtml(url)
    if not plot:
        plot = _get_plot(html)
    utils.kodilog('AKSV: Scraping episodes for {}'.format(url))
    
    # Extract show title and year from page if not provided
    if not show_title:
        title_match = re.search(r'<title>([^<|]+)', html)
        if title_match:
            page_title = utils.cleantext(title_match.group(1))
            show_title = _clean_title(page_title)
            if not year:
                year = _extract_year(page_title)
    
    # Try to extract season number from URL or page title
    season_num = None
    season_match = re.search(r'(?:الموسم|الجزء|الثاني).*?(\d+)', url)
    if not season_match:
        season_match = re.search(r'Season\s+(\d+)', show_title if show_title else '')
    if season_match:
        try:
            season_num = int(season_match.group(1))
        except:
            pass
    
    # Isolate episodes section
    # Episodes header is "الحلقات"
    episodes_block = ""
    header_matches = list(re.finditer(r'<div class="header-title">([^<]+)</div>', html))
    for i, match in enumerate(header_matches):
        if "الحلقات" in match.group(1):
            start = match.end()
            # If there's a next section (like "More"), stop there
            end = header_matches[i+1].start() if i+1 < len(header_matches) else len(html)
            episodes_block = html[start:end]
            break
    
    # If no header found, search for the most likely container
    if not episodes_block:
        # Fallback to broad search if header parsing fails
        episodes_block = html

    # Pattern for episodes (based on bg-primary2 containers found in browser)
    # <h2 or div class="font-size-18 text-white mb-2"><a href="..." class="text-white">Episode Name</a></h2>
    # Followed by <img src="..." 
    entries = re.compile(r'class="bg-primary2.*?href="([^"]+)"[^>]*>(.*?)</a>.*?<img src="([^"]+)"', re.DOTALL).findall(episodes_block)
    
    if not entries:
        # Fallback to previous pattern but only within the isolated block
        entries = re.compile(r'class="bg-primary2.*?href="([^"]+)"[^>]*>(.*?)</a>', re.DOTALL).findall(episodes_block)
        # Wrap in tuple with empty image
        entries = [(e[0], e[1], '') for e in entries]

    if entries:
        cleaned_entries = []
        for item_url, title, item_img in entries:
            item_img = _get_high_res_img(item_img)
            clean_name = _clean_title(title, "Episode")
            # Extract episode number from name like "Episode 01"
            episode_num_match = re.search(r'Episode\s+(\d+)', clean_name)
            episode_num = int(episode_num_match.group(1)) if episode_num_match else None
            # Keep original episode title for episode name
            episode_name = utils.cleantext(title)
            cleaned_entries.append((clean_name, item_url, item_img, episode_num, episode_name))
        
        # Sort ascending by episode number
        cleaned_entries.sort(key=lambda x: x[0])
        
        for name, item_url, item_img, episode_num, episode_name in cleaned_entries:
            if not item_img:
                item_img = addon_image(site.image)
            
            site.add_dir(name, item_url, 'getLinks', item_img, desc=plot, fanart=item_img, landscape=item_img,
                       episode=episode_num, season=season_num, show_title=show_title, year=year, media_type='episode')
    else:
        # Try one last broad search if block parsing was somehow too restrictive
        if episodes_block != html:
             entries = re.compile(r'href="([^"]+/episode/[^"]+)"[^>]*>(.*?)</a>').findall(episodes_block)
             for item_url, title in entries:
                name = utils.cleantext(title)
                site.add_dir(name, item_url, 'getLinks', '', desc=plot, show_title=show_title, year=year)
        
        if not entries:
            utils.notify("Error", "No episodes found", aksvicon)
    
    utils.eod()

@site.register()
def getLinks(url, name):
    html = utils.getHtml(url)
    plot = _get_plot(html)
    utils.kodilog('AKSV: Resolving qualities for {}'.format(name))
    
    # Extract metadata from page for both movies and episodes
    year = None
    show_title = None
    season_num = None
    episode_num = None
    episode_name = None
    original_title = None
    media_type = 'movie'
    
    # Extract from page title
    title_match = re.search(r'<title>([^<|]+)', html)
    if title_match:
        page_title = utils.cleantext(title_match.group(1))
        year = _extract_year(page_title)
        clean_page_title = _clean_title(page_title)
        original_title = clean_page_title
        
        # Check if it's an episode
        if '/episode/' in url or 'الحلقة' in page_title or 'Episode' in clean_page_title:
            media_type = 'episode'
            # Extract episode number
            episode_match = re.search(r'Episode\s+(\d+)', clean_page_title)
            if episode_match:
                episode_num = int(episode_match.group(1))
            episode_name = clean_page_title
            
            # Try to extract show title (remove episode part)
            show_title_match = re.search(r'(.+?)(?:\s+الحلقة|\s+Episode|\s+الموسم|\s+Season)', page_title)
            if show_title_match:
                show_title = _clean_title(show_title_match.group(1))
            else:
                show_title = clean_page_title
            
            # Try to extract season number from URL or title
            season_match = re.search(r'(?:الموسم|الجزء|الثاني).*?(\d+)', url)
            if not season_match:
                season_match = re.search(r'Season\s+(\d+)', page_title)
            if season_match:
                try:
                    season_num = int(season_match.group(1))
                except:
                    pass
    
    # Scrape Qualities and Sizes from the tabs
    # 1. Find the tabs to get labels
    tabs = re.findall(r'<a href="#(tab-\d+)"[^>]*>([^<]+)</a>', html)
    
    if not tabs:
        # Fallback to general watch links if no tabs
        watch_links = re.findall(r'href="(https?://go\.ak\.sv/watch/\d+)"', html)
        if watch_links:
            for w_url in watch_links:
                site.add_download_link('Watch Video', w_url, 'PlayVid', '', plot,
                                     year=year, show_title=show_title, season=season_num, episode=episode_num,
                                     media_type=media_type, original_title=original_title, episode_name=episode_name)
            utils.eod()
            return

    # Get settings for icon display and filtering
    hoster_manager = get_hoster_manager()
    
    found_links = False
    for tab_id, quality in tabs:
        # 2. Find the content block for this tab
        # Pattern: <div class="tab-content ..." id="tab-id"> ... 1.3 GB ... link-show ...
        block_match = re.search(r'id="{}"(.*?)</div>\s*</div>'.format(tab_id), html, re.DOTALL)
        if block_match:
            block = block_match.group(1)
            watch_url_match = re.search(r'class="link-btn link-show[^"]*"[^>]*href="([^"]+)"', block)
            size_match = re.search(r'class="font-size-14[^"]*">([^<]+)<', block)
            
            if watch_url_match:
                watch_url = watch_url_match.group(1)
                
                # Format link with icon and check filtering (quality without size)
                label, should_skip = utils.format_resolver_link(
                    hoster_manager,
                    watch_url,
                    'AKSV',
                    name,
                    quality
                )
                
                if should_skip:
                    utils.kodilog('AKSV: Filtered out: {}'.format(watch_url[:100]))
                    continue
                
                site.add_download_link(label, watch_url, 'PlayVid', site.image, desc=plot, fanart=site.image, landscape=site.image,
                                     year=year, show_title=show_title, season=season_num, episode=episode_num,
                                     media_type=media_type, original_title=original_title, episode_name=episode_name)
                found_links = True

    if not found_links:
        # One last fallback: just find all watch links
        watch_links = re.findall(r'href="(https?://go\.ak\.sv/watch/\d+)"', html)
        for i, w_url in enumerate(watch_links):
            label = "AKSV | Unknown | N/A | {} #{}".format(name, i+1)
            site.add_download_link(label, w_url, 'PlayVid', '', plot,
                                 year=year, show_title=show_title, season=season_num, episode=episode_num,
                                 media_type=media_type, original_title=original_title, episode_name=episode_name)

    utils.eod()

@site.register()
def PlayVid(url, name, download=None):
    """Play video - resolve AKSV URL using hoster resolver"""
    utils.kodilog('AKSV: Attempting to resolve: {}'.format(url[:100]))
    
    hoster_manager = get_hoster_manager()
    
    # Try to resolve with hoster manager
    result = hoster_manager.resolve(url, referer=site.url)
    
    if result:
        video_url = result['url']
        headers = result.get('headers', {})
        
        # Format headers for URL (Kodi accepts headers in URL format)
        if headers:
            header_str = '|' + '&'.join(['{}={}'.format(k, v) for k, v in headers.items()])
            video_url = video_url + header_str
        
        utils.kodilog('AKSV: Resolved to: {}'.format(video_url[:100]))
    else:
        utils.kodilog('AKSV: Resolver failed, trying direct playback')
        video_url = url
    
    vp = utils.VideoPlayer(name, download)
    vp.play_from_direct_link(video_url)


@site.register()
def Search(url, page=None, keyword=None):
    if not keyword:
        keyboard = xbmc.Keyboard('', 'Search AKSV')
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            keyword = keyboard.getText()
    
    if keyword:
        search_url = '{0}/search?q={1}'.format(site.url, keyword.replace(' ', '+'))
        # We don't know if search result is movie or show, _common_listing will handle it
        _common_listing(search_url, 'Search', None)


