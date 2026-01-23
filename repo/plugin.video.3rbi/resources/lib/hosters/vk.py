# -*- coding: utf-8 -*-
"""
VK.com Resolver
Extracts video URLs from vk.com embed pages
"""

import re
import json
from resources.lib import utils

class VKResolver:
    """Resolver for vk.com (VKontakte)"""
    
    def __init__(self):
        self.name = "VK.com"
        self.domains = ['vk.com', 'vk.ru']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vk.com embed URL to video URL
        
        Args:
            url: VK.com embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://fajer.show/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            html = utils.getHtml(url, headers=headers)
            
            utils.kodilog('VK.com: Received {} bytes of HTML'.format(len(html)))
            
            # Check for error/restriction messages
            if 'video_ext_msg' in html or 'video is restricted' in html.lower():
                utils.kodilog('VK.com: Video is restricted or unavailable')
                return None
            
            # VK.com has player data in JavaScript variables
            # Common patterns:
            # 1. var playerParams = {...}
            # 2. "url1080":"https://..."
            # 3. "url720":"https://..."
            # 4. "url480":"https://..."
            # 5. "url360":"https://..."
            # 6. "url240":"https://..."
            # 7. "hls":"https://...m3u8"
            
            patterns = [
                (r'"hls"\s*:\s*"([^"]+)"', 'HLS'),
                (r'"url1080"\s*:\s*"([^"]+)"', '1080p'),
                (r'"url720"\s*:\s*"([^"]+)"', '720p'),
                (r'"url480"\s*:\s*"([^"]+)"', '480p'),
                (r'"url360"\s*:\s*"([^"]+)"', '360p'),
                (r'"url240"\s*:\s*"([^"]+)"', '240p'),
            ]
            
            video_url = None
            quality = 'Unknown'
            
            for pattern, qual in patterns:
                match = re.search(pattern, html)
                if match:
                    video_url = match.group(1)
                    # Unescape URL
                    video_url = video_url.replace('\\/', '/')
                    quality = qual
                    utils.kodilog('VK.com: Found {} video: {}'.format(qual, video_url[:100]))
                    break
            
            if video_url:
                # Video requires headers
                playback_headers = {
                    'Referer': 'https://vk.com/',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://vk.com'
                }
                
                return (video_url, quality, playback_headers)
            
            utils.kodilog('VK.com: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('VK.com: Error resolving - {}'.format(str(e)))
            return None
