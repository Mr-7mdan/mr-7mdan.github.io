---
name: 3rbi-site-creator
description: Create new streaming site modules for 3rbi Kodi addon with verified scrapers. Use when user asks to add a new site, implement site scraper, create site module, or migrate site from Matrix addon. Triggers on "add new site", "create site module", "implement [site name]", "migrate [site] from matrix".
---

# 3rbi Site Creator

Systematically create and verify new streaming site modules for the 3rbi Kodi addon.

## Core Principles

1. **Never Guess Patterns** - Always verify HTML structure with curl
2. **Test in Terminal First** - Validate regex with Python before implementing
3. **Reference Matrix Implementation** - Use as initial guide, but verify current structure
4. **Progressive Testing** - Test each function (categories → listings → episodes → links)
5. **Handle Site Variations** - Search results often have different HTML than category pages

## 0. Domain-Rot Check FIRST (highest-yield)

**Before anything else, verify the live base URL against `sites.json`.** Streaming
sites move domains constantly — a "broken" site is far more often a moved domain than
a broken scraper.

Real moves seen in a single maintenance sweep:
- akwam: `ak.sv` → `akwam.it`
- arabseed: `a.asd.homes` → `a.asd.ink`
- egydead: `w.egydead.live` → `tv9.egydead.live`
- viola: `vio-la.com` → `hd.vio-la.com`
- larozza: `larozza.xyz` → `laroza.casa` → `laroza.surf`
- egydrama: `v.egydrama.com` → `egydrama.com`

**Fix:** update the site's `url` in `sites.json` and move the old value into
`alt_urls`. At runtime, `getHtml` called with `site_name=site.name` auto-updates the
stored URL when it follows a redirect, so it chases moves on its own too.

**Volatile per-request subdomains:** some hosts rotate a subdomain on every request
(e.g. faselhd resolves to `web*****x.faselhdx.bid`). Keep the stable entry domain
(`faselhd.club`) as `url` — do NOT pin the volatile subdomain.

## Restricted-Environment Fetching (curl may be blocked)

In some environments `curl` / `wget` / inline HTTP are intercepted or blocked. Use
the headless probe harness at `scripts/maint/probe.py` (zero Kodi dependencies) run
inside a Python sandbox (e.g. context-mode `ctx_execute`). Canonical invocation:

```python
src = open('/Users/mohammed/Documents/Arabi/plugin.video.3rbi/scripts/maint/probe.py').read()
ns = {}
exec(compile(src, 'probe.py', 'exec'), ns)
fetch = ns['fetch']
r = fetch(url, timeout=12)   # -> final_url, status, html, length, cf_challenge, redirected
```

- **Always pass `timeout=12`** — sandboxes kill anything over ~30s.
- If a fetch times out on an Arabic slug, URL-encode it with `urllib.parse.quote`
  and retry.

## Cloudflare Reality (getHtml has NO JS solver)

`getHtml` (in `utils.py`) uses plain `urllib` + TLS-downgrade retries + an optional
Flaresolverr call (gated by the addon setting `fs_enable`). It has **no JS-challenge
solver of its own.**

- A real CF JS challenge — body contains `"Just a moment"`, `"__cf_chl"`, or
  `"challenge-platform"` — needs Flaresolverr running in Kodi.
- IP matters: datacenter IPs may pass where a home IP gets challenged, and
  vice-versa.
- **Headless "works" ≠ Kodi works.** A probe success from a sandbox does not prove
  the site loads inside Kodi. Always confirm CF-sensitive sites in Kodi.

## API Surface (real working contract)

Confirmed against `cima4u.py` / `egydead.py`. Match this exactly:

- **getLinks:**
  ```python
  label, should_skip = utils.format_resolver_link(
      hoster_manager, embed_url, site.title, name, quality=...)
  if not should_skip:
      basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)
  ```
