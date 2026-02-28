# -*- coding: utf-8 -*-
"""
Generic Hoster Resolver
Fallback resolver for common video players (JWPlayer, Plyr, VideoJS, etc.)
Used when no specific resolver is found for a hoster
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.packer import cPacker


class GenericResolver(HosterResolver):
    def __init__(self):
        self.name = "Generic"
        # This resolver matches ANY domain - it's a fallback
        self.domains = ['*']
    
    def can_resolve(self, url):
        """
        Generic resolver can handle any URL - always returns True
        Used as fallback when no specific resolver matches
        """
        return True
    
    def matches(self, url):
        """
        Generic resolver always returns False for matches()
        It should only be used as a fallback by HosterManager
        """
        return False
    
    def resolve(self, url):
        """
        Try to extract video from common player patterns
        
        Supports:
        - JWPlayer (sources array)
        - Plyr
        - VideoJS
        - HTML5 video/source tags
        - Direct m3u8/mp4 URLs in JavaScript
        
        Args:
            url: Any embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Generic Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            html = utils.getHtml(url, headers=headers)
            
            # Handle case where getHtml returns non-string (e.g., list or None)
            if not html or not isinstance(html, str):
                utils.kodilog('Generic Resolver: Invalid HTML response (type: {})'.format(type(html)))
                return None
            
            utils.kodilog('Generic Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Check for packed JavaScript and unpack it
            packer = cPacker()
            # Look for eval(function(p,a,c,k,e,d) anywhere in the HTML
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e,d\).*?)</script>', html, re.DOTALL)
            if packed_match:
                utils.kodilog('Generic Resolver: Detected packed JavaScript, unpacking...')
                try:
                    packed_code = packed_match.group(1)
                    unpacked = packer.unpack(packed_code)
                    # Use unpacked code for extraction
                    html = unpacked + '\n' + html  # Keep both for fallback
                    utils.kodilog('Generic Resolver: Successfully unpacked JavaScript ({} bytes)'.format(len(unpacked)))
                except Exception as e:
                    utils.kodilog('Generic Resolver: Failed to unpack JavaScript - {}'.format(str(e)))
            
            video_url = None
            quality = 'HD'
            
            # Pattern 1: JWPlayer sources array
            # sources: [{file:"https://...m3u8"}] or sources:[{file:"https://...mp4"}]
            match = re.search(r'sources:\s*\[\s*\{\s*(?:file|src)\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
            if match:
                video_url = match.group(1)
                utils.kodilog('Generic Resolver: Found JWPlayer sources')
            
            # Pattern 2: JWPlayer file property
            # file: "https://...m3u8"
            if not video_url:
                match = re.search(r'file\s*:\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Generic Resolver: Found JWPlayer file property')
            
            # Pattern 3: Plyr source
            # data-plyr-provider or source src in Plyr context
            if not video_url:
                match = re.search(r'data-plyr-(?:provider|embed-id|config).*?["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Generic Resolver: Found Plyr source')
            
            # Pattern 4: VideoJS source
            # <source src="..." type="video/mp4">
            if not video_url:
                match = re.search(r'<source[^>]+src\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Generic Resolver: Found HTML5 source tag')
            
            # Pattern 5: HTML5 video tag
            # <video src="...">
            if not video_url:
                match = re.search(r'<video[^>]+src\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Generic Resolver: Found HTML5 video tag')
            
            # Pattern 6: Direct m3u8/mp4 URL in JavaScript variables
            # var video = "https://...m3u8" or let src = "https://...mp4"
            if not video_url:
                match = re.search(r'(?:var|let|const)\s+\w+\s*=\s*["\']([^"\']+\.(?:m3u8|mp4)[^"\']*)["\']', html, re.IGNORECASE)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Generic Resolver: Found JS variable with video URL')
            
            # Pattern 7: Generic m3u8/mp4 URL search (less reliable, last resort)
            if not video_url:
                # Look for full URLs with m3u8 or mp4
                # Skip placeholder URLs with {series}, {episode}, etc.
                matches = re.findall(r'https?://[^\s"\'<>]+\.(?:m3u8|mp4)(?:\?[^\s"\'<>]*)?', html, re.IGNORECASE)
                for match in matches:
                    # Skip placeholder URLs
                    if '{' in match or '}' in match:
                        continue
                    video_url = match
                    utils.kodilog('Generic Resolver: Found generic video URL')
                    break
            
            if not video_url:
                utils.kodilog('Generic Resolver: No video source found')
                return None
            
            # Clean up URL
            video_url = video_url.replace('\\/', '/')
            video_url = video_url.strip()
            
            # Make URL absolute if relative
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            elif video_url.startswith('/'):
                from urllib.parse import urlparse
                parsed = urlparse(url)
                video_url = '{}://{}{}'.format(parsed.scheme, parsed.netloc, video_url)
            
            utils.kodilog('Generic Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Detect quality from URL or HTML
            if '1080' in video_url or '1080p' in html:
                quality = '1080p'
            elif '720' in video_url or '720p' in html:
                quality = '720p'
            elif '480' in video_url or '480p' in html:
                quality = '480p'
            elif '360' in video_url or '360p' in html:
                quality = '360p'
            
            # Extract domain for referer
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = '{}://{}'.format(parsed.scheme, parsed.netloc)
            
            # Headers for playback
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': domain + '/',
                'Origin': domain
            }
            
            return (video_url, quality, playback_headers)
            
        except Exception as e:
            utils.kodilog('Generic Resolver: Error - {}'.format(str(e)))
            return None
