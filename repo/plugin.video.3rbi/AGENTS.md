# 3rbi Kodi Addon

## Project Snapshot
Python-based Kodi video addon for Arabic streaming sites. Uses regex-based web scraping, dynamic site loading, and ResolveURL for video extraction. See sub-AGENTS.md in major directories for detailed patterns.

## Root Setup Commands
```bash
# Install to Kodi (macOS)
cp -r . "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/"

# Compile Python files
python3 -m py_compile resources/lib/**/*.py

# Watch Kodi logs
tail -f ~/Library/Logs/kodi.log | grep "@@@@3rbi:"
```

## Universal Conventions
- **Never guess patterns** - Always test regex with `curl + python3 -c` in terminal first
- **User-Agent required** - Most sites need `headers={'User-Agent': utils.USER_AGENT}`
- **Icon keyword argument** - `utils.notify(title, msg, icon=site.image)` not positional
- **Imports** - Always add imports at top of file, never mid-file
- **Site registration** - Use `@site.register()` decorator pattern (see existing sites)

## Security & Secrets
- Never commit API keys or tokens
- No PII collection - addon uses public streaming sites only
- Follow Kodi addon guidelines for data handling

## JIT Index

### Package Structure
- Site Modules: `resources/lib/sites/` → [see resources/lib/sites/AGENTS.md](resources/lib/sites/AGENTS.md)
- Core Library: `resources/lib/*.py` (utils, basics, site_base, etc.)
- Entry Point: `default.py` - URL dispatcher and main menu

### Quick Find Commands
```bash
# Find site module
ls resources/lib/sites/*.py

# Find function in site
rg -n "def getLinks" resources/lib/sites/

# Find pattern usage
rg -n "re.findall" resources/lib/sites/*.py

# Find how a site handles something
rg -A 5 "pagination" resources/lib/sites/cima4u.py
```

### Key Files
- `resources/lib/site_base.py` - SiteBase class, registration pattern
- `resources/lib/utils.py` - HTML fetching, notifications, Kodi helpers
- `resources/lib/basics.py` - addDir, addDownLink for Kodi list building
- `resources/lib/hoster_resolver.py` - Video URL resolution manager
- `resources/lib/sites.json` - Active sites configuration
- `default.py` - Main entry, URL routing

## Site Module Development

**Critical Rule**: Test patterns with curl + Python BEFORE implementing!

```bash
# Fetch page
curl -s "https://site.com/movies/" -o /tmp/test.html

# Test pattern
cat /tmp/test.html | python3 -c "
import re, sys
html = sys.stdin.read()
pattern = r'YOUR_PATTERN_HERE'
matches = re.findall(pattern, html, re.DOTALL)
print(f'Found {len(matches)} matches')
"
```

See `resources/lib/sites/AGENTS.md` for complete site development workflow.

## Definition of Done

Before deploying site module:
- [ ] All regex patterns tested in terminal with real HTML
- [ ] Handles both category pages AND search results (often different!)
- [ ] Python compiles without errors: `python3 -m py_compile file.py`
- [ ] Copied to Kodi addons directory
- [ ] Tested in Kodi: categories load, search works, videos play
- [ ] Kodi logs show correct match counts (no 0 matches errors)

# context-mode — MANDATORY routing rules

You have context-mode MCP tools available. These rules are NOT optional — they protect your context window from flooding. A single unrouted command can dump 56 KB into context and waste the entire session.

## BLOCKED commands — do NOT attempt these

### curl / wget — BLOCKED
Any shell command containing `curl` or `wget` will be intercepted and blocked by the context-mode plugin. Do NOT retry.
Instead use:
- `context-mode_ctx_fetch_and_index(url, source)` to fetch and index web pages
- `context-mode_ctx_execute(language: "javascript", code: "const r = await fetch(...)")` to run HTTP calls in sandbox

### Inline HTTP — BLOCKED
Any shell command containing `fetch('http`, `requests.get(`, `requests.post(`, `http.get(`, or `http.request(` will be intercepted and blocked. Do NOT retry with shell.
Instead use:
- `context-mode_ctx_execute(language, code)` to run HTTP calls in sandbox — only stdout enters context

### Direct web fetching — BLOCKED
Do NOT use any direct URL fetching tool. Use the sandbox equivalent.
Instead use:
- `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)` to query the indexed content

## REDIRECTED tools — use sandbox equivalents

### Shell (>20 lines output)
Shell is ONLY for: `git`, `mkdir`, `rm`, `mv`, `cd`, `ls`, `npm install`, `pip install`, and other short-output commands.
For everything else, use:
- `context-mode_ctx_batch_execute(commands, queries)` — run multiple commands + search in ONE call
- `context-mode_ctx_execute(language: "shell", code: "...")` — run in sandbox, only stdout enters context

### File reading (for analysis)
If you are reading a file to **edit** it → reading is correct (edit needs content in context).
If you are reading to **analyze, explore, or summarize** → use `context-mode_ctx_execute_file(path, language, code)` instead. Only your printed summary enters context.

### grep / search (large results)
Search results can flood context. Use `context-mode_ctx_execute(language: "shell", code: "grep ...")` to run searches in sandbox. Only your printed summary enters context.

## Tool selection hierarchy

1. **GATHER**: `context-mode_ctx_batch_execute(commands, queries)` — Primary tool. Runs all commands, auto-indexes output, returns search results. ONE call replaces 30+ individual calls.
2. **FOLLOW-UP**: `context-mode_ctx_search(queries: ["q1", "q2", ...])` — Query indexed content. Pass ALL questions as array in ONE call.
3. **PROCESSING**: `context-mode_ctx_execute(language, code)` | `context-mode_ctx_execute_file(path, language, code)` — Sandbox execution. Only stdout enters context.
4. **WEB**: `context-mode_ctx_fetch_and_index(url, source)` then `context-mode_ctx_search(queries)` — Fetch, chunk, index, query. Raw HTML never enters context.
5. **INDEX**: `context-mode_ctx_index(content, source)` — Store content in FTS5 knowledge base for later search.

## Output constraints

- Keep responses under 500 words.
- Write artifacts (code, configs, PRDs) to FILES — never return them as inline text. Return only: file path + 1-line description.
- When indexing content, use descriptive source labels so others can `search(source: "label")` later.

## ctx commands

| Command | Action |
|---------|--------|
| `ctx stats` | Call the `stats` MCP tool and display the full output verbatim |
| `ctx doctor` | Call the `doctor` MCP tool, run the returned shell command, display as checklist |
| `ctx upgrade` | Call the `upgrade` MCP tool, run the returned shell command, display as checklist |
