# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`plugin.video.3rbi` is a **Kodi (Matrix/Python 3) video addon** for Arabic streaming sites. It scrapes site HTML with regex, lists results in Kodi, and resolves the chosen video link to a playable stream via ResolveURL plus a bundled set of custom hoster resolvers. There is no build step — Python source runs directly inside Kodi.

`AGENTS.md` (root) and `resources/lib/sites/AGENTS.md` are the authoritative, detailed playbooks for site-scraper development and the global-search contract. Read them before adding or editing a site module. This file is the architecture map.

## Commands

```bash
# Deploy to Kodi (macOS) — the addon must run from inside Kodi's addons dir
cp -r . "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/"

# Compile-check (the only "test" — there is no unit-test suite)
python3 -m py_compile resources/lib/**/*.py default.py

# Watch logs (all addon logging is tagged)
tail -f ~/Library/Logs/kodi.log | grep "@@@@3rbi:"

# Lint (ruff is used — see .ruff_cache)
ruff check resources/lib/

# Find things
rg -n "def getMovies" resources/lib/sites/        # a site function
rg -n "data-embed" resources/lib/sites/*.py       # a scrape pattern across sites
```

After deploying, **restart Kodi** to pick up new/changed site modules, then verify in logs that scrapers report non-zero match counts (`Found N items`), not `Found 0`.

## Architecture

**Entry point — `default.py`.** Kodi invokes it with a `?mode=...&url=...` query string. `process_queries()` parses the query and calls `url_dispatcher.dispatch(mode, queries)`. `INDEX()` builds the root menu (Sites, Browse by Category, Global Search, Live TV, Favorites, etc.). The wildcard `from resources.lib.sites import *` is what registers every active site at import time.

**Mode dispatch — `resources/lib/url_dispatcher.py`.** `URL_Dispatcher` is the routing core. A function decorated with `@register()` is keyed by `"<module_name>.<func_name>"`. `dispatch()` introspects the function's signature (`getargspec`) and maps query-string keys onto its positional args (required) and keyword args (optional), coercing `"true"/"false"/"none"` strings to real types. **Consequence: a function's parameter names ARE its URL contract** — renaming a param changes the link format. Class-level registries (`func_registry`, etc.) are shared across all dispatcher instances.

**Site modules — `resources/lib/site_base.py` + `resources/lib/sites/*.py`.** Each site is one file exposing a `SiteBase` instance and `@site.register()`-decorated functions (`Main`, `getMovies`, `getTVShows`, `getEpisodes`, `search`, `getLinks`…). `SiteBase` extends `URL_Dispatcher`, so site functions dispatch the same way. The function marked `@site.register(default_mode=True)` (usually `Main`) is the site's landing page. Instances are tracked in a `WeakSet`; `get_sites()` / `get_site_by_name()` enumerate them for the menu.

**Site config is data, not code — `resources/lib/sites.json`.** Each site has `{label, active, url, alt_urls?}`. Two things read it:
- `resources/lib/sites/__init__.py` builds `__all__` from sites where `active == true`, so **only active sites get imported** by the wildcard import.
- `SiteBase.__init__` calls `_load_url_from_config(name)` when constructed with `url=None`, so site modules never hardcode their domain. Passing `site_name=site.name` to `utils.getHtml(...)` enables automatic redirect detection: when a site 301s to a new domain, `SiteBase.update_site_url()` rewrites `sites.json` and updates live instances. **To change a domain or toggle a site, edit `sites.json` — not the `.py`.**

**Site management UI — `resources/lib/site_manager.py`.** Kodi-facing enable/disable/enable-all menu, plus self-update: `check_updates()` / `update_all_sites()` pull `sites.json` and site `.py` files from the GitHub repo (`GITHUB_BASE_URL`), preserving local `active` states. This is how end users receive new scrapers without reinstalling.

**Hoster resolution — `resources/lib/hoster_resolver.py` + `resources/lib/hosters/*.py`.** `HosterManager` **auto-discovers** every `.py` in `hosters/` (no registration needed — drop a file in to add a host), each defining a `HosterResolver` subclass with `can_resolve(url)` / `resolve(url)`. `generic.py` is forced to load **last** because it matches all URLs as a fallback. `resolve()` returns the direct stream URL (+ optional headers). Site `getLinks` functions call `get_hoster_manager()` to turn embed/server links into playable URLs. ResolveURL (bundled under `script.module.resolveurl`) handles common hosts; the `hosters/` modules cover site-specific ones.

**Cross-site features.** `global_search.py` queries many sites at once via a `SEARCH_CONFIG` table and an interceptor that drops navigation/non-Arabic junk — every site must satisfy the search contract documented in `resources/lib/sites/AGENTS.md`. `category_browser.py` + `category_mapper.py` (+ `CATEGORY_MAPPING.md`) provide cross-site genre browsing. `favorites.py` (large, SQLite-backed) handles favorites, custom lists, and bookmarks. `live_tv.py` handles IPTV. `utils.py` is the shared toolbelt (`getHtml`, `kodilog`, `notify`, `USER_AGENT`, caching, i18n). `basics.py` builds Kodi list items (`addDir`, `addDownLink`, `addon_image`).

## Conventions that bite if ignored

- **Test every regex in the terminal against real HTML before writing it into a module.** Search-result pages frequently use different markup than category pages — handle both with a fallback pattern. (Full workflow in `resources/lib/sites/AGENTS.md`.)
- **Always pass a User-Agent**: `utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT}, site_name=site.name)`. The `site_name` kwarg is what enables redirect auto-update.
- **`utils.notify(title, msg, icon=site.image)`** — `icon` must be keyword; positional raises `TypeError`.
- **Imports go at the top of the file**, never mid-file.
- **Pagination is needed on `getEpisodes` too**, not just movie/series lists — long-running shows break without it.
- Bundled third-party addons (`plugin.video.matrix`, `plugin.video.umbrella`, `script.module.resolveurl`) are **reference/dependency code** — `plugin.video.matrix` in particular is the source to consult when porting a site's scrape logic.

## Logging

Use `utils.kodilog(msg)` (tag `@@@@3rbi:`). Listing functions should log match counts (`f'{site.title}: Found {len(matches)} items'`) — a `Found 0` in the log is the primary signal that a scrape pattern broke (usually a site redesign or domain change).
