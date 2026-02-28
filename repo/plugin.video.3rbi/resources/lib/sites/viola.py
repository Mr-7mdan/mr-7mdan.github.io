# -*- coding: utf-8 -*-
"""
VioLa Site Module
https://vio-la.com
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase("viola", "VioLa", url=None, image="sites/viola.png")


@site.register(default_mode=True)
def Main():
    """Main menu"""
    from resources.lib.category_mapper import get_category_icon

    site.add_dir(
        "English Movies",
        site.url + "/category.php?cat=aflammotrjma",
        "getMovies",
        get_category_icon("English Movies"),
    )
    site.add_dir(
        "Arabic Movies",
        site.url + "/category.php?cat=aflamarabic",
        "getMovies",
        get_category_icon("Arabic Movies"),
    )
    site.add_dir(
        "Turkish Movies",
        site.url + "/category.php?cat=aflamturky",
        "getMovies",
        get_category_icon("Turkish Movies"),
    )
    site.add_dir(
        "Indian Movies",
        site.url + "/category.php?cat=aflamhindi",
        "getMovies",
        get_category_icon("Indian Movies"),
    )
    site.add_dir(
        "Asian Movies",
        site.url + "/category.php?cat=aflamasia",
        "getMovies",
        get_category_icon("Asian Movies"),
    )
    site.add_dir(
        "Anime Movies",
        site.url + "/category.php?cat=aflamanmi",
        "getMovies",
        get_category_icon("Anime Movies"),
    )

    site.add_dir(
        "Arabic TV Shows",
        site.url + "/category.php?cat=moslslatarabic",
        "getTVShows",
        get_category_icon("Arabic TV Shows"),
    )
    site.add_dir(
        "Turkish TV Shows",
        site.url + "/category.php?cat=moslsltturkymotrjam",
        "getTVShows",
        get_category_icon("Turkish TV Shows"),
    )
    site.add_dir(
        "Turkish TV Shows (Dubbed)",
        site.url + "/category.php?cat=moslsltturkymodblj",
        "getTVShows",
        get_category_icon("Turkish TV Shows (Dubbed)"),
    )
    site.add_dir(
        "Indian TV Shows",
        site.url + "/category.php?cat=hindimotrjam",
        "getTVShows",
        get_category_icon("Indian TV Shows"),
    )
    site.add_dir(
        "Korean TV Shows",
        site.url + "/category.php?cat=koreandrama",
        "getTVShows",
        get_category_icon("Korean TV Shows"),
    )
    site.add_dir(
        "Cartoon TV Shows",
        site.url + "/category.php?cat=animemotrjm",
        "getTVShows",
        get_category_icon("Cartoon TV Shows"),
    )

    site.add_dir(
        "TV Programs",
        site.url + "/category.php?cat=showtv",
        "getTVShows",
        get_category_icon("TV Programs"),
    )

    site.add_dir("Search", "", "search", get_category_icon("Search"))

    utils.eod()


@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if search_text:
        search_url = site.url + "/search.php?keywords=" + search_text
        getMovies(search_url)


@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f"{site.title}: Getting movies from: {url}")

    html = utils.getHtml(
        url, headers={"User-Agent": utils.USER_AGENT}, site_name=site.name
    )

    if not html:
        utils.kodilog(f"{site.title}: No HTML received")
        utils.eod(content='movies')
        return

    pattern = r'<a href="(https?://vio-la\.com/watch\.php\?vid=[^"]+)" title="([^"]+)"[^>]*>.*?data-echo="([^"]+)"'
    matches = re.findall(pattern, html, re.DOTALL)

    seen = set()
    unique_matches = []
    for m in matches:
        if m[0] not in seen:
            seen.add(m[0])
            unique_matches.append(m)

    utils.kodilog(f"{site.title}: Found {len(unique_matches)} items")

    if unique_matches:
        for movie_url, title, image in unique_matches:
            title = title.strip()

            title = re.sub(
                r"فيلم|movie|مشاهدة|مترجم|مدبلج|اون لاين|HD", "", title
            ).strip()

            year = ""
            year_match = re.search(r"(\d{4})", title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, "").strip()

            if title:
                site.add_dir(title, movie_url, "getLinks", image, year=year)

    # Pagination - extract page number from URL and increment
    import urllib.parse

    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)

    # Get current page number (default to 1)
    current_page = int(params.get("page", ["1"])[0])

    # Check if there's a next page by looking for higher page numbers in HTML
    page_numbers = re.findall(r"page=(\d+)&order=DESC", html)
    if page_numbers:
        max_page = max(int(p) for p in page_numbers)
        if current_page < max_page:
            next_page = current_page + 1
            params["page"] = [str(next_page)]
            params["order"] = ["DESC"]

            new_query = urllib.parse.urlencode(params, doseq=True)
            next_url = parsed._replace(query=new_query).geturl()

            site.add_dir("Next Page", next_url, "getMovies", addon_image(site.img_next))

    utils.eod(content='movies')


@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    getMovies(url)


@site.register()
def getLinks(url, name=""):
    """Extract video links from page"""
    utils.kodilog(f"{site.title}: Getting links from: {url}")

    html = utils.getHtml(url, headers={"User-Agent": utils.USER_AGENT})

    if not html:
        utils.notify(site.title, "لم يتم تحميل الصفحة", icon=site.image)
        utils.eod(content='videos')
        return

    hoster_manager = get_hoster_manager()

    iframe_match = re.search(
        r'<iframe[^>]+src="(https?://vio-la\.com/embed\.php\?vid=[^"]+)"', html
    )

    links_found = False

    if iframe_match:
        embed_url = iframe_match.group(1)
        utils.kodilog(f"{site.title}: Found embed URL: {embed_url}")

        embed_html = utils.getHtml(embed_url, headers={"User-Agent": utils.USER_AGENT})

        if embed_html:
            utils.kodilog(
                f"{site.title}: Embed page fetched, length: {len(embed_html)}"
            )

            external_iframe = re.search(
                r'<iframe[^>]+src="(https?://[^"]+)"', embed_html
            )

            if external_iframe:
                video_url = external_iframe.group(1)
                utils.kodilog(f"{site.title}: Found external iframe: {video_url}")
                links_found = True

                # Determine resolver icon based on video URL domain
                resolver_icon = site.image
                if "vk.com" in video_url or "vkvideo.ru" in video_url:
                    resolver_icon = "sites/vk.png"
                elif "ok.ru" in video_url:
                    resolver_icon = "sites/okru.png"

                # Make sure icon path is correct
                resolver_icon = (
                    basics.addon_image(resolver_icon) if resolver_icon else site.image
                )

                label, should_skip = utils.format_resolver_link(
                    hoster_manager, video_url, site.title, name, quality="Server"
                )

                if label and not should_skip:
                    basics.addDownLink(
                        label, video_url, f"{site.name}.PlayVid", resolver_icon
                    )
                    utils.kodilog(f"{site.title}: Added link: {label[:50]}")
            else:
                utils.kodilog(f"{site.title}: No external iframe found in embed page")
        else:
            utils.kodilog(f"{site.title}: Failed to fetch embed page")
    else:
        utils.kodilog(f"{site.title}: No embed iframe found in watch page")

    if not links_found:
        utils.notify(site.title, "لم يتم العثور على روابط", icon=site.image)

    utils.eod(content='videos')


@site.register()
def PlayVid(url, name=""):
    """Resolve and play video"""
    utils.kodilog(f"{site.title}: Resolving URL: {url[:100]}")

    hoster_manager = get_hoster_manager()
    result = hoster_manager.resolve(url, referer=site.url)

    utils.kodilog(f"{site.title}: Resolve result: {result}")

    if result and result.get("url"):
        video_url = result["url"]
        utils.kodilog(f"{site.title}: Playing direct URL: {video_url[:100]}")

        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(video_url)
    else:
        utils.kodilog(f"{site.title}: Resolve failed, trying direct play")
        vp = utils.VideoPlayer(name, False)
        vp.play_from_direct_link(url)