- **PlayVid:**
  ```python
  result = get_hoster_manager().resolve(url, referer=site.url)
  # then play the resolved direct link:
  utils.VideoPlayer(name, False).play_from_direct_link(video_url)
  ```
- **sites.json** is a DICT keyed by sitename; each entry has `label` / `active` /
  `url` / `alt_urls`.
- **`sites/__init__.py`** auto-builds `__all__` from entries with `active: true` —
  never hand-edit `__all__`.

## Workflow

### Phase 1: Discovery & Analysis

**Step 1: Check Matrix Implementation**
```bash
# Find the old site module
ls plugin.video.matrix/resources/sites/*.py | grep -i [sitename]

# Read and analyze patterns
cat plugin.video.matrix/resources/sites/[site].py | grep -A 10 "def show"
```

**Analyze:**
- URL patterns for categories, search, pagination
- Regex patterns for movies, series, episodes
- Special handling (authentication, cloudflare, etc.)
- Data extraction patterns

**Step 2: Discover Category URLs from Homepage**

**CRITICAL: Never hardcode category URLs - extract them from the homepage!**

```bash
# Fetch homepage
curl -sL "https://site.example" -A "Mozilla/5.0" -o /tmp/site_home.html

# Extract category links
cat /tmp/site_home.html | python3 -c "
import re, sys
html = sys.stdin.read()

print('=== Movies Categories ===')
movies = re.findall(r'<a[^>]+href=\"([^\"]*category[^\"]+)\"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
for url, name in movies[:10]:
    name_clean = name.strip()
    print(f'{name_clean}: {url}')

print('\n=== Series Categories ===')
series = re.findall(r'<a[^>]+href=\"([^\"]*series-category[^\"]+)\"[^>]*>([^<]+)</a>', html, re.IGNORECASE)
for url, name in series[:10]:
    name_clean = name.strip()
    print(f'{name_clean}: {url}')
"
```

**Important Notes:**
- Sites may use **English slugs** even for Arabic categories (e.g., `/category/english-movies/` not `/category/افلام-اجنبي/`)
- Always verify category URLs work before implementing
- Use the discovered URLs in your Main() function

**Step 3: Determine TV Show Structure**

**CRITICAL: Sites have different TV show hierarchies!**

**Pattern A: TV Shows → Seasons → Episodes (Most Common)**
```bash
# Example: EgyDead
# TV Shows page lists all shows
curl -sL "https://site.example/series/" -o /tmp/tvshows.html

# Clicking a show goes to seasons page
curl -sL "https://site.example/season/show-name/" -o /tmp/seasons.html

# Check structure
cat /tmp/seasons.html | python3 -c "
import re, sys
html = sys.stdin.read()

# Count seasons vs episodes
seasons = len([u for u in re.findall(r'href=\"([^\"]+)\"', html) if '/season/' in u])
episodes = len([u for u in re.findall(r'href=\"([^\"]+)\"', html) if '/episode/' in u])

print(f'Seasons: {seasons}')
print(f'Episodes: {episodes}')

if seasons > 0 and episodes == 0:
    print('✓ Pattern A: TV Shows → getSeasons → getEpisodes')
elif episodes > 0:
    print('✓ Pattern B: Seasons listed directly as TV shows → getEpisodes')
"
```

**Pattern B: Skip TV Shows, List Seasons Directly**
```bash
# Some sites list seasons in the main series category
# Each "season" goes directly to episodes page
# Present these as "TV shows" that route to getEpisodes

# Check if series category lists seasons or shows
curl -sL "https://site.example/series/" | grep -i "season\|موسم" | head -5
```

**Implementation:**
- **Pattern A**: Use `getSeasons` function (TV show → seasons → episodes)
- **Pattern B**: Skip `getSeasons`, route directly to `getEpisodes`

**Step 4: Detect Search Type (Regular vs AJAX)**

**Regular Search (Query Parameter)**
```bash
# Test search URL pattern
curl -sL "https://site.example/?s=test" -o /tmp/search.html
# OR
curl -sL "https://site.example/search/test" -o /tmp/search.html
```

