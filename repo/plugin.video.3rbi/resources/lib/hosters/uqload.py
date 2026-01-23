# -*- coding: utf-8 -*-
"""
Uqload Resolver
Extracts video URLs from uqload embed pages
Supports multiple TLDs: .cx, .to, .net, .co, .org, .ws, .bz
"""

import re
from resources.lib import utils

class UqloadResolver:
    """Resolver for uqload hosting (multiple TLDs)"""
    
    def __init__(self):
        self.name = "Uqload"
        # Support all common uqload TLDs
        self.domains = ['uqload.']  # Matches any uqload.* domain
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve uqload URL to direct video link
        
        Args:
            url: Uqload embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Uqload Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            if not html:
                utils.kodilog('Uqload Resolver: No HTML response')
                return None
            
            # Method 1: Extract from player sources array
            # Pattern: sources:["URL"] or sources: ["URL"]
            sources_match = re.search(r'sources\s*:\s*\[\s*["\']([^"\']+)["\']', html)
            if sources_match:
                video_url = sources_match.group(1)
                utils.kodilog('Uqload Resolver: Found video URL from sources: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Method 2: Extract from sources JavaScript variable
            # Pattern: var sources = ["URL"];
            var_match = re.search(r'var\s+sources\s*=\s*\[\s*["\']([^"\']+)["\']', html)
            if var_match:
                video_url = var_match.group(1)
                utils.kodilog('Uqload Resolver: Found video URL from var: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Method 3: Extract direct .mp4 URL
            mp4_match = re.search(r'(https?://[^"\'<>\s]+\.mp4[^"\'<>\s]*)', html)
            if mp4_match:
                video_url = mp4_match.group(1)
                utils.kodilog('Uqload Resolver: Found direct mp4 URL: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            utils.kodilog('Uqload Resolver: No video URL found')
            return None
            
        except Exception as e:
            utils.kodilog('Uqload Resolver: Error - {}'.format(str(e)))
            return None
