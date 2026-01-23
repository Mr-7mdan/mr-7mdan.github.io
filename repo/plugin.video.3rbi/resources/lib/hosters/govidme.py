# -*- coding: utf-8 -*-
# Based on vStream govidme resolver

import re
from resources.lib import utils

class GovidMeResolver:
    """Resolver for govid.me hosting sites"""
    
    def __init__(self):
        self.name = 'GovidMe'
        self.domains = ['govid.me']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve govid.me URL to direct video link
        
        Args:
            url: GovidMe embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('GovidMe Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': 'Android',
                'Referer': 'https://cima-club.io/'
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('GovidMe Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('GovidMe Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video URLs with quality: file:"...",label:"..."
            matches = re.findall(r'file:\s*["\']([^"\'<]+)["\']\s*,\s*label:\s*["\']([^"\'<]+)["\']', html)
            if not matches:
                utils.kodilog('GovidMe Resolver: No video sources found')
                return None
            
            # Get highest quality (last in list)
            video_url, quality = matches[-1]
            
            # URL encode special characters
            video_url = video_url.replace('[', '%5B').replace(']', '%5D').replace('+', '%20')
            
            utils.kodilog('GovidMe Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
            
            # Return with headers
            response_headers = {
                'User-Agent': 'Android',
                'Referer': url
            }
            
            return (video_url, quality, response_headers)
            
        except Exception as e:
            utils.kodilog('GovidMe Resolver: Error - {}'.format(str(e)))
            return None
