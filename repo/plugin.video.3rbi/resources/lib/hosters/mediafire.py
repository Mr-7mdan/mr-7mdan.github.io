# -*- coding: utf-8 -*-
# Based on vStream mediafire resolver

import re
from resources.lib import utils

class MediafireResolver:
    """Resolver for mediafire file hosting"""
    
    def __init__(self):
        self.name = 'Mediafire'
        self.domains = ['mediafire.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve mediafire URL to direct download link
        
        Args:
            url: Mediafire file URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Mediafire Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Mediafire Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Mediafire Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract download link: aria-label="Download file" ... href="..."
            match = re.search(r'aria-label="Download file"[^>]+href="([^"]+)"', html)
            if not match:
                utils.kodilog('Mediafire Resolver: No download link found')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Mediafire Resolver: Found download URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Mediafire Resolver: Error - {}'.format(str(e)))
            return None
