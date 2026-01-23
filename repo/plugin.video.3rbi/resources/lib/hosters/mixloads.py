# -*- coding: utf-8 -*-
# Based on vStream mixloads resolver

import re
from resources.lib import utils

class MixloadsResolver:
    """Resolver for mixloads hosting sites"""
    
    def __init__(self):
        self.name = 'Mixloads'
        self.domains = ['mixloads.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve mixloads URL to direct video link
        
        Args:
            url: Mixloads embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Mixloads Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Mixloads Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Mixloads Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video URLs with quality: {file:"...",label:"..."}
            matches = re.findall(r'\{file:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']', html)
            if not matches:
                utils.kodilog('Mixloads Resolver: No video sources found')
                return None
            
            # Get highest quality (last in list)
            video_url, quality = matches[-1]
            utils.kodilog('Mixloads Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, quality, response_headers)
            
        except Exception as e:
            utils.kodilog('Mixloads Resolver: Error - {}'.format(str(e)))
            return None