**AJAX Search (POST Endpoint)**
```bash
# Look for AJAX search in browser DevTools Network tab
# Common patterns:
# - /ajax/search.php
# - /wp-content/themes/[theme]/Ajax/live-search.php
# - /api/search

# Example: EgyDead AJAX search
curl -X POST "https://egydead.rip/wp-content/themes/egydeadc-taq/Ajax/live-search.php" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "User-Agent: Mozilla/5.0" \
  --data "search=test" \
  -o /tmp/ajax_search.html

# Check response structure
cat /tmp/ajax_search.html | python3 -c "
import re, sys
html = sys.stdin.read()

# AJAX often returns different HTML structure
pattern = r'<div class=\"liveItem\">.*?href=\"([^\"]+)\".*?<h3>([^<]+)</h3>'
matches = re.findall(pattern, html, re.DOTALL)

print(f'Found {len(matches)} AJAX results')
if matches:
    print('Uses AJAX search - different pattern needed')
"
```

**Step 5: Categorize Search Results**

**CRITICAL: Search results can be mixed (movies + TV shows + seasons)**

```bash
# Analyze search result URLs to determine routing
cat /tmp/search.html | python3 -c "
import re, sys
html = sys.stdin.read()

# Extract all result URLs
urls = re.findall(r'<a href=\"([^\"]+)\"', html)

# Categorize by URL pattern
movies = [u for u in urls if '/movie/' in u or (not '/season/' in u and not '/serie/' in u and not '/episode/' in u)]
seasons = [u for u in urls if '/season/' in u]
series = [u for u in urls if '/serie/' in u]
episodes = [u for u in urls if '/episode/' in u]

print(f'Movies: {len(movies)} → route to getLinks')
print(f'Seasons: {len(seasons)} → route to getSeasons or getEpisodes')
print(f'Series: {len(series)} → route to getSeasons')
print(f'Episodes: {len(episodes)} → route to getLinks (individual episodes)')

print('\nSample routing logic:')
print('if \"/season/\" in url or \"/serie/\" in url:')
print('    # Pattern A: → getSeasons → episodes')
print('    # Pattern B: → getEpisodes directly')
print('elif \"/episode/\" in url:')
print('    # Individual episode → getLinks')
print('else:')
print('    # Movie → getLinks')
"
```

**Example: EgyDead Search Routing**
```python
# AJAX search returns mixed results
if '/season/' in result_url or '/serie/' in result_url:
    # TV show/season - check site structure
    # Pattern A: site.add_dir(..., 'getSeasons', ...)
    # Pattern B: site.add_dir(..., 'getEpisodes', ...)
else:
    # Movie or individual episode
    site.add_dir(..., 'getLinks', ...)
```

**Step 6: Live Site Verification**
```bash
# Test discovered category URLs
curl -sL "DISCOVERED_CATEGORY_URL" -A "Mozilla/5.0" | grep -i "movieItem\|MovieBlock" | wc -l
```

**Document:**
- Base URL
- Actual category URLs from homepage (not guessed!)
- TV show structure (Pattern A or B)
- Search type (Regular or AJAX)
- Search result routing rules
- HTML structure changes from Matrix version
- Any anti-bot measures (User-Agent requirements, etc.)

### Phase 2: Pattern Testing (Critical Step)

**NEVER implement patterns without testing them first!**

#### Test Movies/Series Listing

