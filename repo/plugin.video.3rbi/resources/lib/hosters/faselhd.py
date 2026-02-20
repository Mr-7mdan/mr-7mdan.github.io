# -*- coding: utf-8 -*-
"""
FaselHD video_player Resolver
Resolves video_player?player_token= URLs to direct m3u8 streams
"""

import re
import os
import subprocess
import tempfile
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.packer import cPacker

_NODE_PATH = None

def _find_node():
    global _NODE_PATH
    if _NODE_PATH:
        return _NODE_PATH
    candidates = [
        '/usr/local/bin/node', '/usr/bin/node', '/opt/homebrew/bin/node',
        os.path.expanduser('~/.nvm/versions/node/v25.1.0/bin/node'),
    ]
    for p in candidates:
        if os.path.exists(p):
            _NODE_PATH = p
            return p
    try:
        r = subprocess.run(['which', 'node'], capture_output=True, text=True, timeout=3)
        if r.returncode == 0 and r.stdout.strip():
            _NODE_PATH = r.stdout.strip()
            return _NODE_PATH
    except Exception:
        pass
    return None


_NODE_STUB = r"""
const vm = require('vm');
const writes = [];
const addW = (s) => { if (s) writes.push(String(s)); };
const makeEl = () => {
  const el = {
    setAttribute: (k, v) => { el[k] = v; }, style: {}, className: '', value: '',
    src: '', type: '', href: '',
    appendChild: (c) => { if (c && c.src) addW(c.src); if (c && c.href) addW(c.href); },
    insertAdjacentHTML: (p, h) => addW(h),
    get innerHTML() { return ''; },
    set innerHTML(v) { addW(v); }
  };
  return el;
};
const ctx = vm.createContext({
  setTimeout: (fn) => { try { fn(); } catch (e) {} }, clearTimeout: () => {},
  setInterval: () => {}, clearInterval: () => {},
  location: { href: 'https://x.com/', hostname: 'x.com', protocol: 'https:', search: '', hash: '' },
  navigator: { userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', platform: 'Win32', language: 'en-US', languages: ['en-US'], cookieEnabled: true },
  screen: { width: 1920, height: 1080, colorDepth: 24 },
  history: { pushState: () => {} },
  document: {
    write: addW, writeln: addW,
    getElementById: () => makeEl(),
    createElement: () => makeEl(),
    createTextNode: (t) => ({ textContent: t }),
    querySelector: () => null, querySelectorAll: () => [],
    body: { appendChild: (el) => { if (el && el.src) addW(el.src); }, style: {}, set innerHTML(v) { addW(v); } },
    head: { appendChild: () => {} },
    cookie: '', readyState: 'complete',
    addEventListener: () => {}, removeEventListener: () => {},
    createDocumentFragment: () => ({ appendChild: () => {} })
  },
  jwplayer: (id) => ({
    setup: (cfg) => {
      if (!cfg) return;
      if (cfg.file) addW('JW:' + cfg.file);
      if (cfg.sources) cfg.sources.forEach(s => addW('JW:' + (s.file || s.src || '')));
      if (cfg.playlist) cfg.playlist.forEach(p => {
        if (p.file) addW('JW:' + p.file);
        if (p.sources) p.sources.forEach(s => addW('JW:' + (s.file || s.src || '')));
      });
    },
    on: function() { return this; }, play: function() { return this; }
  }),
  Hls: function() { return { loadSource: (u) => addW('HLS:' + u), attachMedia: () => {}, on: () => {} }; },
  XMLHttpRequest: function() { return { open: () => {}, send: () => {}, setRequestHeader: () => {}, onload: null, onerror: null, status: 200, responseText: '' }; },
  fetch: () => Promise.resolve({ text: () => Promise.resolve(''), json: () => Promise.resolve({}), ok: true }),
  Image: function() { return { set src(v) { addW('IMG:' + v); } }; },
  console: { log: () => {}, warn: () => {}, error: () => {}, info: () => {} },
  Math, JSON, Object, Array, String, Number, Boolean, RegExp, Date,
  parseInt, parseFloat, encodeURIComponent, decodeURIComponent, isNaN, isFinite,
  Promise, Symbol, Map, Set, WeakMap, WeakSet,
  atob: (s) => Buffer.from(s, 'base64').toString('binary'),
  btoa: (s) => Buffer.from(s, 'binary').toString('base64'),
});
ctx.window = { location: ctx.location, navigator: ctx.navigator, document: ctx.document };
ctx.document.defaultView = ctx.window;
try { vm.runInContext(SCRIPT_PLACEHOLDER, ctx, { timeout: 8000 }); } catch (e) {}
const out = writes.join('\n');
process.stdout.write(out);
"""


