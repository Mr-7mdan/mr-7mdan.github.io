# -*- coding: utf-8 -*-
# Based on vStream updown resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class UpdownResolver:
    """Resolver for updown hosting sites"""
    
    def __init__(self):
        self.name = 'Updown'
        self.domains = ['updown.to', 'updown.bz']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve updown URL to direct video link
        
        Args:
            url: Updown embed URL (may include |Referer=...)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Updown Resolver: Attempting {}'.format(url[:100]))
            
            # Extract Referer if provided
            if '|Referer=' in url:
                parts = url.split('|Referer=')
                clean_url = parts[0]
                referer = parts[1]
            else:
                clean_url = url
                referer = url
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer
            }
            
            html = utils.getHtml(clean_url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Updown Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Updown Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Look for packed JavaScript
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e(?:.|\s)+?\))</script>', html, re.DOTALL)
            if not packed_match:
                utils.kodilog('Updown Resolver: No packed JavaScript found')
                return None
            
            utils.kodilog('Updown Resolver: Unpacking JavaScript...')
            try:
                packer = cPacker()
                packed_code = packed_match.group(1)
                unpacked = packer.unpack(packed_code)
                utils.kodilog('Updown Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
            except Exception as e:
                utils.kodilog('Updown Resolver: Failed to unpack - {}'.format(str(e)))
                return None
            
            # Extract video URL: file:"..."
            match = re.search(r'file:\s*["\']([^"\']+)["\']', unpacked)
            if not match:
                utils.kodilog('Updown Resolver: No video URL found in unpacked code')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Updown Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': clean_url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Updown Resolver: Error - {}'.format(str(e)))
            return None
