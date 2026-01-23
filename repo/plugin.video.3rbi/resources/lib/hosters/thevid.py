# -*- coding: utf-8 -*-
# Based on vStream thevid resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class ThevidResolver:
    """Resolver for thevid hosting sites"""
    
    def __init__(self):
        self.name = 'Thevid'
        self.domains = ['thevid.net', 'thevid.co', 'thevid.tv']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve thevid URL to direct video link
        
        Args:
            url: Thevid embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Thevid Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Thevid Resolver: Invalid HTML response')
                return None
            
            if 'Not Found' in html:
                utils.kodilog('Thevid Resolver: Video not found (404)')
                return None
            
            utils.kodilog('Thevid Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Look for packed JavaScript
            packed_match = re.search(r'(\s*eval\s*\(\s*function(?:.|\s)+?)</script>', html, re.DOTALL)
            if not packed_match:
                utils.kodilog('Thevid Resolver: No packed JavaScript found')
                return None
            
            utils.kodilog('Thevid Resolver: Unpacking JavaScript...')
            try:
                packer = cPacker()
                packed_code = packed_match.group(1)
                unpacked = packer.unpack(packed_code)
                utils.kodilog('Thevid Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
            except Exception as e:
                utils.kodilog('Thevid Resolver: Failed to unpack - {}'.format(str(e)))
                return None
            
            # Extract video URL: var vldAb="...";
            match = re.search(r'var vldAb\s*=\s*["\']([^"\']+)["\']', unpacked)
            if not match:
                utils.kodilog('Thevid Resolver: No video URL found in unpacked code')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Thevid Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Thevid Resolver: Error - {}'.format(str(e)))
            return None
