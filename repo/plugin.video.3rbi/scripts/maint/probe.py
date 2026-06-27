#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3rbi maintenance probe — standalone headless scraper diagnostic.

NOT imported by the addon. Has ZERO Kodi deps so it runs in any plain Python 3
(incl. the context-mode ctx_execute sandbox, where curl/wget are blocked).

It mirrors resources/lib/utils.getHtml closely enough for triage:
  - random Windows browser User-Agent + the addon's base_hdrs
  - gzip handling, redirect following (records the final URL = redirect detection)
  - TLS-permissive context (sites often have broken chains)
  - real Cloudflare *challenge* detection (not just "Server: cloudflare")

Usage A — quick reachability of a base URL:
    from probe import fetch
    r = fetch("https://c4u.top/")
    print(r["final_url"], r["status"], len(r["html"]), r["cf_challenge"])

Usage B — score a site's real regexes against its real pages:
    from probe import probe_site
    res = probe_site("https://c4u.top", [
        # (label, path_or_abs_url, [regex, regex, ...])  -> reports match count per regex
        ("movies",  "/category/افلام/",        [r'<li class="MovieBlock">.*?href="([^"]+)"']),
        ("search",  "/?s=مسلسل",                [r'<li class="MovieBlock">.*?href="([^"]+)"']),
        ("watch",   "/film/x/?wat=1",           [r'data-embed="([^"]+)"']),
    ])
    print_report(res)

In ctx_execute, either import by absolute path or exec the file:
    src = open("/Users/mohammed/Documents/Arabi/plugin.video.3rbi/scripts/maint/probe.py").read()
    ns = {}; exec(compile(src, "probe.py", "exec"), ns)
    fetch = ns["fetch"]; probe_site = ns["probe_site"]
"""

import re
import ssl
import gzip
import json
import random
import urllib.request
import urllib.error
from io import BytesIO
from urllib.parse import quote, urljoin

# --- User-Agent (same shape as resources/lib/random_ua.generate_ua) ---------
_WIN = ['Windows NT 10.0; Win64; x64', 'Windows NT 10.0; WOW64', 'Windows NT 10.0']
_CHROME = ['%s.0.0.0' % i for i in range(110, 124)]


def _ua():
    return ('Mozilla/5.0 (%s) AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/%s Safari/537.36' % (random.choice(_WIN), random.choice(_CHROME)))


BASE_HDRS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
    'Accept-Encoding': 'gzip',
    'Accept-Language': 'en-US,en;q=0.8',
    'Connection': 'keep-alive',
}

# Cloudflare interstitial / JS-challenge fingerprints (real challenge, not just CF-fronted)
_CF_SIGNS = (
    'Just a moment', 'cf-browser-verification', 'cf-challenge', '__cf_chl',
    '/cdn-cgi/challenge-platform/', 'Checking your browser', 'Enable JavaScript and cookies',
)

_CTX = ssl.create_default_context()
_CTX.check_hostname = False
_CTX.verify_mode = ssl.CERT_NONE


def fetch(url, referer='', headers=None, timeout=25, data=None):
    """Fetch a URL. Returns dict: final_url, status, html, length, cf_challenge, error, content_encoding."""
    out = {'url': url, 'final_url': url, 'status': None, 'html': '', 'length': 0,
           'cf_challenge': False, 'error': None, 'redirected': False}
    hdrs = dict(BASE_HDRS)
    hdrs['User-Agent'] = _ua()
    if headers:
        hdrs.update(headers)
    if referer:
        hdrs['Referer'] = referer
    q = quote(url, r':/%?+&=#@,;~()![]$\'*')
    body = None
    if data is not None:
        body = data.encode('utf-8') if isinstance(data, str) else data
    try:
        req = urllib.request.Request(q, data=body, headers=hdrs)
        resp = urllib.request.urlopen(req, timeout=timeout, context=_CTX)
        raw = resp.read()
        out['status'] = resp.status
        out['final_url'] = resp.geturl()
    except urllib.error.HTTPError as e:
        raw = e.read()
        out['status'] = e.code
        out['final_url'] = e.geturl() if hasattr(e, 'geturl') else url
        out['error'] = 'HTTP %s' % e.code
        resp = e
    except Exception as e:
        out['error'] = '%s: %s' % (type(e).__name__, e)
        return out
    enc = resp.headers.get('Content-Encoding', '')
    if 'gzip' in enc.lower():
        try:
            raw = gzip.GzipFile(fileobj=BytesIO(raw)).read()
        except Exception:
            pass
    html = raw.decode('utf-8', errors='ignore') if isinstance(raw, (bytes, bytearray)) else raw
    out['html'] = html
    out['length'] = len(html)
    out['redirected'] = (out['final_url'].rstrip('/') != url.rstrip('/'))
    head = html[:6000]
    out['cf_challenge'] = (out['status'] in (403, 429, 503) and any(s in html for s in _CF_SIGNS)) \
        or any(s in head for s in _CF_SIGNS)
    return out


def count(html, pattern, flags=re.DOTALL):
    try:
        return len(re.findall(pattern, html, flags))
    except re.error as e:
        return 'REGEX_ERR:%s' % e


def sample(html, pattern, n=2, flags=re.DOTALL):
    try:
        m = re.findall(pattern, html, flags)
        return m[:n]
    except re.error:
        return []


def probe_site(base, checks, referer=''):
    """
    base: site base URL.
    checks: list of (label, path_or_abs, [regexes]).
    Returns dict with per-check fetch info + per-regex match counts.
    """
    base = base.rstrip('/')
    results = {'base': base, 'checks': []}
    for label, path, regexes in checks:
        url = path if path.startswith('http') else urljoin(base + '/', path.lstrip('/'))
        r = fetch(url, referer=referer or base)
        rec = {
            'label': label, 'url': url, 'final_url': r['final_url'],
            'status': r['status'], 'length': r['length'],
            'redirected': r['redirected'], 'cf_challenge': r['cf_challenge'],
            'error': r['error'], 'matches': {},
        }
        for i, rx in enumerate(regexes):
            rec['matches']['re%d' % i] = count(r['html'], rx)
        results['checks'].append(rec)
    return results


def print_report(res):
    print('BASE:', res['base'])
    for c in res['checks']:
        flags = []
        if c['redirected']:
            flags.append('REDIR->%s' % c['final_url'])
        if c['cf_challenge']:
            flags.append('CF_CHALLENGE')
        if c['error']:
            flags.append('ERR:%s' % c['error'])
        mc = ' '.join('%s=%s' % (k, v) for k, v in c['matches'].items())
        print('  [%-10s] http=%s len=%-7s %s  %s' % (
            c['label'], c['status'], c['length'], mc, ' '.join(flags)))


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        r = fetch(sys.argv[1])
        print(json.dumps({k: v for k, v in r.items() if k != 'html'}, ensure_ascii=False, indent=2))
        print('html_len=%d  head=%r' % (r['length'], r['html'][:200]))
