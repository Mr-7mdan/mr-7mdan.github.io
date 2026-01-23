# Site Modules

## Package Identity
Streaming site scraper modules for Arabic video sites. Each module implements category browsing, search, episode listing, and video link extraction using regex-based HTML parsing.

## Setup & Run

```bash
# Create new site module
touch resources/lib/sites/[sitename].py

# Test regex patterns BEFORE implementing
curl -s "https://site.com/movies/" -o /tmp/test.html
cat /tmp/test.html | python3 -c "
import re, sys
html = sys.stdin.read()
pattern = r'YOUR_PATTERN'
print(f'Matches: {len(re.findall(pattern, html, re.DOTALL))}')
"

# Compile site module
python3 -m py_compile resources/lib/sites/[sitename].py

# Deploy to Kodi
cp resources/lib/sites/[sitename].py "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/lib/sites/"

# Add to __init__.py
# Add '[sitename]' to __all__ list

# Test in Kodi (restart required)
tail -f ~/Library/Logs/kodi.log | grep "@@@@3rbi:"
```

## Patterns & Conventions

### File Organization
- One site = one Python file in `resources/lib/sites/`
- Name: `[sitename].py` (lowercase, no spaces)
- Icon: `resources/images/sites/[sitename].png`

### Site Module Structure
```python
# 1. Imports (always at top)
import re
from resources.lib import utils
from resources.lib import basics
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.hoster_resolver import get_hoster_manager

# 2. Site instance - URL loaded dynamically from sites.json
site = SiteBase('name', 'Title', url=None, image='sites/icon.png')

# 3. Main menu (with default_mode=True)
@site.register(default_mode=True)
def Main():
    """Main menu"""
    site.add_dir('أفلام', site.url + '/movies/', 'getMovies', site.image)
    site.add_dir('مسلسلات', site.url + '/series/', 'getTVShows', site.image)
    site.add_dir('بحث', '', 'search', site.image)
    utils.eod()

# 4. Functions (registered with @site.register())
@site.register()
def getMovies(url):
    """Get movies listing"""
    utils.kodilog(f'{site.title}: Getting movies from: {url}')
    
    # Pass site_name for automatic redirect detection
    html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
    
    if not html:
        utils.eod()
        return
    
    # Implementation
    pass
```

### Critical Patterns

**DO: Test patterns in terminal first**
```bash
curl -s "URL" | python3 -c "
import re, sys
html = sys.stdin.read()
pattern = r'<div class=\"movie\">.*?<a href=\"([^\"]+)\"'
matches = re.findall(pattern, html, re.DOTALL)
print(f'Found {len(matches)} movies')
for url in matches[:3]:
    print(url)
"
```

**DON'T: Guess patterns without testing**
```python
# BAD - Never do this
pattern = r'<div class="movie">'  # Did you test this?
```

**DO: Handle search results differently**
```python
# Regular category pages
pattern1 = r'data-image="([^"]+)"'
matches = re.findall(pattern1, html, re.DOTALL)

# Search results may use different structure
if not matches and '?s=' in url:
    pattern2 = r'background-image:url\(([^\)]+)\)'
    matches = re.findall(pattern2, html, re.DOTALL)
```

**DON'T: Assume same pattern works everywhere**
```python
# BAD - Search results often have different HTML
pattern = r'...'  # This only works on category pages!
matches = re.findall(pattern, html)
```

**DO: Use keyword argument for icon**
```python
# CORRECT
utils.notify('Site', 'Message', icon=site.image)
```

**DON'T: Use positional argument**
```python
# BAD - Causes TypeError
utils.notify('Site', 'Message', site.image)
```

**DO: Use site.img_next for pagination**
```python
# CORRECT
site.add_dir('Next Page', next_url, 'getMovies', addon_image(site.img_next))
```

**DON'T: Hardcode icon path**
```python
# BAD - Won't work
site.add_dir('Next Page', next_url, 'getMovies', addon_image('next.png'))
```

**DO: Be explicit with href extraction**
```python
# CORRECT - Anchored to structure
pattern = r'<li class="Block">\s*<a href="([^"]+)"[^>]*>\s*<div'
```

**DON'T: Use greedy patterns**
```python
# BAD - Captures garbage after href
pattern = r'<a href="([^"]+)".*?background-image'
# Result: URL contains '<div class=' etc.
```

## Dynamic URL Management

