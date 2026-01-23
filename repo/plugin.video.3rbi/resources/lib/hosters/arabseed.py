# -*- coding: utf-8 -*-
# Based on vStream arabseed resolver

import re
from resources.lib import utils

class ArabseedResolver:
    """Resolver for ArabSeed direct video hosting"""
    
    def __init__(self):
        self.name = 'ArabSeed'
        self.domains = ['arabseed.', 'asd.homes']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        # Avoid conflict with play.php wrapper (handled by arabseed_play.py)
        if 'play.php' in url or '/play/' in url:
            return False
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve ArabSeed URL to direct video link
        
        Args:
            url: ArabSeed video page URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('ArabSeed Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Mobile Safari/537.36',
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('ArabSeed Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('ArabSeed Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video source: <source src="..." type="video/mp4">
            match = re.search(r'<source\s+src="([^"]+)"\s+type="video/mp4"', html)
            if not match:
                utils.kodilog('ArabSeed Resolver: No video source found')
                return None
            
            video_url = match.group(1)
            utils.kodilog('ArabSeed Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers (verifypeer=false handled by Kodi)
            response_headers = {
                'User-Agent': headers['User-Agent']
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('ArabSeed Resolver: Error - {}'.format(str(e)))
            return None
