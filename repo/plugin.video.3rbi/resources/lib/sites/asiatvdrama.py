# -*- coding: utf-8 -*-
"""
AsiaTVDrama Site Module
https://asiatvdrama.com

Asian (Korean/Chinese/Japanese/Thai/Taiwanese) drama + Asian movies.
Structure (WordPress custom post types, verified live):
  - listing card:  <div class="block-post2"><a href=".../drama/..">  (shows + movies)
  - drama page  ->  <ul class="list-seasons"> links to .../seasons/..
  - seasons page -> <ul class="eplist2 list-eps"> links to .../episodes/..
                    (present server-side for shows that have aired episodes;
                     upcoming dramas render an empty/absent list)
  - episode page -> only episodes with an uploaded video carry the watch form:
                    <form action="https://asiawiki.me"><input name="epwatch" value="ID">
  - watch backend: GET {action}/wp-admin/admin-ajax.php?action=fetch_episode&id=ID
                   -> JSON {"servers": {name: "<iframe src=..>"}, "episiodes": [..],
                            "seasons": {..}, "downloads": [..]}
Mechanism re-verified live; episodes/servers are scrapable headless (no JS).
"""

import re
import json
import urllib.parse as urllib_parse
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager
from resources.lib.category_mapper import get_category_icon

site = SiteBase('asiatvdrama', 'AsiaTVDrama', url=None, image='sites/asiatvdrama.png')

# Listing card: drama (show/movie) poster blocks
LIST_PATTERN = (r'<div class="block-post2">\s*<a href="([^"]+)" title="([^"]+)">'
                r'\s*<div class="blockImg">\s*<img[^>]*data-img="([^"]+)"')
NEXT_PATTERN = r'<a class="next page-numbers" href="([^"]+)"'

# Junk words to strip from titles
_JUNK = (r'مشاهدة|مسلسل|فيلم|انمي|أنمي|مترجمة|مترجم|مدبلجة|مدبلج|كاملة|كامل|'
         r'اون لاين|أون لاين|HD|الكوري|الكورية|الصيني|الصينية|الياباني|اليابانية|'
         r'التايلاندي|التايلاندية|التايواني|التايوانية|الاسيوي|الاسيوية')


def _clean_title(title):
    title = title.strip()
    title = re.sub(_JUNK, '', title).strip()
    title = re.sub(r'\s+', ' ', title).strip(' -|/')
    return title


def _extract_year(title):
    year = ''
    m = re.search(r'(19|20)\d{2}', title)
    if m:
        year = m.group(0)
        title = title.replace(year, '').strip()
    return title, year


def _list_dramas(html, route_mode):
    """Parse drama/movie listing cards and add them as directories."""
    matches = re.findall(LIST_PATTERN, html, re.DOTALL)
    utils.kodilog(f'{site.title}: Found {len(matches)} items')

    for drama_url, title, image in matches:
        title = _clean_title(title)
        title, year = _extract_year(title)
        if not title:
            continue
        site.add_dir(title, drama_url, route_mode, image, year=year, media_type='tvshow')

    return len(matches)


@site.register(default_mode=True)
def Main():
    """Main menu"""
    base = site.url
    site.add_dir('Korean TV Shows', site.url + '/types/الدراما-الكورية/', 'getTVShows', get_category_icon('Korean TV Shows') or site.image)
    site.add_dir('Chinese TV Shows', site.url + '/types/الدراما-الصينية/', 'getTVShows', get_category_icon('Chinese TV Shows') or site.image)
    site.add_dir('Japanese TV Shows', site.url + '/types/الدراما-اليابانية/', 'getTVShows', get_category_icon('Japanese TV Shows') or site.image)
    site.add_dir('Thai TV Shows', site.url + '/types/الدراما-التايلندية/', 'getTVShows', get_category_icon('Thai TV Shows') or site.image)
    site.add_dir('Taiwanese TV Shows', site.url + '/types/الدراما-التايونية/', 'getTVShows', get_category_icon('Taiwanese TV Shows') or site.image)
    site.add_dir('Asian Movies', site.url + '/types/افلام-اسيوية/', 'getTVShows', get_category_icon('Asian Movies') or site.image)
    site.add_dir('Search', '', 'search', get_category_icon('Search') or site.image)
    utils.eod()


@site.register()
def search():
    """Search via the WordPress ?s= page (returns drama/movie cards)."""
    search_text = utils.get_search_input()
    if not search_text:
        utils.eod(content='tvshows')
        return

    utils.kodilog(f'{site.title}: Searching for: {search_text}')
    search_url = site.url + '/?s=' + urllib_parse.quote(search_text)

    html = utils.getHtml(search_url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='tvshows')
        return

    found = _list_dramas(html, 'getSeasons')
    if not found:
        utils.notify(site.title, 'لا توجد نتائج', icon=site.image)

    utils.eod(content='tvshows')


