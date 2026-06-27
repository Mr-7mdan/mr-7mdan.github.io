# -*- coding: utf-8 -*-
"""
Vidara Resolver
Extracts video URLs from vidara.to embed pages.

Mechanism (verified live 2026-06):
  - Embed page /e/<filecode> loads jwplayer and POSTs to /api/stream with a
    JSON body {"filecode": <code>, "device": "web"}.
  - The API returns JSON: {"streaming_url": "https://.../master.m3u8?token=..",
    "title", "thumbnail", "subtitles", "default_sub_lang", "vast_ads"}.
  - The HLS token is IP-bound, so playback must use the same client/headers.
No packed eval, no JS challenge -- fully scrapable headless via a plain POST.
"""

import re
import json
from six.moves.urllib_parse import urlparse
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver


class VidaraResolver(HosterResolver):
    """Resolver for vidara.to (and vidara.* variants)"""

    def __init__(self):
        self.name = 'Vidara'
        self.domains = ['vidara.to', 'vidara.']

    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)

    def _filecode(self, url):
        """Extract the filecode from a vidara embed URL.

        Forms: https://vidara.to/e/<code>, /d/<code>, /f/<code>, /<code>.
        """
        path = urlparse(url).path.strip('/')
        if not path:
            return ''
        parts = [p for p in path.split('/') if p]
        # Drop a leading type segment (e, d, f, embed) if present.
        if parts and parts[0].lower() in ('e', 'd', 'f', 'embed', 'v'):
            parts = parts[1:]
        code = parts[0] if parts else ''
        # Strip any file extension (e.g. .html).
        code = re.sub(r'\.[a-z0-9]+$', '', code, flags=re.IGNORECASE)
        return code

    def resolve(self, url, referer=None, max_depth=3):
        """
        Resolve a vidara embed URL to a direct HLS stream URL.

        Args:
            url: Vidara embed URL (e.g. https://vidara.to/e/<filecode>)
            referer: optional referer (unused; vidara token is IP-bound)
            max_depth: unused (kept for interface compatibility)

        Returns:
            (stream_url, 'HD', headers) tuple or None if failed
        """
        try:
            utils.kodilog('Vidara Resolver: Attempting {}'.format(url[:100]))

            if url.startswith('//'):
                url = 'https:' + url

            parsed = urlparse(url)
            origin = '{}://{}'.format(parsed.scheme or 'https', parsed.netloc)

            filecode = self._filecode(url)
            if not filecode:
                utils.kodilog('Vidara Resolver: Could not extract filecode')
                return None

            api_url = '{}/api/stream'.format(origin)
            req_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Origin': origin,
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
            }

            data = utils.postHtml(
                api_url,
                json_data={'filecode': filecode, 'device': 'web'},
                headers=req_headers,
            )

            if not data or not isinstance(data, str):
                utils.kodilog('Vidara Resolver: Empty API response')
                return None

            try:
                payload = json.loads(data)
            except ValueError:
                utils.kodilog('Vidara Resolver: API response not JSON')
                return None

            stream_url = (payload.get('streaming_url')
                          or payload.get('file')
                          or payload.get('source'))

            if not stream_url:
                utils.kodilog('Vidara Resolver: No streaming_url in API response')
                return None

            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url

            utils.kodilog('Vidara Resolver: Found stream: {}'.format(stream_url[:100]))

            quality = 'HD'
            if '1080' in stream_url:
                quality = '1080p'
            elif '720' in stream_url:
                quality = '720p'
            elif '480' in stream_url:
                quality = '480p'

            # HLS token is IP/UA-bound; play with the same UA and embed referer.
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Origin': origin,
            }

            return (stream_url, quality, playback_headers)

        except Exception as e:
            utils.kodilog('Vidara Resolver: Error - {}'.format(str(e)))
            return None