```bash
# Fetch category page
curl -s "https://site.example/category/movies/" -o /tmp/site_movies.html

# Test pattern 1: Find movie blocks
cat /tmp/site_movies.html | python3 -c "
import re
import sys
html = sys.stdin.read()

# Try different patterns
patterns = [
    (r'<div class=\"movie-item\">.*?<a href=\"([^\"]+)\".*?src=\"([^\"]+)\".*?<h3>([^<]+)</h3>', 'div.movie-item'),
    (r'<li class=\"MovieBlock\">.*?href=\"([^\"]+)\".*?data-image=\"([^\"]+)\".*?<div class=\"Title\">([^<]+)</div>', 'li.MovieBlock'),
]

for pattern, desc in patterns:
    matches = re.findall(pattern, html, re.DOTALL)
    print(f'{desc}: Found {len(matches)} matches')
    if matches:
        for i, match in enumerate(matches[:2], 1):
            print(f'  {i}. URL: {match[0][:60]}')
            print(f'     Image: {match[1][:60]}')
            print(f'     Title: {match[2][:40]}')
        break
"
```

#### Test Title & Poster Parsing

```bash
# Verify extracted data quality
cat /tmp/site_movies.html | python3 -c "
import re
import sys
html = sys.stdin.read()

# Extract first item to check quality
pattern = r'<li class=\"MovieBlock\">.*?href=\"([^\"]+)\".*?data-image=\"([^\"]+)\".*?<div class=\"Title\">([^<]+)</div>'
matches = re.findall(pattern, html, re.DOTALL)

if matches:
    url, image, title = matches[0]
    print(f'=== First Item Quality Check ===')
    print(f'Title: {title.strip()}')
    print(f'Title length: {len(title.strip())} chars')
    print(f'Title has junk: {any(x in title.lower() for x in [\"مشاهدة\", \"تحميل\", \"اون لاين\"])}')
    print(f'Image URL: {image}')
    print(f'Image is data-image: {\"data-image\" in html[:html.find(image)+100]}')
    
    # Check for hi-res alternatives
    print(f'\n=== Hi-Res Image Opportunities ===')
    # Look for original/full size image patterns
    if '-150x' in image or '-300x' in image or 'thumb' in image.lower():
        print(f'FOUND: Thumbnail detected - check for full size')
        full_size = re.sub(r'-\d+x\d+', '', image)
        print(f'Try: {full_size}')
    
    # Check for srcset with higher resolutions
    srcset = re.search(r'srcset=\"([^\"]+)\"', html[:1000])
    if srcset:
        print(f'FOUND: srcset with multiple resolutions')
        print(f'  {srcset.group(1)[:100]}')
"
```

#### Test Pagination (All Page Types!)

**CRITICAL: Test pagination on ALL page types - movies, TV shows, AND episodes**

```bash
# Test Movies Pagination
echo "=== Movies Pagination ==="
cat /tmp/site_movies.html | python3 -c "
import re
import sys
html = sys.stdin.read()

patterns = [
    (r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', 'next page-numbers'),
    (r'<link rel=\"next\" href=\"([^\"]+)\"', 'link rel=next'),
    (r'<a[^>]+rel=\"next\"[^>]+href=\"([^\"]+)\"', 'a rel=next'),
]

for pattern, desc in patterns:
    match = re.search(pattern, html)
    if match:
        print(f'Found ({desc}): {match.group(1)}')
        break
else:
    print('No pagination found - OK if single page')
"

# Test TV Shows Pagination
echo -e "\n=== TV Shows Pagination ==="
curl -s "https://site.example/category/series/" -o /tmp/site_series.html
cat /tmp/site_series.html | python3 -c "
import re
import sys
html = sys.stdin.read()
match = re.search(r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', html)
if match:
    print(f'Series pagination: {match.group(1)}')
else:
    print('No series pagination')
"

# Test Episodes Pagination (often forgotten!)
echo -e "\n=== Episodes Pagination ==="
curl -s "https://site.example/series/long-show/" -o /tmp/site_eps.html
cat /tmp/site_eps.html | python3 -c "
import re
import sys
html = sys.stdin.read()
# Check if episodes span multiple pages
match = re.search(r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', html)
if match:
    print(f'Episodes pagination: {match.group(1)}')
    print('IMPORTANT: Implement pagination in getEpisodes()!')
else:
    print('All episodes on one page')
"
```

#### Test Search Results (Often Different!)

