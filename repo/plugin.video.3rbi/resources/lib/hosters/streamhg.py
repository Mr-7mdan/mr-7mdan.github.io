# -*- coding: utf-8 -*-
"""
StreamHG hoster resolver (StreamWish-family XFS).

Live mechanism (verified 2026-06):
  - The embed URL the site hands us is the *frontend* host, e.g.
        https://hgcloud.to/e/<ID>
    Fetched server-side it returns only a ~950-byte JS loader
    ("Page is loading, please wait...") whose obfuscated /main.js does a
    client-side location.replace() to the real *player* host (currently
    audinifer.com) keeping the same /e/<ID> path. There is NO server
    redirect and NO intermediate API call, so a JS-less client (Kodi)
    never reaches the player by following the frontend URL.
  - The player host (audinifer.com/e/<ID>) returns the classic
    StreamWish/jwplayer page: a packed eval(p,a,c,k,e,d) block whose
    unpacked body contains the master.m3u8 (served from a *.premilkyway.com
    style CDN). This is identical to streamwish.py's packed-jwplayer path.

So resolve() = streamwish's packed-unpack approach, plus one extra step:
when the fetched page is the loader, rewrite the host to the known player
domain(s) and refetch before unpacking.

PLAYER_DOMAINS rotates over time (DMCA churn). When playback starts failing
with "loader detected, no player", load a fresh embed in a browser, note the
domain hgcloud.to redirects to, and prepend it here.
"""

import re
from urllib.parse import urlparse

from resources.lib import utils
from resources.lib.packer import cPacker
from resources.lib.hoster_resolver import HosterResolver

# Real player hosts the frontend (hgcloud.to) JS-redirects to. Most-recent first.
PLAYER_DOMAINS = ['audinifer.com']

# Packed block extractor — uses [\s\S]*? (NOT the catastrophic-backtracking
# "(?:.|\s)+?" some older resolvers use) so a 15 KB player page unpacks fast.
_PACKED_RE = re.compile(
    r"(eval\(function\(p,a,c,k,e,d\)\{[\s\S]*?\}\([\s\S]*?\.split\([\s\S]*?\)\)\))"
)


class StreamHGResolver(HosterResolver):
    """Resolver for StreamHG (hgcloud.to) and its player domains."""

    def __init__(self):
        self.name = 'StreamHG'
        # Frontend + player hosts. can_resolve() does substring matching, so the
        # bare 'hgcloud'/'streamhg' tokens also catch mirror TLD changes.
        self.domains = ['hgcloud.to', 'hgcloud', 'streamhg', 'audinifer.com']

    def can_resolve(self, url):
        u = (url or '').lower()
        return any(d in u for d in self.domains)

    # -- helpers ----------------------------------------------------------
    def _extract_stream(self, html):
        """Return a direct m3u8/mp4 URL from a player page, or None."""
        if not html or not isinstance(html, str):
            return None

        # Pre-unpack direct hit (some player builds inline it).
        m = re.search(r'file:\s*["\'](https?://[^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html)
        if m:
            return m.group(1)

        packed = _PACKED_RE.search(html)
        if not packed:
            return None
        try:
            unpacked = cPacker().unpack(packed.group(1))
        except Exception as e:
            utils.kodilog('StreamHG Resolver: unpack failed - {}'.format(e))
            return None

        # jwplayer setup keeps the literal master.m3u8 in the unpacked body.
        m = re.search(r'(https?://[^"\'\s]+\.m3u8[^"\'\s]*)', unpacked)
        if m:
            return m.group(1)
        m = re.search(r'file:\s*["\'](https?://[^"\']+)["\']', unpacked)
        if m:
            return m.group(1)
        return None

    def _is_loader(self, html):
        return bool(html) and (
            'Page is loading' in html
            or 'main.js' in html
            or len(html) < 2000
        )

    # -- main -------------------------------------------------------------
    def resolve(self, url):
        try:
            utils.kodilog('StreamHG Resolver: Attempting {}'.format(url[:100]))
            ua = utils.USER_AGENT
            parsed = urlparse(url)
            origin = '{}://{}'.format(parsed.scheme or 'https', parsed.netloc)

            html = utils.getHtml(url, headers={'User-Agent': ua, 'Referer': origin + '/'})

            stream = self._extract_stream(html)
            player_origin = origin

            # Frontend loader page -> hop to the real player host(s).
            if not stream and self._is_loader(html):
                utils.kodilog('StreamHG Resolver: loader page, trying player domains')
                for dom in PLAYER_DOMAINS:
                    player_url = '{}://{}{}'.format(parsed.scheme or 'https', dom, parsed.path)
                    p_html = utils.getHtml(
                        player_url,
                        headers={'User-Agent': ua, 'Referer': origin + '/'},
                    )
                    stream = self._extract_stream(p_html)
                    if stream:
                        player_origin = '{}://{}'.format(parsed.scheme or 'https', dom)
                        utils.kodilog('StreamHG Resolver: resolved via {}'.format(dom))
                        break

            if not stream:
                utils.kodilog('StreamHG Resolver: No video source found')
                return None

            if stream.startswith('//'):
                stream = 'https:' + stream

            utils.kodilog('StreamHG Resolver: Found stream {}'.format(stream[:100]))
            headers = {
                'User-Agent': ua,
                'Referer': player_origin + '/',
                'Origin': player_origin,
            }
            return (stream, 'HD', headers)

        except Exception as e:
            utils.kodilog('StreamHG Resolver: Error - {}'.format(str(e)))
            return None
