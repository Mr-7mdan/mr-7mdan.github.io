# -*- coding: utf-8 -*-
# estream.to resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class EstreamResolver:
    """Resolver for estream.to"""
    
    def __init__(self):
        self.name = 'estream'
        self.domains = ['estream.to', 'estream.in']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve estream URL to direct video link
        
        Args:
            url: estream embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('estream Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            # First request - get redirect URL
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('estream Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('estream Resolver: First request {} bytes'.format(len(html)))
            
            # Check for JavaScript redirect
            redirect_match = re.search(r"window\.location\.replace\(['\"]([^'\"]+)['\"]", html)
            if redirect_match:
                redirect_url = redirect_match.group(1)
                utils.kodilog('estream Resolver: Following redirect')
                
                # Fetch the actual player page
                html = utils.getHtml(redirect_url, headers=headers)
                
                if not html or not isinstance(html, str):
                    utils.kodilog('estream Resolver: Invalid redirect response')
                    return None
                
                utils.kodilog('estream Resolver: Player page {} bytes'.format(len(html)))
            
            # Look for packed JavaScript
            packed_match = re.search(r'(\s*eval\s*\(\s*function\(p,a,c,k,e(?:.|\s)+?)</script>', html, re.DOTALL)
            if packed_match:
                utils.kodilog('estream Resolver: Unpacking JavaScript...')
                try:
                    packer = cPacker()
                    packed_code = packed_match.group(1)
                    unpacked = packer.unpack(packed_code)
                    utils.kodilog('estream Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
                    html = unpacked  # Search in unpacked code
                except Exception as e:
                    utils.kodilog('estream Resolver: Unpack failed - {}'.format(str(e)))
                    # Continue with original HTML
            
            # Debug: show what we're searching
            utils.kodilog('estream Resolver: Searching in {} chars of content'.format(len(html)))
            utils.kodilog('estream Resolver: Sample content: {}'.format(html[:300]))
            
            # Look for video URL in multiple patterns
            patterns = [
                r'file:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                r'file:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                r'"file":\s*"([^"]+)"',
                r'sources:\s*\[.*?"file":\s*"([^"]+)"',
            ]
            
            video_url = None
            for i, pattern in enumerate(patterns, 1):
                match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('estream Resolver: Found video URL: {}'.format(video_url[:100]))
                    break
            
            if not video_url:
                utils.kodilog('estream Resolver: No video URL found')
                return None
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('estream Resolver: Error - {}'.format(str(e)))
            return None
