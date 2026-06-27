# -*- coding: utf-8 -*-
"""
EarnVids / VidHide family resolver.

Covers ourdrama.cc, morencius.com and the wider EarnVids/VidHide host family
(filelions, streamvid, vidhide* skins). All of them serve an /embed/<id> page
whose player config is a Dean-Edwards-packed `eval(p,a,c,k,e,d)` jwplayer blob.

Live mechanism (verified 2026-06 against ourdrama.cc):
    embed page -> packed eval(...) script -> unpack ->
        var links={"hls2":"https://<cdn>/hls2/.../master.m3u8?t=...","hls3":"...txt"};
        jwplayer("vplayer").setup({sources:[{file:links.hls4||links.hls3||links.hls2,...}]})
    The hls2 entry is a real HLS master playlist (.m3u8) and plays with a
    Referer of the embed host origin. We prefer the real .m3u8 over the .txt
    variant so Kodi/InputStream Adaptive can attach headers by extension.
"""

import re
from six.moves.urllib_parse import urlparse
from resources.lib import utils
from resources.lib.packer import cPacker


class EarnVidsResolver:
    """Resolver for the EarnVids / VidHide packed-jwplayer host family."""

    def __init__(self):
        self.name = 'EarnVids'
        # Substring matches. ourdrama.cc / morencius.com verified live; the rest
        # are EarnVids/VidHide-family skins that share the identical packed
        # jwplayer `var links={...}` structure.
        self.domains = [
            'ourdrama.cc',
            'morencius.com',
            'vidhide',      # vidhide.com / vidhidepro / vidhidevip / vidhidehub / vidhidefast
            'filelions',    # filelions.to / .com / .online (EarnVids family)
            'streamvid',    # streamvid.net (EarnVids family)
            'earnvid',      # earnvids / earnvideo
        ]

    def can_resolve(self, url):
        """Check if this resolver can handle the given URL."""
        return any(domain in url.lower() for domain in self.domains)

    def _origin(self, url):
        """Return scheme://host/ for use as Referer/Origin."""
        p = urlparse(url)
        return '{}://{}/'.format(p.scheme or 'https', p.netloc)

    def _pick_stream(self, text):
        """Pick the best playable stream URL from (unpacked) player text."""
        # 1. Prefer a real HLS master playlist (.m3u8) -- plays cleanly in Kodi.
        m3u8 = re.findall(r'["\'](https?://[^"\']+?\.m3u8[^"\']*)["\']', text)
        if m3u8:
            return m3u8[0]
        # 2. Otherwise a direct mp4.
        mp4 = re.findall(r'["\'](https?://[^"\']+?\.mp4[^"\']*)["\']', text)
        if mp4:
            return mp4[0]
        # 3. jwplayer-style file: "..." (non-m3u8/mp4 skins).
        fm = re.search(r'file\s*:\s*["\'](https?://[^"\']+)["\']', text)
        if fm:
            return fm.group(1)
        # 4. EarnVids `var links={...}` object -- first http value (e.g. .txt master).
        lm = re.search(r'links\s*=\s*\{(.*?)\}', text, re.DOTALL)
        if lm:
            vals = re.findall(r'["\'](https?://[^"\']+)["\']', lm.group(1))
            if vals:
                return vals[0]
        return None

    def resolve(self, url, referer=None, max_depth=3):
        """
        Resolve an EarnVids/VidHide embed URL to a direct stream.

        Returns (stream_url, 'HD', headers) tuple or None.
        """
        try:
            utils.kodilog('EarnVids Resolver: Attempting {}'.format(url[:100]))
            origin = self._origin(url)

            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer or origin,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            html = utils.getHtml(url, headers=headers)
            if not html or not isinstance(html, str):
                utils.kodilog('EarnVids Resolver: Invalid HTML response')
                return None

            utils.kodilog('EarnVids Resolver: Received {} bytes'.format(len(html)))

            stream_url = None

            # Primary: Dean-Edwards packed eval(p,a,c,k,e,d) jwplayer blob.
            idx = html.find('eval(function(p,a,c,k,e')
            if idx != -1:
                end = html.find('</script>', idx)
                packed = html[idx:end if end != -1 else len(html)].strip()
                try:
                    unpacked = cPacker().unpack(packed)
                    utils.kodilog('EarnVids Resolver: Unpacked {} bytes'.format(len(unpacked)))
                    stream_url = self._pick_stream(unpacked)
                except Exception as e:
                    utils.kodilog('EarnVids Resolver: Unpack failed - {}'.format(str(e)))

            # Fallback: unpacked player config absent -> try the raw page
            # (some VidHide skins emit sources inline without packing).
            if not stream_url:
                stream_url = self._pick_stream(html)

            if not stream_url:
                utils.kodilog('EarnVids Resolver: No stream found')
                return None

            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url

            utils.kodilog('EarnVids Resolver: Found stream {}'.format(stream_url[:100]))

            quality = 'HD'
            if '1080' in stream_url:
                quality = '1080p'
            elif '720' in stream_url:
                quality = '720p'
            elif '480' in stream_url:
                quality = '480p'

            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin,
                'Origin': origin.rstrip('/'),
            }

            return (stream_url, quality, playback_headers)

        except Exception as e:
            utils.kodilog('EarnVids Resolver: Error - {}'.format(str(e)))
            return None