**NEW: Sites now load URLs dynamically from sites.json and auto-update on redirects!**

### How It Works

**1. Site Initialization:**
```python
# OLD - Hardcoded URL (don't use)
site = SiteBase('cima4u', 'Cima4u', 'https://cima4u.info', 'sites/cima4u.png')

# NEW - Dynamic URL from sites.json
site = SiteBase('cima4u', 'Cima4u', url=None, image='sites/cima4u.png')
```

**2. Redirect Detection:**
```python
# Pass site_name to enable automatic redirect detection
html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)
```

**3. Automatic Updates:**
When a site redirects to a new domain (e.g., cima4u.info → cima4u.net):
- System detects the redirect
- Updates sites.json automatically
- Shows notification to user
- All site instances update their URL

**4. Manual URL Updates:**
To change a site's URL, edit `sites.json`:
```json
{
    "sites": {
        "cima4u": {
            "label": "Cima4u",
            "active": true,
            "url": "https://new-domain.com"
        }
    }
}
```

### Benefits
- **No code changes** when sites change domains
- **Automatic redirect following** keeps sites working
- **Centralized configuration** in sites.json
- **User notifications** when URLs update

## Key Files

### Reference Implementations
- **Cima4u**: `cima4u.py` - Complete example with search, pagination, series
  - Handles data-image vs background-image for search
  - ?wat=1 for video links
  - data-embed for server extraction
- **ArabSeed**: `arabseed.py` - Simple, clean patterns
- **Aksv**: `aksv.py` - Complex with authentication

### Core Dependencies
- `site_base.py` - SiteBase class, @register decorator
- `utils.py` - getHtml(), kodilog(), notify(), USER_AGENT
- `basics.py` - addDir(), addDownLink(), addon_image()
- `hoster_resolver.py` - get_hoster_manager(), resolve()

## JIT Index Hints

```bash
# Find how a site implements something
rg -A 10 "def getMovies" resources/lib/sites/cima4u.py

# Find all sites with pagination
rg -n "page-numbers|rel=\"next\"" resources/lib/sites/*.py

# Find all data-embed patterns
rg -n "data-embed" resources/lib/sites/*.py

# Find search implementations
rg -A 5 "def search" resources/lib/sites/*.py

# Find video link extraction patterns
rg -A 20 "def getLinks" resources/lib/sites/*.py

# Compare implementations
diff resources/lib/sites/cima4u.py resources/lib/sites/arabseed.py
```

## Quality Verification Checklist

### Title & Poster Parsing

**Always verify extracted data quality:**

```bash
# Check first extracted item
cat /tmp/test.html | python3 -c "
import re, sys
html = sys.stdin.read()
pattern = r'<li class=\"MovieBlock\">.*?href=\"([^\"]+)\".*?data-image=\"([^\"]+)\".*?Title\">([^<]+)</div>'
matches = re.findall(pattern, html, re.DOTALL)

if matches:
    url, image, title = matches[0]
    print(f'Title: {title.strip()}')
    print(f'Has junk words: {any(x in title.lower() for x in [\"مشاهدة\", \"تحميل\"])}')
    print(f'Image: {image}')
    
    # Check for hi-res
    if '-150x' in image or '-300x' in image or 'thumb' in image.lower():
        print(f'THUMBNAIL DETECTED - Try full size:')
        print(f'  {re.sub(r\"-\\d+x\\d+\", \"\", image)}')
"
```

**Look for hi-res image opportunities:**
- Thumbnails with `-150x150`, `-300x300` patterns
- `srcset` attributes with multiple resolutions
- Original image URLs (remove size suffix)

### Pagination Coverage

**CRITICAL: Test pagination on ALL page types!**

```bash
# 1. Movies pagination
curl -s "site.com/movies/" | python3 -c "
import re, sys
match = re.search(r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', sys.stdin.read())
print(f'Movies: {\"YES\" if match else \"NO\"}')"

# 2. TV Shows pagination  
curl -s "site.com/series/" | python3 -c "
import re, sys
match = re.search(r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', sys.stdin.read())
print(f'Series: {\"YES\" if match else \"NO\"}')"

# 3. Episodes pagination (often forgotten!)
curl -s "site.com/series/long-show/" | python3 -c "
import re, sys
match = re.search(r'<a class=\"next page-numbers\" href=\"([^\"]+)\"', sys.stdin.read())
print(f'Episodes: {\"YES\" if match else \"NO\"}')
if match:
    print('⚠️  Implement pagination in getEpisodes()!')"
```

