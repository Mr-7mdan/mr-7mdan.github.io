# -*- coding: utf-8 -*-
# Based on vStream filemoon resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class FilemoonResolver:
    """Resolver for filemoon.sx and related domains"""
    
    def __init__(self):
        self.name = 'Filemoon'
        self.domains = ['filemoon.sx', 'filemoon.to', 'filemoon.in']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve filemoon URL to direct video link
        
        Args:
            url: Filemoon embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Filemoon Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Filemoon Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Filemoon Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Look for packed JavaScript
            packed_match = re.search(r'(\s*eval\s*\(\s*function\(p,a,c,k,e(?:.|\s)+?)</script>', html, re.DOTALL)
            if not packed_match:
                utils.kodilog('Filemoon Resolver: No packed JavaScript found')
                return None
            
            utils.kodilog('Filemoon Resolver: Unpacking JavaScript...')
            try:
                packer = cPacker()
                packed_code = packed_match.group(1)
                unpacked = packer.unpack(packed_code)
                utils.kodilog('Filemoon Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
            except Exception as e:
                utils.kodilog('Filemoon Resolver: Failed to unpack - {}'.format(str(e)))
                return None
            
            # Extract video URL: file:"..."
            match = re.search(r'file:\s*["\']([^"\']+)["\']', unpacked, re.IGNORECASE)
            if not match:
                utils.kodilog('Filemoon Resolver: No video URL found in unpacked code')
                return None
            
            video_url = match.group(1)
            utils.kodilog('Filemoon Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Filemoon Resolver: Error - {}'.format(str(e)))
            return None
