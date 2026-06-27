# -*- coding: utf-8 -*-
"""
Rpmvid / Rpmshare Resolver  (the "rpmvid" video platform)

Mechanism (reverse-engineered + verified live 2026-06):
  - Embed page is a Vite/React SPA shell served from https://<host>/ (e.g.
    7.rpmvid.site). The file code lives in the URL *fragment*:
        https://7.rpmvid.site/#<code>
    There is NO packed eval and NO m3u8 in the HTML, so packer.py / the generic
    resolver can't touch it. The bundle reads location.hash and fetches the
    stream metadata from a JSON API, decrypting it client-side.
  - GET /api/v1/video?id=<code>   ->  body is an AES-128-CBC ciphertext, hex
    encoded. (The /api/v1/info endpoint is metadata-only; /api/v1/video carries
    the stream.) The ONLY request requirement is a real browser User-Agent --
    a non-browser UA is rejected with HTTP 400 {"message":"Request is invalid"}.
  - Decryption mirrors the bundle's E()/S()/v():
        key = AES-128-CBC, derived from location.protocol ("https:") -> the
              constant b"kiemtienmua911ca"
        iv  = derived from location.protocol + location.hash[0] ('#') -> the
              constant b"1234567890oiuytr"
    Both are CONSTANT for every rpmvid host (they depend on the protocol and the
    leading '#' of the hash, never on the hostname or the code), so they are
    hardcoded here. The plaintext is PKCS#7-padded JSON.
  - The decrypted JSON exposes the HLS master playlist:
        {"source":"https://<ip>/v4/<token>/<ts>/8q/<code>/master.m3u8?v=...",
         "cf":"https://<cf-host>/v4/8q/<code>/cf-master.<ts>.txt", ...}
    "source" is the in-house CDN (a raw-IP host with a self-signed cert -> needs
    verifypeer=false); "cf" is the Cloudflare fallback. The token is short-lived
    (~minutes) and IP/UA-bound, so playback uses the same UA + the embed origin
    as Referer.

Implemented with only stdlib + the addon's bundled single-block AES
(resources/lib/jscrypto/pyaes) -- no pycryptodome / cryptography dependency.
"""

import re
import json
from array import array
from six.moves.urllib_parse import urlparse

from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.jscrypto import pyaes

# Constant AES-128-CBC parameters (see module docstring -- protocol/hash derived).
_KEY = b'kiemtienmua911ca'
_IV = b'1234567890oiuytr'


def _cbc_decrypt(key, iv, ciphertext):
    """AES-CBC decrypt + PKCS#7 unpad using the bundled single-block AES.

    Done block-by-block with AES.decrypt_block (which mutates in place) to avoid
    pyaes.CBCMode.decrypt(), whose array.tostring() is gone on Python 3.9+.
    """
    aes = pyaes.AES(key)
    out = bytearray()
    prev = array('B', iv)
    for off in range(0, len(ciphertext), 16):
        ctblock = ciphertext[off:off + 16]
        block = array('B', ctblock)
        aes.decrypt_block(block)
        for i in range(16):
            block[i] ^= prev[i]
        out += bytes(block)
        prev = array('B', ctblock)
    if out:
        pad = out[-1]
        if 1 <= pad <= 16:
            out = out[:-pad]
    return bytes(out)


class RpmvidResolver(HosterResolver):
    """Resolver for the rpmvid / rpmshare video platform (7.rpmvid.site et al.)."""

    def __init__(self):
        self.name = 'Rpmvid'
        # Verified live: rpmvid.site (7.rpmvid.site). 'rpmvid.' / 'rpmshare' cover
        # numbered subdomains and the rpmshare branding seen on source sites.
        self.domains = ['rpmvid.site', 'rpmvid.', 'rpmshare', '7.rpmvid']

    def can_resolve(self, url):
        return any(domain in url.lower() for domain in self.domains)

    def _filecode(self, url):
        """Extract the file code -- it normally lives in the URL fragment."""
        parsed = urlparse(url)
        code = (parsed.fragment or '').strip()
        if not code:
            # Fallbacks: ?id=<code> or a /<code> path segment.
            m = re.search(r'[?&]id=([^&]+)', url)
            if m:
                code = m.group(1)
            else:
                segs = [s for s in parsed.path.split('/') if s]
                code = segs[-1] if segs else ''
        code = code.split('&')[0].split('?')[0]
        return re.sub(r'\.[a-z0-9]+$', '', code, flags=re.IGNORECASE)

    def resolve(self, url, referer=None, max_depth=3):
        """Resolve an rpmvid embed URL to a direct HLS stream URL.

        Returns (stream_url, quality, headers) or None.
        """
        try:
            utils.kodilog('Rpmvid Resolver: Attempting {}'.format(url[:100]))

            if url.startswith('//'):
                url = 'https:' + url

            parsed = urlparse(url)
            origin = '{}://{}'.format(parsed.scheme or 'https', parsed.netloc)

            code = self._filecode(url)
            if not code:
                utils.kodilog('Rpmvid Resolver: Could not extract file code')
                return None

            api_url = '{}/api/v1/video?id={}&w=1920&h=1080&r='.format(origin, code)
            api_headers = {
                'User-Agent': utils.USER_AGENT,  # browser UA is mandatory
                'Referer': '{}/#{}'.format(origin, code),
                'Accept': 'application/json, text/plain, */*',
            }

            data = utils.getHtml(api_url, headers=api_headers)
            if not data or not isinstance(data, str):
                utils.kodilog('Rpmvid Resolver: Empty API response')
                return None

            data = data.strip()
            if not re.fullmatch(r'[0-9a-fA-F]+', data) or len(data) % 32 != 0:
                # An error body (e.g. {"message":"Request is invalid"}) or junk.
                utils.kodilog('Rpmvid Resolver: API did not return ciphertext: '
                              '{}'.format(data[:80]))
                return None

            try:
                ciphertext = bytes(int(data[i:i + 2], 16) for i in range(0, len(data), 2))
                clear = _cbc_decrypt(_KEY, _IV, ciphertext)
                decoded = json.loads(clear.decode('utf-8'))
            except Exception as e:
                utils.kodilog('Rpmvid Resolver: Decrypt failed - {}'.format(str(e)))
                return None

            stream_url = decoded.get('source') or decoded.get('cf')
            if not stream_url:
                utils.kodilog('Rpmvid Resolver: No source in decrypted payload')
                return None
            if stream_url.startswith('//'):
                stream_url = 'https:' + stream_url

            utils.kodilog('Rpmvid Resolver: Found stream: {}'.format(stream_url[:100]))

            # Token is IP/UA-bound; the in-house CDN is a raw-IP host with a
            # self-signed cert, so play with the same UA, embed origin Referer,
            # and TLS verification disabled.
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': origin + '/',
                'Origin': origin,
                'verifypeer': 'false',
            }

            return (stream_url, 'HD', playback_headers)

        except Exception as e:
            utils.kodilog('Rpmvid Resolver: Error - {}'.format(str(e)))
            return None
