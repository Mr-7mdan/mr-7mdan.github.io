# -*- coding: utf-8 -*-
"""
VOE Resolver
Extracts video URLs from voe.sx embed pages
"""

import re
from resources.lib import utils

class VoeResolver:
    """Resolver for voe.sx"""
    
    def __init__(self):
        self.name = "VOE"
        self.domains = ['voe.sx', 'lauradaydo.com', 'voe.to']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve voe.sx embed URL to video URL
        
        Args:
            url: VOE embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://a.asd.homes/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            html = utils.getHtml(url, headers=headers)
            
            utils.kodilog('VOE: Received {} bytes of HTML'.format(len(html)))
            
            # Check for JavaScript redirect to lauradaydo.com or other domains
            redirect_match = re.search(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"]", html)
            if redirect_match and 'voe.sx' not in redirect_match.group(1):
                redirect_url = redirect_match.group(1)
                utils.kodilog('VOE: Following JavaScript redirect to: {}'.format(redirect_url[:100]))
                html = utils.getHtml(redirect_url, headers=headers)
                utils.kodilog('VOE: After redirect, received {} bytes of HTML'.format(len(html)))
            
            # VOE typically has video URL in various formats:
            # 1. 'hls': 'https://...m3u8'
            # 2. 'mp4': 'https://...mp4'
            # 3. sources: 'https://...mp4'
            
            patterns = [
                r"var\s+source\s*=\s*['\"]([^'\"]+)['\"]",  # lauradaydo.com pattern
                r"'hls'\s*:\s*'([^']+)'",
                r'"hls"\s*:\s*"([^"]+)"',
                r"'mp4'\s*:\s*'([^']+)'",
                r'"mp4"\s*:\s*"([^"]+)"',
                r'sources:\s*["\']([^"\']+)["\']',
                r'src:\s*["\']([^"\']+\.(?:mp4|m3u8))',
            ]
            
            video_url = None
            for pattern in patterns:
                match = re.search(pattern, html, re.DOTALL)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('VOE: Found video URL with pattern: {}'.format(pattern[:30]))
                    break
            
            if video_url:
                utils.kodilog('VOE: Found video URL: {}'.format(video_url[:100]))
                
                # Determine quality
                quality = 'HD'
                if '1080' in video_url or '1080' in html:
                    quality = '1080p'
                elif '720' in video_url or '720' in html:
                    quality = '720p'
                elif '480' in video_url:
                    quality = '480p'
                
                # Video requires headers
                playback_headers = {
                    'Referer': url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://voe.sx'
                }
                
                return (video_url, quality, playback_headers)
            
            utils.kodilog('VOE: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('VOE: Error resolving - {}'.format(str(e)))
            return None