```bash
# Search results may use different HTML structure
curl -s "https://site.example/?s=test" -o /tmp/site_search.html

# Compare structure
echo "=== Search Structure ==="
cat /tmp/site_search.html | python3 -c "
import re
import sys
html = sys.stdin.read()
# Test if same pattern works
pattern = r'<li class=\"MovieBlock\">.*?href=\"([^\"]+)\"'
matches = re.findall(pattern, html, re.DOTALL)
print(f'Found {len(matches)} items')
if len(matches) == 0:
    print('DIFFERENT STRUCTURE - need alternative pattern')
    # Look for differences
    blocks = re.findall(r'<li class=\"MovieBlock\">(.*?)</li>', html, re.DOTALL)[:1]
    if blocks:
        print('Sample block:')
        print(blocks[0][:500])
"
```

#### Test Episode Listing

```bash
# Fetch series page
curl -s "https://site.example/series/show-name/" -o /tmp/site_episodes.html

cat /tmp/site_episodes.html | python3 -c "
import re
import sys
html = sys.stdin.read()

# Test episode pattern
pattern = r'<a href=\"([^\"]+)\"[^>]*>.*?(?:الحلقة|Episode|EP).*?(\d+)'
matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
print(f'Found {len(matches)} episodes')
for i, (url, ep_num) in enumerate(matches[:5], 1):
    print(f'{i}. Episode {ep_num}: {url[:60]}')
"
```

#### Test Video Links Extraction

```bash
# Fetch video page (use ?watch=1 or ?wat=1 if needed)
curl -s "https://site.example/movie/name/?wat=1" -o /tmp/site_watch.html

cat /tmp/site_watch.html | python3 -c "
import re
import sys
html = sys.stdin.read()

# Test server link patterns
patterns = [
    (r'<a[^>]+class=\"[^\"]*server[^\"]*\"[^>]+data-embed=\"([^\"]+)\"[^>]*>([^<]*)</a>', 'data-embed'),
    (r'<iframe[^>]+src=\"([^\"]+)\"', 'iframe src'),
    (r'data-url=\"([^\"]+)\"', 'data-url'),
]

for pattern, desc in patterns:
    matches = re.findall(pattern, html)
    if matches:
        print(f'{desc}: Found {len(matches)} servers')
        for i, match in enumerate(matches[:3], 1):
            if isinstance(match, tuple):
                print(f'  {i}. {match[1]}: {match[0][:60]}')
            else:
                print(f'  {i}. {match[:60]}')
        break
"
```

### Phase 3: Implementation

**Step 1: Create Site Module File**

File: `resources/lib/sites/[sitename].py`

