# -*- coding: utf-8 -*-
"""
Luluvid/Lulustream Resolver
Extracts video URLs from luluvid.com/lulustream embed pages
"""

import re
from resources.lib import utils

class LuluvidResolver:
    """Resolver for luluvid.com/lulustream hosting"""
    
    def __init__(self):
        self.name = "Luluvid"
        self.domains = ['luluvid.com', 'lulustream.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve luluvid URL to direct video link (HLS m3u8)
        
        Args:
            url: Luluvid embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Luluvid Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            if not html:
                utils.kodilog('Luluvid Resolver: No HTML response')
                return None
            
            # Method 1: Extract from JWPlayer sources (HLS)
            # Pattern: sources: [{file:"URL.m3u8"}] or sources:[{file:"URL"}]
            sources_match = re.search(r'sources\s*:\s*\[\s*{\s*file\s*:\s*["\']([^"\']+)["\']', html)
            if sources_match:
                video_url = sources_match.group(1)
                utils.kodilog('Luluvid Resolver: Found HLS URL from sources: {}'.format(video_url[:100]))
                return (video_url, 'HLS', headers)
            
            # Method 2: Extract direct file: "URL" pattern
            file_match = re.search(r'file\s*:\s*["\']([^"\']+\.m3u8[^"\']*)["\']', html)
            if file_match:
                video_url = file_match.group(1)
                utils.kodilog('Luluvid Resolver: Found HLS URL from file: {}'.format(video_url[:100]))
                return (video_url, 'HLS', headers)
            
            # Method 3: Look for any m3u8 URL in HTML
            m3u8_match = re.search(r'(https?://[^"\'<>\s]+\.m3u8[^"\'<>\s]*)', html)
            if m3u8_match:
                video_url = m3u8_match.group(1)
                utils.kodilog('Luluvid Resolver: Found direct m3u8 URL: {}'.format(video_url[:100]))
                return (video_url, 'HLS', headers)
            
            utils.kodilog('Luluvid Resolver: No video URL found')
            return None
            
        except Exception as e:
            utils.kodilog('Luluvid Resolver: Error - {}'.format(str(e)))
            return None