@site.register()
def getTVShows(url):
    """List drama shows / movies for a category (types) page."""
    utils.kodilog(f'{site.title}: Getting shows from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod(content='tvshows')
        return

    _list_dramas(html, 'getSeasons')

    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getTVShows', addon_image(site.img_next))

    utils.eod(content='tvshows')


@site.register()
def getSeasons(url, name=''):
    """Drama (show) page -> list its seasons.

    Single-season shows / movies collapse straight to the episode list.
    """
    utils.kodilog(f'{site.title}: Getting seasons from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='seasons')
        return

    block = re.search(r'<ul class="list-seasons">(.*?)</ul>', html, re.DOTALL)
    seasons = []
    if block:
        seasons = re.findall(r'<a href="(https?://[^"]+/seasons/[^"]+)"[^>]*>\s*([^<]+?)\s*</a>',
                             block.group(1), re.DOTALL)

    utils.kodilog(f'{site.title}: Found {len(seasons)} seasons')

    # Single season (or movie) -> skip a level, show episodes directly.
    if len(seasons) == 1:
        getEpisodes(seasons[0][0], name=name)
        return

    if not seasons:
        # Fallback: treat the page itself as the season container.
        getEpisodes(url, name=name)
        return

    for season_url, season_name in seasons:
        season_name = re.sub(r'\s+', ' ', season_name).strip() or 'موسم'
        site.add_dir(season_name, season_url, 'getEpisodes', site.image, media_type='season')

    utils.eod(content='seasons')


@site.register()
def getEpisodes(url, name=''):
    """Seasons page -> list episodes."""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.eod(content='episodes')
        return

    block = re.search(r'<ul class="eplist2 list-eps">(.*?)</ul>', html, re.DOTALL)
    content = block.group(1) if block else html

    ep_pat = r'<a href="(https?://[^"]+/episodes/[^"]+)"[^>]*title="([^"]*)"'
    episodes = re.findall(ep_pat, content, re.DOTALL)
    # Fallback: if the scoped list yielded nothing but the page still carries
    # episode links (markup drift), scan the whole document.
    if not episodes and block:
        episodes = re.findall(ep_pat, html, re.DOTALL)
    # De-duplicate while preserving order (the list can repeat the active item).
    _seen = set()
    episodes = [(u, t) for (u, t) in episodes if not (u in _seen or _seen.add(u))]

    utils.kodilog(f'{site.title}: Found {len(episodes)} episodes')

    for ep_url, ep_title in episodes:
        ep_title = re.sub(r'\s+', ' ', ep_title).strip()
        ep_num = ''
        m = re.search(r'(\d+)', ep_title)
        if m:
            ep_num = m.group(1)
        if not ep_title:
            ep_title = f'الحلقة {ep_num}' if ep_num else 'الحلقة'
        site.add_dir(ep_title, ep_url, 'getLinks', site.image, episode=ep_num, media_type='episode')

    if not episodes:
        utils.notify(site.title, 'لم يتم العثور على حلقات', icon=site.image)

    # Pagination (long-running shows)
    next_match = re.search(NEXT_PATTERN, html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getEpisodes', addon_image(site.img_next))

    utils.eod(content='episodes')


@site.register()
def getLinks(url, name=''):
    """Episode page -> resolve watch backend -> list server embeds."""
    utils.kodilog(f'{site.title}: Getting links from: {url}')

    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod(content='videos')
        return

    # Aired episodes carry a watch form that posts an episode id to an external
    # backend (currently asiawiki.me). Derive the backend host from the form's
    # own action so a backend-domain migration doesn't break playback -- never
    # hardcode it. The form is absent on premium ("العضوية الذهبية") episodes,
    # which is why getLinks can legitimately yield nothing.
    form_block = ''
    for fb in re.findall(r'<form\b[^>]*>.*?</form>', html, re.DOTALL | re.IGNORECASE):
        if 'epwatch' in fb:
            form_block = fb
            break

    # epwatch id -- accept either input attribute order (name/value or value/name).
    scope = form_block or html
    id_match = (re.search(r'name=["\']epwatch["\'][^>]*value=["\'](\d+)["\']', scope, re.IGNORECASE)
                or re.search(r'value=["\'](\d+)["\'][^>]*name=["\']epwatch["\']', scope, re.IGNORECASE))
    ep_id = id_match.group(1) if id_match else ''

    # backend = the form action (domain-agnostic); asiawiki.me only as last resort.
    act = re.search(r'\baction=["\'](https?://[^"\']+)["\']', form_block, re.IGNORECASE)
    backend = act.group(1) if act else 'https://asiawiki.me'

    if not ep_id:
        gated = ('العضوية' in html) or ('العضويات' in html)
        msg = 'حلقة للأعضاء فقط (اشتراك مدفوع)' if gated else 'لم يتم العثور على روابط'
        utils.kodilog(f'{site.title}: No epwatch id found (premium={gated})')
        utils.notify(site.title, msg, icon=site.image)
        utils.eod(content='videos')
        return

    ajax_url = '%s/wp-admin/admin-ajax.php?action=fetch_episode&id=%s' % (backend.rstrip('/'), ep_id)
    data_html = utils.getHtml(ajax_url, headers={'User-Agent': utils.USER_AGENT, 'Referer': backend})

    servers = {}
    if data_html:
        try:
            servers = json.loads(data_html).get('servers') or {}
        except (ValueError, AttributeError):
            utils.kodilog(f'{site.title}: Failed to parse fetch_episode JSON')

    hoster_manager = get_hoster_manager()
    count = 0
    for server_name, iframe in servers.items():
        m = re.search(r'src=["\']([^"\']+)["\']', iframe, re.IGNORECASE)
        if not m:
            continue
        embed_url = m.group(1).strip()
        if embed_url.startswith('//'):
            embed_url = 'https:' + embed_url
        if not embed_url.startswith('http'):
            continue

        label, should_skip = utils.format_resolver_link(
            hoster_manager, embed_url, site.title, name, quality=str(server_name).strip())
        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)
            count += 1

    utils.kodilog(f'{site.title}: Found {count} servers')
    if not count:
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