```python
# -*- coding: utf-8 -*-
"""
[SiteName] Site Module
[URL]
"""

import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

site = SiteBase('[sitename]', '[SiteTitle]', url=None, image='sites/[sitename].png')

@site.register(default_mode=True)
def Main():
    """Main menu"""
    # Movies
    site.add_dir('أفلام', site.url + '/category/movies/', 'getMovies', site.image)
    
    # TV Shows
    site.add_dir('مسلسلات', site.url + '/category/series/', 'getTVShows', site.image)
    
    # Search
    site.add_dir('بحث', '', 'search', site.image)
    
    utils.eod()

@site.register()
def search():
    """Search for content"""
    search_text = utils.get_search_input()
    if search_text:
        search_url = site.url + '/?s=' + search_text
        # Search returns mixed results (movies + series), getMovies handles routing
        getMovies(search_url)

@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    # Pass site_name for automatic redirect detection
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.kodilog(f'{site.title}: No HTML received')
        utils.eod()
        return
    
    # Pattern from terminal testing
    pattern1 = r'TESTED_PATTERN_HERE'
    matches = re.findall(pattern1, html, re.DOTALL)
    
    # Alternative pattern for search results if needed
    if not matches and '?s=' in url:
        pattern2 = r'ALTERNATIVE_PATTERN_HERE'
        matches = re.findall(pattern2, html, re.DOTALL)
    
    utils.kodilog(f'{site.title}: Found {len(matches)} movies')
    
    if matches:
        for movie_url, image, title in matches:
            # Clean title
            title = title.strip()
            title = re.sub(r'مشاهدة|فيلم|مترجم', '', title).strip()
            
            # Extract year if present
            year = ''
            year_match = re.search(r'(\d{4})', title)
            if year_match:
                year = year_match.group(1)
                title = title.replace(year, '').strip()
            
            if title:
                # CRITICAL: Route series URLs to getEpisodes, movie URLs to getLinks
                # Search returns mixed content types - detect from URL
                if '/season/' in movie_url or '/series/' in movie_url:
                    # This is a TV show - show episode list
                    site.add_dir(title, movie_url, 'getEpisodes', image, 
                               year=year, media_type='tvshow')
                else:
                    # This is a movie - show video links
                    site.add_dir(title, movie_url, 'getLinks', image, 
                               year=year, media_type='movie')
    
    # Pagination - IMPORTANT: strip trailing slash to avoid malformed URLs
    next_match = re.search(r'PAGINATION_PATTERN_HERE', html)
    if next_match:
        next_url = next_match.group(1).rstrip('/')
        site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
    
    utils.eod()

@site.register()
def getTVShows(url):
    """Get TV shows listing"""
    # Similar to getMovies but for series
    pass

@site.register()
def getEpisodes(url, name=''):
    """Get episodes for a series"""
    utils.kodilog(f'{site.title}: Getting episodes from: {url}')
    
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
    
    if not html:
        utils.eod()
        return
    
    # Pattern from terminal testing
    episode_pattern = r'EPISODE_PATTERN_HERE'
    episodes = re.findall(episode_pattern, html, re.DOTALL)
    
    for ep_url, ep_num in episodes:
        ep_title = f'{name} - الحلقة {ep_num}'
        site.add_dir(ep_title, ep_url, 'getLinks', site.image, 
                   episode=ep_num, media_type='episode')
    
    utils.eod()

@site.register()
def getLinks(url, name=''):
    """Extract video links from page"""
    utils.kodilog(f'{site.title}: Getting links from: {url}')
    
    # Append watch parameter if needed
    watch_url = url + '?wat=1' if '?wat=' not in url else url
    
    html = utils.getHtml(watch_url, headers={'User-Agent': utils.USER_AGENT})
    
    if not html:
        utils.notify(site.title, 'لم يتم تحميل الصفحة', icon=site.image)
        utils.eod()
        return
    
    hoster_manager = get_hoster_manager()
    
    # Pattern from terminal testing
    server_pattern = r'SERVER_PATTERN_HERE'
    servers = re.findall(server_pattern, html)
    
    utils.kodilog(f'{site.title}: Found {len(servers)} servers')
    
    for embed_url, server_name in servers:
        embed_url = embed_url.strip()
        server_name = server_name.strip() or 'Server'
        
        # Format link with resolver icons
        label, should_skip = utils.format_resolver_link(
            hoster_manager,
            embed_url,
            site.title,
            name,
            quality=server_name
        )
        
        if not should_skip:
            basics.addDownLink(label, embed_url, f'{site.name}.PlayVid', site.image)
    
    if not servers:
        utils.notify(site.title, 'لم يتم العثور على روابط', icon=site.image)
    
    utils.eod()

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
```

**Step 2: Activation is automatic (do NOT edit `__init__.py`)**

`resources/lib/sites/__init__.py` builds `__all__` dynamically from `sites.json` —
every site with `"active": true` is imported automatically. There is no manual
`__all__` list to maintain. To enable the site, set `active: true` in `sites.json`
(Phase 4, Step 2). To disable it, set `active: false` — no code change.

**Step 3: Add Site Icon**

- Download logo/icon for the site
- Save as `resources/images/sites/[sitename].png`
- Recommended size: 256x256 or 512x512

