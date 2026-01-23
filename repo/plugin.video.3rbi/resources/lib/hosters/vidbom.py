# -*- coding: utf-8 -*-
# Based on vStream vidbom resolver

import re
from resources.lib import utils

class VidbomResolver:
    """Resolver for vidbom.com, vedbam.xyz"""
    
    def __init__(self):
        self.name = 'Vidbom'
        self.domains = ['vidbom.com', 'vidbom.net', 'vedbam.xyz']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vidbom URL to direct video link
        
        Args:
            url: Vidbom embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Vidbom Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Vidbom Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Vidbom Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video URL: sources: [{file:"..."}]
            match = re.search(r'sources:\s*\[\s*\{\s*file:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if not match:
                utils.kodilog('Vidbom Resolver: No video source found')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Vidbom Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': headers['User-Agent'],
                'Referer': 'https://vedbam.xyz/'
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Vidbom Resolver: Error - {}'.format(str(e)))
            return None
