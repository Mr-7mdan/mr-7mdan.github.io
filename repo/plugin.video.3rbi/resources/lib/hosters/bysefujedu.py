# -*- coding: utf-8 -*-
"""
Bysefujedu Resolver  (the "Byse" video platform -- NOT a FileMoon clone)

Mechanism (reverse-engineered + verified live 2026-06):
  - Embed page /e/<code> is a Vite/React SPA shell ("Byse Frontend"); there is
    NO packed eval and NO m3u8 in the HTML, so the FileMoon resolver can't touch
    it. The player chunk (videoPagesBundle) fetches the file metadata from a JSON
    API and decrypts the stream list client-side.
  - GET /api/videos/<code>  ->  JSON with a "playback" object:
        {algorithm:"AES-256-GCM", iv:<b64url>, payload:<b64url>,
         key_parts:[<b64url>, ... ~30 fragments], version:"<1..20>"}
  - Key derivation (mirrors the bundle's vi()/Ki()/yo()/Mo()):
        vi()  = {n: [n, 31-n] for n in 1..20}
        for the given version v, pick key_parts[v-1] and key_parts[(31-v)-1],
        base64url-decode each fragment and concatenate -> 32-byte AES-256 key.
        (If version is out of 1..20 or indices out of range, fall back to using
        every key_part concatenated -- same as the JS.)
  - AES-256-GCM decrypt(iv, payload) of the payload yields JSON
        {sources:[{url:"https://.../master.m3u8?...", label, height, ...}], ...}
    The 12-byte IV is the 96-bit GCM case, so decryption is plain AES-CTR with
    J0 = IV||0x00000001 and the keystream starting at J0+1; we drop the trailing
    16-byte auth tag (no verification needed to recover the plaintext).
  - The HLS token is short-lived (~15 min) and IP-bound, so playback uses the
    same client/UA.

Implemented with only stdlib + the addon's bundled single-block AES
(resources/lib/jscrypto/pyaes) -- no pycryptodome / cryptography dependency.
"""

import re
import json
import base64
from array import array
from six.moves.urllib_parse import urlparse

from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.jscrypto import pyaes


def _b64url(s):
    """Decode a base64url (no-padding) string to bytes."""
    s = s.replace('-', '+').replace('_', '/')
    s += '=' * (-len(s) % 4)
    return base64.b64decode(s)


def _select_key_parts(version, parts):
    """Pick the key fragments for this payload version (mirrors bundle vi/Ki/yo)."""
    n = len(parts)
    vmap = {str(k): (k, 31 - k) for k in range(1, 21)}
    pair = vmap.get(str(version).strip())
    if not pair:
        return parts
    i, s = pair
    if i < 1 or s < 1 or i > n or s > n:
        return parts
    sel = [parts[x - 1] for x in (i, s) if 1 <= x <= n]
    sel = [p for p in sel if isinstance(p, str) and p]
    return sel or parts


def _aes_gcm_decrypt(key, iv, ct_with_tag):
    """AES-256-GCM decrypt for the 96-bit-IV case using single-block AES (CTR).

    Recovers the plaintext only -- the 16-byte auth tag is discarded, not
    verified (the addon trusts its own API response).
    """
    if len(iv) != 12:
        raise ValueError('Unexpected GCM IV length: %d' % len(iv))
    ct = ct_with_tag[:-16] if len(ct_with_tag) > 16 else b''
    aes = pyaes.AES(key)
    out = bytearray()
    ctr = int.from_bytes(iv + b'\x00\x00\x00\x02', 'big')  # J0 + 1
    for off in range(0, len(ct), 16):
        block = array('B', ctr.to_bytes(16, 'big'))
        aes.encrypt_block(block)  # mutates block in place -> keystream
        chunk = ct[off:off + 16]
        out += bytes(a ^ b for a, b in zip(chunk, bytes(block)))
        ctr = (ctr & ~0xffffffff) | ((ctr + 1) & 0xffffffff)  # GCM 32-bit inc
    return bytes(out)