**Implementation:**
- getMovies() - Add pagination at end
- getTVShows() - Add pagination at end  
- getEpisodes() - **Don't forget this one!**

## Common Gotchas

1. **Search results HTML differs from category pages**
   - Always test search URL separately
   - Add fallback pattern with `if not matches:`

2. **URL parameters for video pages**
   - Some sites use `?watch=1`, others `?wat=1`
   - Check network tab or Matrix implementation

3. **Regex captures HTML garbage**
   - Make patterns more explicit
   - Anchor to structural elements: `\s*<div class="Thumb">`

4. **TypeError in utils.notify**
   - Use `icon=site.image` keyword argument
   - Not positional: ~~`utils.notify('a', 'b', site.image)`~~

5. **Pagination icon not found**
   - Use `addon_image(site.img_next)` 
   - Not `addon_image('next.png')`

6. **Pattern matches in terminal but not in code**
   - Check you copied pattern exactly (quotes, backslashes)
   - Verify using same `re.DOTALL` flag

7. **Episodes pagination missing**
   - Series with 100+ episodes need pagination
   - Test with long-running show
   - Add same pagination logic as getMovies/getTVShows

8. **Low-quality poster images**
   - Check for `-150x150` or `-300x300` in URL
   - Try removing size suffix for full resolution
   - Look for `srcset` attribute with higher resolutions

## Pre-PR Checks

```bash
# 1. Test pattern extraction in terminal (REQUIRED)
curl -s "https://site.com/movies/" | python3 -c "import re, sys; ..."

# 2. Compile Python
python3 -m py_compile resources/lib/sites/[sitename].py

# 3. Copy to Kodi
cp resources/lib/sites/[sitename].py "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/lib/sites/"

# 4. Add to __init__.py
echo "Verify '[sitename]' in __all__ list"

# 5. Test in Kodi
# - Restart Kodi
# - Check site appears in menu
# - Test categories, search, pagination, video playback
# - Monitor logs: tail -f ~/Library/Logs/kodi.log | grep "@@@@3rbi:"

# 6. Verify match counts in logs
# Should see: "Found X movies", "Found Y servers"
# Not: "Found 0 movies" (pattern failed)
```

## Complete Workflow Example

See Cima4u implementation (`cima4u.py`) as reference:

1. **Analyze**: Check `plugin.video.matrix/resources/sites/cimau.py`
2. **Fetch**: `curl -s "https://cima4u.info/category/افلام-اجنبي/" -o /tmp/test.html`
3. **Test pattern**: 
   ```bash
   cat /tmp/test.html | python3 -c "
   import re, sys
   html = sys.stdin.read()
   pattern = r'<li class=\"MovieBlock\">.*?href=\"([^\"]+)\"'
   print(f'Matches: {len(re.findall(pattern, html, re.DOTALL))}')
   "
   ```
4. **Test search separately**: 
   ```bash
   curl -s "https://cima4u.info/?s=test" -o /tmp/search.html
   # Test same pattern - often fails, need alternative!
   ```
5. **Implement**: Create `cima4u.py` with tested patterns
6. **Test watch page**: `curl -s "URL?wat=1" | python3 -c ...`
7. **Deploy**: Compile, copy to Kodi, add to `__init__.py`
8. **Verify**: Test all functions in Kodi, check logs

## Definition of Done

Site module is complete when:
- [ ] All regex patterns tested with curl + Python terminal
- [ ] Handles category pages (pattern1)
- [ ] Handles search results (pattern2 if different)
- [ ] **Title parsing verified** - No junk words (مشاهدة, تحميل, اون لاين)
- [ ] **Poster images checked** - Hi-res used if available (not thumbnails)
- [ ] **Movies pagination** tested and implemented
- [ ] **TV Shows pagination** tested and implemented
- [ ] **Episodes pagination** tested and implemented (don't forget!)
- [ ] Episode extraction tested (for series)
- [ ] Video server links extraction tested
- [ ] Compiles without errors
- [ ] Added to `__init__.py` __all__ list
- [ ] Copied to Kodi
- [ ] Kodi logs show correct match counts (not 0)
- [ ] At least one video plays successfully
- [ ] No Python exceptions in logs
