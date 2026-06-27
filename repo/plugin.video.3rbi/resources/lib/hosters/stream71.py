# -*- coding: utf-8 -*-
# Resolver for 71stream.one
#
# 71stream is an Inertia.js (Laravel) single-page embed player. The embed page
# does NOT use a packed eval(p,a,c,k,e,d) jwplayer blob. Instead the stream URL
# is delivered inside the Inertia `data-page="..."` attribute, which holds an
# HTML-entity-encoded JSON payload:
#
#   <div id="app" data-page="{ &quot;component&quot;:&quot;Video/Embed&quot;,
#        &quot;props&quot;:{ ..., &quot;url&quot;:&quot;https://cdn.../playlist.m3u8&quot;,
#        &quot;mime&quot;:&quot;application/vnd.apple.mpegurl&quot;, ... } }">
#
# props.url is the direct master .m3u8 (or an .mp4). The CDN observed is
# cdnvid.dramalvr.com and served the playlist without a Referer in headless
# tests, but we still send Referer + User-Agent for safety / geo-gated cases.

import re
import json

try:
    import html as _htmlmod  # Python 3
    _unescape = _htmlmod.unescape
except Exception:  # pragma: no cover
    try:
        from HTMLParser import HTMLParser
        _unescape = HTMLParser().unescape
    except Exception:
        _unescape = lambda s: s

from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver


class Stream71Resolver(HosterResolver):
    """Resolver for 71stream.one embeds (Inertia.js data-page JSON)."""

    def __init__(self):
        self.name = '71Stream'
        # 71stream.one is the only live domain observed; the others are listed
        # for forward-compatibility / mirror handling.
        self.domains = ['71stream.one', '71stream.', 'cdnvid.dramalvr.com']

    def can_resolve(self, url):
        return any(domain in url.lower() for domain in self.domains)

    def _origin(self, url):
        m = re.match(r'(https?://[^/]+)', url)
        return (m.group(1) + '/') if m else 'https://71stream.one/'

    def resolve(self, url):
        """
        Resolve a 71stream embed URL to a direct stream.

        Returns: (video_url, quality, headers) tuple, or None on failure.
        """
        try:
            utils.kodilog('71Stream Resolver: Attempting {}'.format(url[:100]))

            # Normalise to the /embed/ form if only a hashid/short path was given.
            if '/embed/' not in url and '71stream.' in url.lower():
                m = re.search(r'71stream\.[a-z]+/(?:e/|embed/)?([A-Za-z0-9]+)', url)
                if m:
                    origin = self._origin(url).rstrip('/')
                    url = '{}/embed/{}'.format(origin, m.group(1))
                    utils.kodilog('71Stream Resolver: Normalised to {}'.format(url))

            origin = self._origin(url)
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin,
            }

            html = utils.getHtml(url, headers=headers)
            if not html or not isinstance(html, str):
                utils.kodilog('71Stream Resolver: Invalid HTML response')
                return None

            utils.kodilog('71Stream Resolver: Received {} bytes'.format(len(html)))

            stream_url = None
            mime = ''

            # Primary path: parse the Inertia data-page JSON.
            page = re.search(r'data-page="([^"]+)"', html)
            if page:
                try:
                    data = json.loads(_unescape(page.group(1)))
                    props = data.get('props', {}) if isinstance(data, dict) else {}
                    stream_url = props.get('url') or props.get('file') or props.get('source')
                    mime = props.get('mime', '') or ''
                    if stream_url:
                        utils.kodilog('71Stream Resolver: Found url in data-page JSON')
                except Exception as e:
                    utils.kodilog('71Stream Resolver: data-page JSON parse failed - {}'.format(str(e)))

            # Fallback 1: HTML-entity-encoded "url":"...m3u8/mp4..." inside data-page.
            if not stream_url:
                m = re.search(r'&quot;(?:url|file|source)&quot;:&quot;(https?[^&]+?\.(?:m3u8|mp4)[^&"]*)&quot;', html)
                if m:
                    stream_url = _unescape(m.group(1)).replace('\\/', '/')
                    utils.kodilog('71Stream Resolver: Found url via encoded regex')

            # Fallback 2: plain JSON / JS "url":"...m3u8/mp4..." (in case markup changes).
            if not stream_url:
                m = re.search(r'["\'](?:url|file|source)["\']\s*:\s*["\'](https?[^"\']+?\.(?:m3u8|mp4)[^"\']*)["\']', html)
                if m:
                    stream_url = m.group(1).replace('\\/', '/')
                    utils.kodilog('71Stream Resolver: Found url via plain regex')

            # Fallback 3: any bare m3u8/mp4 URL in the page.
            if not stream_url:
                m = re.search(r'https?:\\?/\\?/[^"\'\s]+?\.(?:m3u8|mp4)[^"\'\s]*', html)
                if m:
                    stream_url = m.group(0).replace('\\/', '/')
                    utils.kodilog('71Stream Resolver: Found url via bare regex')

            if not stream_url:
                utils.kodilog('71Stream Resolver: No stream URL found')
                return None

            stream_url = _unescape(stream_url)
            utils.kodilog('71Stream Resolver: Resolved {}'.format(stream_url[:120]))

            quality = 'HD'
            if 'mpegurl' in mime.lower() or stream_url.endswith('.m3u8'):
                quality = 'HD'

            out_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin,
            }
            return (stream_url, quality, out_headers)

        except Exception as e:
            utils.kodilog('71Stream Resolver: Error - {}'.format(str(e)))
            return None
