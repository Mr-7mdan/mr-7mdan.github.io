# -*- coding: utf-8 -*-
# Based on vStream megadrive resolver

import re
from resources.lib import utils

class MegadriveResolver:
    """Resolver for megadrive video hosting"""
    
    def __init__(self):
        self.name = 'Megadrive'
        self.domains = ['megadrive.to']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve megadrive URL to direct video link
        
        Args:
            url: Megadrive embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Megadrive Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Megadrive Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Megadrive Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video source: <source ... src='...'>
            match = re.search(r"<source[^>]+src='([^']+)'", html)
            if not match:
                utils.kodilog('Megadrive Resolver: No video source found')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Megadrive Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Megadrive Resolver: Error - {}'.format(str(e)))
            return None