**Step 4: Add to sites.json**

`sites.json` is an **object keyed by site name** (NOT an array). Each entry uses
`label` / `active` / `url` (optional `alt_urls`). Add your site under the `sites` key:

```json
{
  "sites": {
    "[sitename]": {
      "label": "[SiteTitle]",
      "active": true,
      "url": "https://site.url"
    }
  }
}
```

### Phase 4: Testing & Verification

**Step 1: Compile**
```bash
cd /Users/mohammed/Documents/Arabi/plugin.video.3rbi
python3 -m py_compile resources/lib/sites/[sitename].py
```

**Step 2: Register in sites.json**
```bash
# Add site to sites.json
python3 << 'EOF'
import json

sites_json = 'resources/lib/sites.json'
with open(sites_json, 'r') as f:
    config = json.load(f)

# Add new site (note: Python True, not JSON true)
config['sites']['[sitename]'] = {
    "label": "[SiteTitle]",
    "active": True,
    "url": "[https://base-url]"
}

with open(sites_json, 'w') as f:
    json.dump(config, f, indent=4, ensure_ascii=False)

print('✓ Added [sitename] to sites.json')
EOF
```

**Step 3: Copy to Kodi**
```bash
cp resources/lib/sites/[sitename].py "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/lib/sites/"
cp resources/lib/sites.json "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/lib/"
cp resources/images/sites/[sitename].png "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/images/sites/"
```

**Step 4: Test in Kodi**
1. Restart Kodi
2. Open 3rbi addon
3. Test site menu appears
4. Test categories load
5. Test movie/series listings
6. Test search
7. Test pagination
8. Test episodes (for series)
9. Test video links extraction
10. Test video playback

**Step 4: Check Logs**
```bash
tail -f ~/Library/Logs/kodi.log | grep "@@@@3rbi:"
```

Look for:
- Pattern match counts
- URL formations
- Error messages

### Phase 5: Common Issues & Fixes

#### Issue: Empty Listings
**Cause:** Pattern doesn't match current HTML
**Fix:** Re-fetch page and test pattern in terminal

#### Issue: Search Returns Different Structure
**Cause:** Search results use different HTML than category pages
**Fix:** Add alternative pattern with `if not matches:` check

#### Issue: URL Contains Garbage
**Cause:** Regex too greedy, capturing beyond href value
**Fix:** Make pattern more explicit with anchors:
```python
# BAD: Too greedy
r'<a href="([^"]+)".*?background-image'

# GOOD: Explicit structure
r'<li class="Block">\s*<a href="([^"]+)"[^>]*>\s*<div'
```

#### Issue: Pagination Not Working
**Cause:** Using wrong icon path
**Fix:** Use `addon_image(site.img_next)` not `addon_image('next.png')`

#### Issue: Video Links Fail to Resolve
**Cause:** Wrong URL parameter (watch vs wat)
**Fix:** Check network tab or test with curl

#### Issue: TypeError in utils.notify
**Cause:** Positional arguments in wrong order
**Fix:** Use keyword argument:
```python
# WRONG
utils.notify('Site', 'Message', site.image)

# RIGHT
utils.notify('Site', 'Message', icon=site.image)
```

## Hoster Resolver Authoring & Testing

`HosterManager` auto-loads every `resources/lib/hosters/*.py`. A resolver class must
end in `Resolver` and subclass `HosterResolver`. **Just drop a file in — no
registration.** `generic.py` is forced last (it matches everything via a
packer-based GET + unpack).

**Contract:**
- `can_resolve(url) -> bool` — typically `any(domain in url for domain in self.domains)`
- `resolve(url, referer=None, max_depth=3)` returns `(video_url, quality)` OR
  `(video_url, quality, headers)` OR `None`.
- The manager chains resolvers up to `max_depth` and records success/failure in
  `hoster_tracker`.

