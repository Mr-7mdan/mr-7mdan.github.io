# -*- coding: utf-8 -*-
# Based on vStream mixdrop resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class MixdropResolver:
    """Resolver for mixdrop.sn, mixdrop.net, mixdrop.to, etc."""
    
    def __init__(self):
        self.name = 'Mixdrop'
        self.domains = ['mixdrop.sn', 'mixdrop.net', 'mixdrop.to', 'mixdrop.co', 'mixdrop.ch', 'mixdrop.bz', 'm1xdrop.bz']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve mixdrop URL to direct video link
        
        Args:
            url: Mixdrop embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Mixdrop Resolver: Attempting {}'.format(url[:100]))
            
            # Convert /f/ to /e/ for embed format
            url = url.replace('/f/', '/e/')
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Cookie': 'hds2=1'  # Required cookie for mixdrop
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Mixdrop Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Mixdrop Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Find and unpack JavaScript
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e,d\).*?)</script>', html, re.DOTALL)
            if not packed_match:
                utils.kodilog('Mixdrop Resolver: No packed JavaScript found')
                return None
            
            utils.kodilog('Mixdrop Resolver: Unpacking JavaScript...')
            try:
                packer = cPacker()
                packed_code = packed_match.group(1)
                unpacked = packer.unpack(packed_code)
                utils.kodilog('Mixdrop Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
            except Exception as e:
                utils.kodilog('Mixdrop Resolver: Failed to unpack - {}'.format(str(e)))
                return None
            
            # Extract video URL from unpacked code
            # Pattern: wurl="..." or similar variations
            video_url = None
            
            # Try wurl pattern
            match = re.search(r'wurl\s*=\s*["\']([^"\']+)["\']', unpacked)
            if match:
                video_url = match.group(1)
                utils.kodilog('Mixdrop Resolver: Found wurl pattern')
            
            # Try vsrc pattern (alternative)
            if not video_url:
                match = re.search(r'vsrc\d*\s*=\s*["\']([^"\']+)["\']', unpacked)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Mixdrop Resolver: Found vsrc pattern')
            
            # Try furl pattern (another alternative)
            if not video_url:
                match = re.search(r'furl\s*=\s*["\']([^"\']+)["\']', unpacked)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Mixdrop Resolver: Found furl pattern')
            
            if not video_url:
                utils.kodilog('Mixdrop Resolver: No video URL found in unpacked code')
                return None
            
            # Fix protocol-relative URLs
            if video_url.startswith('//'):
                video_url = 'https:' + video_url
            
            utils.kodilog('Mixdrop Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Origin': 'https://' + url.split('/')[2] if '/' in url else 'https://mixdrop.sn'
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Mixdrop Resolver: Error - {}'.format(str(e)))
            return None

def get_resolver():
    """Factory function to get resolver instance"""
    return MixdropResolver()
