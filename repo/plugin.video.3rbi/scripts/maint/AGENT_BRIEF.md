# Diagnosis Agent Brief — 3rbi site scraper triage (DIAGNOSIS ONLY, NO EDITS)

You diagnose ONE site scraper module. You will be given `SITE`, `JSON_URL`, `LIVE_HINT`.

Repo root: `/Users/mohammed/Documents/Arabi/plugin.video.3rbi`
Module: `resources/lib/sites/<SITE>.py`

**Environment:** `curl`/`wget`/inline HTTP are BLOCKED. Fetch live HTML ONLY through the
context-mode sandbox. First load the tool:
`ToolSearch` → `select:mcp__plugin_context-mode_context-mode__ctx_execute`

A zero-Kodi-dep probe harness exists at `scripts/maint/probe.py`. Use it inside `ctx_execute(language:"python")`:
```python
src=open('/Users/mohammed/Documents/Arabi/plugin.video.3rbi/scripts/maint/probe.py').read()
ns={}; exec(compile(src,'probe.py','exec'),ns)
fetch=ns['fetch']; probe_site=ns['probe_site']; print_report=ns['print_report']
# fetch(url) -> dict(final_url,status,html,length,cf_challenge,redirected,error)
# probe_site(base, [(label, path_or_absurl, [regex,...]), ...]) -> per-regex match counts
```
Use the module's OWN regexes (copy the exact pattern strings out of the .py) when scoring, so a 0
means the real scraper is broken. Build category/search/episode/watch URLs the same way `Main()` and
the functions do (path suffixes appended to the live base). For Arabic search use query `مسلسل` or `فيلم`.

## Steps
1. Read the module. Extract: Main() listing URLs (path suffixes), the regexes in
   getMovies/getTVShows/getSeasons/getEpisodes/getLinks, the search URL/endpoint + whether it is
   regular (`?s=`/`/search/`) or AJAX POST (`utils.getHtml(..., data=...)` to a `.php`), the watch-page
   param in getLinks (`?wat=1`/`?watch=1`/none), and any HARDCODED absolute `https://` base literal (a bug).
2. Fetch `JSON_URL`; record the final/live URL and whether the domain changed.
3. Score live, using the module's real regexes:
   - one movies/listing category page
   - one series listing page (if the site has series)
   - search results for the Arabic query
   - follow into ONE real series → its episodes page (grab a real series URL from the listing first)
   - ONE watch/movie page with the watch param → count server/embed matches and collect 2–3 real embed URLs
   For any pattern that yields 0 on a page that clearly HAS content, inspect the live HTML block and note the
   CORRECT pattern shape (e.g. "class MovieBlock → postDiv", "data-image → background-image"). DO NOT edit.
4. List the distinct embed hosts seen (the domain of each server/embed URL).

## Output — return ONLY this compact JSON (no prose, no markdown fences):
{
 "site":"<SITE>",
 "json_url":"...","live_url":"...","domain_changed":true|false,
 "hardcoded_url": "<literal or null>",
 "search_type":"regular|ajax|none",
 "per_function":{
   "Main":{"urls":["..."],"ok":true|false},
   "getMovies":{"url":"...","matches":0,"ok":false,"note":"correct shape if broken"},
   "getTVShows":{"url":"...","matches":0,"ok":false,"note":""},
   "getSeasons":{"url":"...","matches":0,"ok":false,"note":""},
   "getEpisodes":{"url":"...","matches":0,"ok":false,"note":""},
   "search":{"url":"...","matches":0,"ok":false,"note":""},
   "getLinks":{"url":"...","matches":0,"ok":false,"note":"","embed_samples":["..."]}
 },
 "embed_hosts_seen":["host.com"],
 "severity":"ok|minor|major|dead",
 "root_cause":"one line"
}
Use `null` for functions the module does not have. If a page is CF-challenged (harness cf_challenge=true),
set that function's note to "cf" and ok=false. Keep every note terse.