**Tooling:**
- Reuse `resources/lib/packer.py` to unpack `eval(p,a,c,k,e,d)` jwplayer blobs, then
  extract `sources:[{file:"...m3u8/.mp4"}]`.

**Adding a new host — two paths:**
1. Add its domain to an existing same-structure resolver's `domains` list — but
   **only if the embed structure truly matches**. Verify live; do NOT assume clones.
2. Create a new resolver. Real example from this sweep: `cdnplus_family.py` — XFS
   hosts whose stream comes from a `POST /dl` with `op=embed&file_code=<code>`, not a
   plain GET.

**Testing limits:** you can validate the extraction regex against LIVE embed HTML
headless, but final playback only confirms in Kodi. Many hosts are CF-challenged or
JS-driven (React SPA, JS loader) and CANNOT be scraped with regex — flag those for
Kodi/browser, don't fake a resolver.

## Live Failure Patterns Seen (checklist)

Recurring real breakages from the maintenance sweep — check for each:

- [ ] **Hardcoded OLD domain baked into a getLinks/listing regex.** Make it
  domain-agnostic: `https?://[^"]+/watch\.php` instead of pinning the host.
- [ ] **Search markup differs from category markup.** Parse the search page itself;
  don't blindly delegate to the category listing parser.
- [ ] **Episode list not scoped to its container.** Scope to e.g. `EpsList` /
  `episodes__list`, or it captures the global "latest episodes" widget.
- [ ] **A bare `.*?` after an `href`** can swallow the next card's image when results
  are few. Anchor the pattern.
- [ ] **Category IDs silently bumped via a `<meta refresh>` stub** — follow the
  redirect.
- [ ] **Site went login/members-only** (e.g. asia2tv) → set `active: false`.
- [ ] **Missing import → NameError in search** (e.g. egydead `urllib_parse`).

## Quality Checklist

Before marking site complete:
- [ ] All patterns tested in terminal with real HTML
- [ ] Handles both category pages and search results
- [ ] Pagination works
- [ ] Search function works
- [ ] Episodes extracted correctly (for series)
- [ ] Video links extracted (5+ servers if available)
- [ ] Video playback works with at least one resolver
- [ ] No crashes on empty results
- [ ] Kodi logs show correct match counts
- [ ] Icon displays properly
- [ ] Title cleaning removes Arabic/English stopwords
- [ ] Year extraction works (if applicable)

## Examples from Existing Sites

### Cima4u Pattern (Reference)
```python
# Regular listings - data-image
pattern1 = r'<li class="MovieBlock">.*?<a href="([^"]+)".*?data-image="([^"]+)".*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'

# Search results - background-image  
pattern2 = r'<li class="MovieBlock">\s*<a href="([^"]+)"[^>]*>\s*<div class="Thumb">.*?background-image:url\(([^\)]+)\).*?<div class="BoxTitleInfo">.*?</div>\s*</div>\s*([^<]+?)\s*</div>'

# Server links - data-embed
server_pattern = r'<a[^>]+class="[^"]*sever_link[^"]*"[^>]+data-embed="([^"]+)"[^>]*>([^<]*)</a>'
```

### ArabSeed Pattern (Reference)
Check `plugin.video.matrix/resources/sites/arabseed.py` for alternative patterns.

## Workflow Summary

1. **Analyze Matrix** → Find old implementation
2. **Verify Live** → curl + grep structure
3. **Test Patterns** → Python terminal validation (CRITICAL)
4. **Implement** → Create site module with tested patterns
5. **Deploy** → Copy to Kodi
6. **Test** → Full workflow in Kodi
7. **Debug** → Check logs, re-test patterns if needed
8. **Iterate** → Fix issues, re-deploy

## Success Criteria

Site is production-ready when:
- ✅ Appears in addon menu
- ✅ Categories load with content
- ✅ Search returns results
- ✅ Pagination works
- ✅ Video links extract
- ✅ At least one video plays successfully
- ✅ No Python exceptions in Kodi log