class BysefujeduResolver(HosterResolver):
    """Resolver for bysefujedu.com (the Byse video platform)."""

    def __init__(self):
        self.name = 'Bysefujedu'
        self.domains = ['bysefujedu.com']

    def can_resolve(self, url):
        return any(domain in url.lower() for domain in self.domains)

    def _filecode(self, url):
        """Extract the file code from a /e/<code>, /d/<code> or /<code> URL."""
        path = urlparse(url).path.strip('/')
        parts = [p for p in path.split('/') if p]
        if parts and parts[0].lower() in ('e', 'd', 'f', 'v', 'embed'):
            parts = parts[1:]
        code = parts[0] if parts else ''
        return re.sub(r'\.[a-z0-9]+$', '', code, flags=re.IGNORECASE)

    def resolve(self, url, referer=None, max_depth=3):
        """Resolve a bysefujedu embed URL to a direct HLS stream URL.

        Returns (stream_url, quality, headers) or None.
        """
        try:
            utils.kodilog('Bysefujedu Resolver: Attempting {}'.format(url[:100]))

            if url.startswith('//'):
                url = 'https:' + url

            parsed = urlparse(url)
            origin = '{}://{}'.format(parsed.scheme or 'https', parsed.netloc)

            code = self._filecode(url)
            if not code:
                utils.kodilog('Bysefujedu Resolver: Could not extract file code')
                return None

            api_url = '{}/api/videos/{}'.format(origin, code)
            api_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': '{}/e/{}'.format(origin, code),
                'Accept': 'application/json, text/plain, */*',
                'X-Requested-With': 'XMLHttpRequest',
            }

            data = utils.getHtml(api_url, headers=api_headers)
            if not data or not isinstance(data, str):
                utils.kodilog('Bysefujedu Resolver: Empty API response')
                return None

            try:
                meta = json.loads(data)
            except ValueError:
                utils.kodilog('Bysefujedu Resolver: API response not JSON')
                return None

            playback = meta.get('playback') or {}
            iv_b64 = playback.get('iv')
            payload_b64 = playback.get('payload')
            key_parts = playback.get('key_parts')
            if not (iv_b64 and payload_b64 and isinstance(key_parts, list) and key_parts):
                utils.kodilog('Bysefujedu Resolver: No encrypted playback payload '
                              '(premium-only or geo-blocked?)')
                return None

            try:
                key = b''.join(_b64url(p) for p in
                               _select_key_parts(playback.get('version'), key_parts))
                clear = _aes_gcm_decrypt(key, _b64url(iv_b64), _b64url(payload_b64))
                decoded = json.loads(clear.decode('utf-8'))
            except Exception as e:
                utils.kodilog('Bysefujedu Resolver: Decrypt failed - {}'.format(str(e)))
                return None

            sources = decoded.get('sources') or []
            if not sources:
                utils.kodilog('Bysefujedu Resolver: No sources in decrypted payload')
                return None

            # Prefer the highest-resolution HLS source.
            def _height(s):
                try:
                    return int(s.get('height') or 0)
                except (TypeError, ValueError):
                    return 0

            best = sorted(sources, key=_height, reverse=True)[0]
            stream_url = best.get('url')
            if not stream_url:
                utils.kodilog('Bysefujedu Resolver: Source had no url')
                return None
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url

            height = _height(best)
            quality = best.get('label') or ('{}p'.format(height) if height else 'HD')

            utils.kodilog('Bysefujedu Resolver: Found stream: {}'.format(stream_url[:100]))

            # Token is IP/UA-bound; play with the same UA and embed origin.
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Origin': origin,
            }

            return (stream_url, quality, playback_headers)

        except Exception as e:
            utils.kodilog('Bysefujedu Resolver: Error - {}'.format(str(e)))
            return None
