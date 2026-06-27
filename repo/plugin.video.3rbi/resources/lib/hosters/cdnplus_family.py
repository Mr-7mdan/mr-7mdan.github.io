# -*- coding: utf-8 -*-
"""
Cdnplus / XFileSharing "embed gateway" family resolver.

Covers a set of clone hosts that all serve the SAME embed structure: the
``/e/<code>`` page is only a stub form (no player markup); the real stream is
returned by POSTing ``op=embed&file_code=<code>`` to ``/dl``. The /dl response
contains packed jwplayer JS with ``sources:[{file:"...m3u8"}]``.

Because the GET page carries no sources, generic.py (GET-only) cannot resolve
these hosts -- hence this dedicated POST-based resolver.

Verified headless (2026-06): cdnplus.cyou, anafast.org, vidoba.org,
vidspeed.cyou and 1vid.xyz all return the byte-identical 2549-byte /e/ stub and
accept the POST /dl op=embed flow.
"""

import re
from urllib.parse import urlparse

from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.packer import cPacker


class CdnplusFamilyResolver(HosterResolver):
    def __init__(self):
        self.name = "CdnplusFamily"
        # Clones sharing the XFS /dl op=embed structure
        self.domains = [
            'cdnplus.cyou',
            'anafast.org',
            'vidoba.org',
            'vidspeed.cyou',
            '1vid.xyz',
        ]

    def _extract_code(self, url):
        """Pull the file_code out of an embed URL (/e/<code>, /<code>, *.html)."""
        path = urlparse(url).path
        seg = path.rstrip('/').split('/')[-1]
        seg = seg.replace('.html', '')
        # old XFS style: embed-<code>
        if seg.startswith('embed-'):
            seg = seg[len('embed-'):]
        # some variants suffix the code with -<n>
        if seg and '-' in seg and not seg.startswith('e'):
            seg = seg.split('-')[-1]
        return seg

    def _find_source(self, html):
        """Find an m3u8/mp4 in (possibly packed) player html."""
        if not html or not isinstance(html, str):
            return None

        # Unpack p.a.c.k.e.r blob if present
        packed = re.search(r'(eval\(function\(p,a,c,k,e,d\).*?)</script>', html, re.DOTALL)
        if packed:
            try:
                html = cPacker().unpack(packed.group(1)) + '\n' + html
            except Exception as e:
                utils.kodilog('CdnplusFamily: unpack failed - {}'.format(str(e)))

        patterns = [
            r'sources:\s*\[\s*\{\s*file\s*:\s*"([^"]+)"',
            r'sources:\s*\[\s*\{\s*(?:file|src)\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']',
            r'file\s*:\s*"(https?://[^"]+\.(?:m3u8|mp4)[^"]*)"',
            r'(https?://[^\s"\'<>]+\.(?:m3u8|mp4)[^\s"\'<>]*)',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                return m.group(1).replace('\\/', '/')
        return None

    def resolve(self, url):
        try:
            utils.kodilog('CdnplusFamily: Resolving {}'.format(url[:100]))

            parsed = urlparse(url)
            origin = '{}://{}'.format(parsed.scheme, parsed.netloc)
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            }

            # 1) Try the embed page itself (covers inline-player variants)
            html = utils.getHtml(url, headers=headers)
            video_url = self._find_source(html)

            # 2) Fall back to the XFS POST /dl op=embed gateway
            if not video_url:
                code = self._extract_code(url)
                if code:
                    utils.kodilog('CdnplusFamily: POST /dl file_code={}'.format(code))
                    form = {
                        'op': 'embed',
                        'file_code': code,
                        'auto': '1',
                        'referer': '',
                    }
                    dl_html = utils.postHtml(origin + '/dl', form_data=form, headers=headers)
                    video_url = self._find_source(dl_html)

            if not video_url:
                utils.kodilog('CdnplusFamily: No video source found')
                return None

            quality = 'HD'
            if '1080' in video_url:
                quality = '1080p'
            elif '720' in video_url:
                quality = '720p'
            elif '480' in video_url:
                quality = '480p'

            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Origin': origin,
            }
            utils.kodilog('CdnplusFamily: Found {}'.format(video_url[:100]))
            return (video_url, quality, playback_headers)

        except Exception as e:
            utils.kodilog('CdnplusFamily: Error - {}'.format(str(e)))
            return None
