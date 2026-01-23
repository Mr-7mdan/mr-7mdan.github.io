# -*- coding: utf-8 -*-
# Based on vStream anavids resolver

import re
from resources.lib import utils

class AnavidsResolver:
    """Resolver for anavids hosting sites"""
    
    def __init__(self):
        self.name = 'Anavids'
        self.domains = ['anavids.com', 'anavids.net']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve anavids URL to direct video link
        
        Args:
            url: Anavids embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Anavids Resolver: Attempting {}'.format(url[:100]))
            
            # Convert to embed format if needed
            if 'embed-' not in url:
                url = url.replace('.com/', '.com/embed-')
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Anavids Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Anavids Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video URLs with quality labels: {file:"...",label:"..."}
            matches = re.findall(r'\{file:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']', html)
            if not matches:
                utils.kodilog('Anavids Resolver: No video sources found')
                return None
            
            # Get highest quality (last in list)
            video_url, quality = matches[-1]
            utils.kodilog('Anavids Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, quality, response_headers)
            
        except Exception as e:
            utils.kodilog('Anavids Resolver: Error - {}'.format(str(e)))
            return None
