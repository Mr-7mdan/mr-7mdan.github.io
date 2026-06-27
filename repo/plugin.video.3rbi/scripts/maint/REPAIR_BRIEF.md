# Repair Agent Brief — fix ONE 3rbi site scraper end-to-end

You OWN exactly one module: `resources/lib/sites/<SITE>.py`. Edit only that file. You may also READ
`resources/lib/sites.json`, `resources/lib/utils.py`, `resources/lib/basics.py`, and a healthy
reference module `resources/lib/sites/cima4u.py`. Do NOT touch any other file.

Repo root: `/Users/mohammed/Documents/Arabi/plugin.video.3rbi`

**Environment:** curl/wget/inline HTTP are BLOCKED. Fetch live HTML ONLY via the context-mode sandbox.
Load it: `ToolSearch` → `select:mcp__plugin_context-mode_context-mode__ctx_execute`. Then run python
inside `ctx_execute(language:"python", timeout:60000)`. IMPORTANT: pass `timeout=12` to every `fetch()`
call (the sandbox kills calls >30s; the harness default 25s is too long). Probe harness:
```python
src=open('/Users/mohammed/Documents/Arabi/plugin.video.3rbi/scripts/maint/probe.py').read()
ns={}; exec(compile(src,'probe.py','exec'),ns); fetch=ns['fetch']
r=fetch('https://site/...', timeout=12)   # -> dict(final_url,status,html,length,cf_challenge,error)
import re; print(len(re.findall(PATTERN, r['html'], re.DOTALL)))
```
If an Arabic-slug URL times out, URL-encode the slug with `urllib.parse.quote` and retry once. If a page
still times out after 2 tries, note it and move on (do not block).

## Goal
Make every function's scrape work against the CURRENT live site:
`Main` category URLs, `getMovies`/`getTVShows`/`getSeries`, `getSeasons`, `getEpisodes`, `search`, `getLinks`.

## Procedure
1. Read the module fully. Note the live base URL from `sites.json` (already domain-refreshed) and how each
   function builds URLs + the regex it uses.
2. For each function: fetch the real live page it targets, score the module's CURRENT regex.
   - matches > 0 with clean data  → leave it.
   - matches == 0 on a page that clearly has content → inspect the live HTML block, derive the corrected
     regex (match the new class names/attrs/structure), and Edit the module. Keep capture-group ORDER and
     count identical to what the function unpacks (e.g. `for url,img,title in ...`). Re-fetch + re-score
     until matches > 0 and url/title look right (Arabic-aware, no HTML junk, no nav items).
3. `getLinks`: fetch the watch page (respect the module's watch param), score the server/embed regex,
   and collect 2–3 real embed URLs. Record the distinct embed HOSTS seen (domain of each) — these feed
   hoster testing.
4. Preserve the module's existing helpers, capture-group contract, and call shape. Reuse
   `utils.getHtml(..., site_name=site.name)`, `utils.format_resolver_link`, `basics.addDownLink`,
   `addon_image(site.img_next)`, `get_hoster_manager()`. Do not rename functions or change registration.
5. Run `python3 -m py_compile resources/lib/sites/<SITE>.py` (via Bash) — must pass.

## Return (concise, NOT the whole file)
A short markdown block:
- `SITE`: name
- `live_base`: the working base URL used
- per-function table: function | before_matches | after_matches | changed? | note
- `embed_hosts_seen`: [domains]
- `edits`: 1-line summary of each regex/URL you changed (old→new shape)
- `status`: fixed | partial | already-ok | dead(reason)
- `needs_kodi_check`: anything you couldn't confirm headless (playback, CF, login)
Keep it tight. The actual fix lives in the edited file; do not paste the file back.
