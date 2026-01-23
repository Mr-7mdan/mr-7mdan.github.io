# -*- coding: utf-8 -*-
"""
Bysezejataos.com Hoster Resolver
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver
from resources.lib.packer import cPacker


class BysezejataosResolver(HosterResolver):
    def __init__(self):
        self.name = "Bysezejataos"
        self.domains = ['bysezejataos.com']
    
    def resolve(self, url):
        """
        Resolve Bysezejataos embed URL to video stream
        
        Args:
            url: Bysezejataos embed URL (e.g., https://bysezejataos.com/e/xxxxx)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Bysezejataos: Resolving {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': 'https://a.asd.homes/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            html = utils.getHtml(url, headers=headers)
            utils.kodilog('Bysezejataos: Received {} bytes of HTML'.format(len(html)))
            
            # Check for packed JavaScript and unpack it
            packer = cPacker()
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e,d\).*?)</script>', html, re.DOTALL)
            if packed_match:
                utils.kodilog('Bysezejataos: Detected packed JavaScript, unpacking...')
                try:
                    packed_code = packed_match.group(1)
                    unpacked = packer.unpack(packed_code)
                    html = unpacked + '\n' + html  # Use unpacked code for extraction
                    utils.kodilog('Bysezejataos: Successfully unpacked JavaScript ({} bytes)'.format(len(unpacked)))
                except Exception as e:
                    utils.kodilog('Bysezejataos: Failed to unpack JavaScript - {}'.format(str(e)))
            
            # Try multiple patterns for video sources
            
            # Pattern 1: JWPlayer sources
            source_match = re.search(r'sources:\s*\[\s*\{\s*file\s*:\s*"([^"]+)"', html, re.DOTALL)
            
            # Pattern 2: Direct file property
            if not source_match:
                source_match = re.search(r'file\s*:\s*"(https?://[^"]+\.(?:m3u8|mp4)[^"]*)"', html, re.IGNORECASE)
            
            # Pattern 3: General video URL search
            if not source_match:
                source_match = re.search(r'(https?://[^\s"<>]+\.(?:m3u8|mp4)[^\s"<>]*)', html)
            
            if not source_match:
                utils.kodilog('Bysezejataos: No video source found')
                return None
            
            video_url = source_match.group(1)
            
            # Clean up URL
            video_url = video_url.replace('\\/', '/')
            
            utils.kodilog('Bysezejataos: Found video URL: {}'.format(video_url[:100]))
            
            # Detect quality
            quality = 'HD'
            if '720' in video_url or '720p' in html:
                quality = '720p'
            elif '1080' in video_url or '1080p' in html:
                quality = '1080p'
            elif '480' in video_url or '480p' in html:
                quality = '480p'
            
            # Headers for playback
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': 'https://bysezejataos.com/',
                'Origin': 'https://bysezejataos.com'
            }
            
            return (video_url, quality, playback_headers)
            
        except Exception as e:
            utils.kodilog('Bysezejataos: Error resolving - {}'.format(str(e)))
            return None
