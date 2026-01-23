# -*- coding: utf-8 -*-
"""
ReviewRate Resolver
Extracts direct video URLs from reviewrate.net embed pages
"""

import re
from resources.lib import utils

class ReviewRateResolver:
    """Resolver for reviewrate.net"""
    
    def __init__(self):
        self.name = "ReviewRate"
        self.domains = ['reviewrate.net', 'm.reviewrate.net']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve reviewrate.net embed URL to video URL
        
        Args:
            url: ReviewRate embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page
            html = utils.getHtml(url)
            
            # Extract video source from <source src="..."> tag
            source_match = re.search(r'<source\s+src="([^"]+)"', html)
            if source_match:
                video_url = source_match.group(1)
                utils.kodilog('ReviewRate: Found video URL: {}'.format(video_url[:100]))
                
                # Determine quality from URL or default
                quality = '720p' if '720' in video_url else 'HD'
                
                # Video requires Referer header to avoid 403 errors
                headers = {
                    'Referer': url,  # Use the embed page URL as referer
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                return (video_url, quality, headers)
            
            utils.kodilog('ReviewRate: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('ReviewRate: Error resolving - {}'.format(str(e)))
            return None
