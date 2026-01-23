# -*- coding: utf-8 -*-
"""
ArabSeed Play.php Resolver
Unwraps ArabSeed's play.php wrapper to extract the actual hoster iframe URL
"""

import re
from resources.lib import utils

class ArabSeedPlayResolver:
    """Resolver for ArabSeed play.php wrapper"""
    
    def __init__(self):
        self.name = "ArabSeed Play"
        self.domains = ['a.asd.homes/play.php', 'a.asd.homes/play/']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve ArabSeed play.php to actual hoster URL
        
        Args:
            url: ArabSeed play.php URL with base64 encoded hoster URL
            
        Returns:
            (iframe_url, quality) tuple or None if failed
        """
        try:
            # play.php requires referer header
            headers = {
                'Referer': 'https://a.asd.homes/',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Fetch the play.php page
            html = utils.getHtml(url, headers=headers)
            
            # Extract iframe src
            iframe_match = re.search(r'<iframe\s+src="([^"]+)"', html)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                utils.kodilog('ArabSeed Play: Extracted iframe URL: {}'.format(iframe_url[:100]))
                
                # Return the iframe URL with Unknown quality (will be resolved by next resolver)
                return (iframe_url, 'Unknown')
            
            utils.kodilog('ArabSeed Play: No iframe found')
            return None
            
        except Exception as e:
            utils.kodilog('ArabSeed Play: Error resolving - {}'.format(str(e)))
            return None
