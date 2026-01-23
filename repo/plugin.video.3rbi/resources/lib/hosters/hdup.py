# -*- coding: utf-8 -*-
# Based on vStream hdup resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class HdupResolver:
    """Resolver for hdup hosting sites"""
    
    def __init__(self):
        self.name = 'Hdup'
        self.domains = ['hdup.to', 'hdup.tv']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve hdup URL to direct video link
        
        Args:
            url: Hdup embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Hdup Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Hdup Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Hdup Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Look for packed JavaScript
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e(?:.|\s)+?\))</script>', html, re.DOTALL)
            if not packed_match:
                utils.kodilog('Hdup Resolver: No packed JavaScript found')
                return None
            
            utils.kodilog('Hdup Resolver: Unpacking JavaScript...')
            try:
                packer = cPacker()
                packed_code = packed_match.group(1)
                unpacked = packer.unpack(packed_code)
                utils.kodilog('Hdup Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
            except Exception as e:
                utils.kodilog('Hdup Resolver: Failed to unpack - {}'.format(str(e)))
                return None
            
            # Extract video URLs with quality: file:"...",label:"..."
            matches = re.findall(r'file:\s*["\']([^"\']+)["\']\s*,\s*label:\s*["\']([^"\']+)["\']', unpacked)
            if not matches:
                utils.kodilog('Hdup Resolver: No video sources found in unpacked code')
                return None
            
            # Get highest quality (last in list)
            video_url, quality = matches[-1]
            utils.kodilog('Hdup Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, quality, response_headers)
            
        except Exception as e:
            utils.kodilog('Hdup Resolver: Error - {}'.format(str(e)))
            return None
