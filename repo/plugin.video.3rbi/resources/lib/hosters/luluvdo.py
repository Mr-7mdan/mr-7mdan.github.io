# -*- coding: utf-8 -*-
"""
LuluVdo Resolver
Extracts video URLs from luluvdo.com embed pages
"""

import re
from resources.lib import utils

class LuluvdoResolver:
    """Resolver for luluvdo.com"""
    
    def __init__(self):
        self.name = "LuluVdo"
        self.domains = ['luluvdo.com', 'lulustream.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve luluvdo.com embed URL to video URL
        
        Args:
            url: LuluVdo embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html:
                utils.kodilog('LuluVdo: No HTML received')
                return None
            
            utils.kodilog('LuluVdo: Received {} bytes'.format(len(html)))
            
            # Extract m3u8 URL from file: pattern
            # Pattern: file: "https://xxx.tnmr.org/hls2/.../master.m3u8?t=..."
            m3u8_pattern = r'file\s*:\s*"(https?://[^"]+\.m3u8[^"]*)"'
            match = re.search(m3u8_pattern, html)
            
            if match:
                video_url = match.group(1)
                utils.kodilog('LuluVdo: Found m3u8: {}'.format(video_url[:80]))
                
                playback_headers = {
                    'Referer': url,
                    'User-Agent': utils.USER_AGENT
                }
                
                return (video_url, 'HD', playback_headers)
            
            utils.kodilog('LuluVdo: No m3u8 pattern found')
            return None
            
        except Exception as e:
            utils.kodilog('LuluVdo: Error - {}'.format(str(e)))
            return None
