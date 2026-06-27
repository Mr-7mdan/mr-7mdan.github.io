# -*- coding: utf-8 -*-
"""
FastVIP resolver (fastvip.space).

Host used by WeCima (wecima.gold). WeCima server <li data-watch="...">
entries point at akhbarworld.online?mycimafsd=<base64>; the base64 decodes
to a fastvip.space/e/<code> embed (the wecima.py getLinks function does this
decode before handing the URL to the hoster manager).

Live mechanism (verified 2026-06 against fastvip.space/e/<code>):
    embed page -> Dean-Edwards packed eval(p,a,c,k,e,d) script -> unpack ->
        var links={"hls2":"https://<cdn>.premilkyway.com/hls2/.../master.m3u8?t=...",
                   "hls4":"/stream/.../master.m3u8",
                   "hls3":"https://<cdn>.../hls3/.../master.txt"};
        jwplayer("vplayer").setup({sources:[{file:links.hls4||links.hls3||links.hls2,type:"hls"}]})
    The hls2 entry is a real absolute HLS master playlist (.m3u8) that returns
    #EXTM3U and plays with a Referer of https://fastvip.space/. We prefer that
    absolute .m3u8 over the relative hls4 path and the hls3 .txt variant so
    Kodi/InputStream Adaptive can attach headers by extension.

Note: an expired/deleted file serves a tiny page containing
"File is no longer available" with no packed script -> returns None.
"""

import re
from six.moves.urllib_parse import urlparse
from resources.lib import utils
from resources.lib.packer import cPacker
from resources.lib.hoster_resolver import HosterResolver


class FastVipResolver(HosterResolver):
    """Resolver for the fastvip.space packed-jwplayer embed host."""

    def __init__(self):
        self.name = 'FastVIP'
        self.domains = ['fastvip.space', 'fastvip.']

    def can_resolve(self, url):
        """Check if this resolver can handle the given URL."""
        return any(domain in url.lower() for domain in self.domains)

    def _origin(self, url):
        """Return scheme://host for use as Referer/Origin."""
        p = urlparse(url)
        return '{}://{}'.format(p.scheme or 'https', p.netloc)

    def _pick_stream(self, text):
        """Pick the best playable stream URL from (unpacked) player text."""
        # 1. Prefer a real absolute HLS master playlist (.m3u8) -- the hls2 entry.
        m3u8 = re.findall(r'["\'](https?://[^"\']+?\.m3u8[^"\']*)["\']', text)
        if m3u8:
            return m3u8[0]
        # 2. Otherwise a direct mp4.
        mp4 = re.findall(r'["\'](https?://[^"\']+?\.mp4[^"\']*)["\']', text)
        if mp4:
            return mp4[0]
        # 3. EarnVids-style `links={...}` object -- first absolute http value.
        lm = re.search(r'links\s*=\s*\{(.*?)\}', text, re.DOTALL)
        if lm:
            vals = re.findall(r'["\'](https?://[^"\']+)["\']', lm.group(1))
            if vals:
                return vals[0]
        # 4. jwplayer-style file: "http..." fallback.
        fm = re.search(r'file\s*:\s*["\'](https?://[^"\']+)["\']', text)
        if fm:
            return fm.group(1)
        return None

    def resolve(self, url, referer=None, max_depth=3):
        """
        Resolve a fastvip.space embed URL to a direct stream.

        Returns (stream_url, 'HD', headers) tuple or None.
        """
        try:
            utils.kodilog('FastVIP Resolver: Attempting {}'.format(url[:100]))
            origin = self._origin(url)

            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer or (origin + '/'),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            html = utils.getHtml(url, headers=headers)
            if not html or not isinstance(html, str):
                utils.kodilog('FastVIP Resolver: Invalid HTML response')
                return None

            utils.kodilog('FastVIP Resolver: Received {} bytes'.format(len(html)))

            if 'no longer available' in html.lower():
                utils.kodilog('FastVIP Resolver: File expired / deleted')
                return None

            stream_url = None

            # Primary: Dean-Edwards packed eval(p,a,c,k,e,d) jwplayer blob.
            idx = html.find('eval(function(p,a,c,k,e')
            if idx != -1:
                end = html.find('</script>', idx)
                packed = html[idx:end if end != -1 else len(html)].strip()
                try:
                    unpacked = cPacker().unpack(packed)
                    utils.kodilog('FastVIP Resolver: Unpacked {} bytes'.format(len(unpacked)))
                    stream_url = self._pick_stream(unpacked)
                except Exception as e:
                    utils.kodilog('FastVIP Resolver: Unpack failed - {}'.format(str(e)))

            # Fallback: some skins emit sources inline without packing.
            if not stream_url:
                stream_url = self._pick_stream(html)

            if not stream_url:
                utils.kodilog('FastVIP Resolver: No stream found')
                return None

            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url

            utils.kodilog('FastVIP Resolver: Found stream {}'.format(stream_url[:100]))

            quality = 'HD'
            if '1080' in stream_url:
                quality = '1080p'
            elif '720' in stream_url:
                quality = '720p'
            elif '480' in stream_url:
                quality = '480p'

            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Origin': origin,
            }

            return (stream_url, quality, playback_headers)

        except Exception as e:
            utils.kodilog('FastVIP Resolver: Error - {}'.format(str(e)))
            return None