class FaselHDResolver(HosterResolver):
    def __init__(self):
        self.name = "FaselHD"
        self.domains = ['faselhdx.bid', 'faselhd.club', 'faselhd.pro', 'faselhd.info']

    def can_resolve(self, url):
        return 'video_player' in url and any(d in url for d in self.domains)

    def resolve(self, url):
        try:
            utils.kodilog('FaselHD Resolver: Fetching {}'.format(url[:80]))
            html = utils.getHtml(url, headers={
                'User-Agent': utils.USER_AGENT,
                'Referer': 'https://faselhd.club/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            })
            if not html:
                return None

            # Strategy 1: direct m3u8 URL visible in HTML
            m3u8s = re.findall(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>\\]*', html)
            if m3u8s:
                utils.kodilog('FaselHD Resolver: Direct m3u8 found')
                return (m3u8s[0], 'HD', {'User-Agent': utils.USER_AGENT, 'Referer': url})

            # Strategy 2: cPacker (Dean Edwards p,a,c,k,e,r)
            result = self._try_cpacker(html, url)
            if result:
                return result

            # Strategy 3: Matrix-style m3u8 master playlist (legacy)
            match = re.search(r',RESOLUTION=([^\s,]+).*?(https?[^\s"\']+\.m3u8)', html, re.DOTALL)
            if match:
                utils.kodilog('FaselHD Resolver: m3u8 from RESOLUTION tag')
                return (match.group(2), match.group(1), {'User-Agent': utils.USER_AGENT})

            # Strategy 4: Node.js JS evaluation (heavy obfuscation)
            m3u8_url = self._eval_with_nodejs(html, url)
            if m3u8_url:
                return (m3u8_url, 'HD', {'User-Agent': utils.USER_AGENT, 'Referer': url})

            utils.kodilog('FaselHD Resolver: All strategies failed')
            return None

        except Exception as e:
            utils.kodilog('FaselHD Resolver: Error - {}'.format(str(e)))
            return None

    def _try_cpacker(self, html, referer):
        """Strategy 2: Dean Edwards p,a,c,k,e,r unpacking via cPacker."""
        packed_match = re.search(r'(eval\(function\(p,a,c,k,e(?:.|\s)+?\))</script>', html, re.DOTALL)
        if not packed_match:
            return None
        try:
            utils.kodilog('FaselHD Resolver: cPacker found, unpacking...')
            packer = cPacker()
            unpacked = packer.unpack(packed_match.group(1))
            utils.kodilog('FaselHD Resolver: cPacker unpacked {} bytes'.format(len(unpacked)))

            headers = {'User-Agent': utils.USER_AGENT, 'Referer': referer}

            # m3u8 direct URL
            m3u8s = re.findall(r'https?://[^\s"\'<>\\]+\.m3u8[^\s"\'<>\\]*', unpacked)
            if m3u8s:
                utils.kodilog('FaselHD Resolver: cPacker -> m3u8 {}'.format(m3u8s[0][:80]))
                return (m3u8s[0], 'HD', headers)

            # file:"URL",label:"quality" (multiple sources)
            sources = re.findall(r'file:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']', unpacked)
            if sources:
                best_url, best_q = sources[-1]
                utils.kodilog('FaselHD Resolver: cPacker -> file/label {}'.format(best_url[:80]))
                return (best_url, best_q, headers)

            # file:"URL" (single)
            m = re.search(r'file:\s*["\']([^"\']+)["\']', unpacked)
            if m:
                utils.kodilog('FaselHD Resolver: cPacker -> file {}'.format(m.group(1)[:80]))
                return (m.group(1), 'HD', headers)

            # wurl="URL"
            m = re.search(r'wurl\s*=\s*["\']([^"\']+)["\']', unpacked)
            if m:
                video_url = m.group(1)
                if video_url.startswith('//'):
                    video_url = 'https:' + video_url
                utils.kodilog('FaselHD Resolver: cPacker -> wurl {}'.format(video_url[:80]))
                return (video_url, 'HD', headers)

            utils.kodilog('FaselHD Resolver: cPacker unpacked but no URL found')
        except Exception as e:
            utils.kodilog('FaselHD Resolver: cPacker error - {}'.format(str(e)))
        return None

    def _eval_with_nodejs(self, html, referer):
        node = _find_node()
        if not node:
            utils.kodilog('FaselHD Resolver: node not found')
            return None
        try:
            scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
            big = sorted([s for s in scripts if len(s) > 5000], key=len, reverse=True)
            if len(big) < 2:
                return None
            combined = big[0] + '\n' + big[1]

            js = _NODE_STUB.replace('SCRIPT_PLACEHOLDER', repr(combined))
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False, encoding='utf-8') as f:
                f.write(js)
                tmp = f.name

            result = subprocess.run([node, tmp], capture_output=True, text=True, timeout=12)
            try:
                os.unlink(tmp)
            except Exception:
                pass

            out = result.stdout
            utils.kodilog('FaselHD Resolver: Node output length {}'.format(len(out)))

            # Look for m3u8 URLs in output
            found = re.findall(r'https?://[^\s"\'<>\n]+\.m3u8[^\s"\'<>\n]*', out)
            if found:
                utils.kodilog('FaselHD Resolver: Node found {}'.format(found[0][:80]))
                return found[0]

            # Look for JW: or HLS: prefixed URLs
            for prefix in ['JW:', 'HLS:']:
                prefixed = re.findall(re.escape(prefix) + r'(https?://[^\s\n]+)', out)
                m3u8_prefixed = [u for u in prefixed if '.m3u8' in u or 'stream' in u]
                if m3u8_prefixed:
                    return m3u8_prefixed[0]

            # Look for scdns.io URLs
            scdns = re.findall(r'https?://[^\s"\'<>\n]*scdns[^\s"\'<>\n]*', out, re.IGNORECASE)
            if scdns:
                return scdns[0]

            return None
        except Exception as e:
            utils.kodilog('FaselHD Resolver: Node eval error - {}'.format(str(e)))
            return None
