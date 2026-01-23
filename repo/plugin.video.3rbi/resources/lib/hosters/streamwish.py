# -*- coding: utf-8 -*-
# Based on vStream streamwish resolver

import re
from resources.lib import utils
from resources.lib.packer import cPacker

class StreamwishResolver:
    """Resolver for streamwish and related domains"""
    
    def __init__(self):
        self.name = 'Streamwish'
        self.domains = ['streamwish.to', 'streamwish.com', 'awish.pro', 'wishembed.pro']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve streamwish URL to direct video link
        
        Args:
            url: Streamwish embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Streamwish Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Streamwish Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Streamwish Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Pattern 1: Direct file:"..." pattern
            match = re.search(r'file:\s*"(https[^"]+)"', html)
            if match:
                video_url = match.group(1)
                utils.kodilog('Streamwish Resolver: Found direct file URL: {}'.format(video_url[:100]))
                
                response_headers = {
                    'User-Agent': utils.USER_AGENT,
                    'Referer': url
                }
                
                return (video_url, 'HD', response_headers)
            
            # Pattern 2: Packed JavaScript
            packed_match = re.search(r'(eval\(function\(p,a,c,k,e(?:.|\s)+?\))</script>', html, re.DOTALL)
            if packed_match:
                utils.kodilog('Streamwish Resolver: Unpacking JavaScript...')
                try:
                    packer = cPacker()
                    packed_code = packed_match.group(1)
                    unpacked = packer.unpack(packed_code)
                    utils.kodilog('Streamwish Resolver: Successfully unpacked ({} bytes)'.format(len(unpacked)))
                    
                    # Try wurl pattern
                    match = re.search(r'wurl\s*=\s*["\']([^"\']+)["\']', unpacked)
                    if match:
                        video_url = match.group(1)
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        utils.kodilog('Streamwish Resolver: Found wurl: {}'.format(video_url[:100]))
                        
                        response_headers = {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': url
                        }
                        
                        return (video_url, 'HD', response_headers)
                    
                    # Try file pattern
                    match = re.search(r'file:\s*["\']([^"\']+)["\']', unpacked)
                    if match:
                        video_url = match.group(1)
                        utils.kodilog('Streamwish Resolver: Found file in unpacked: {}'.format(video_url[:100]))
                        
                        response_headers = {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': url
                        }
                        
                        return (video_url, 'HD', response_headers)
                    
                except Exception as e:
                    utils.kodilog('Streamwish Resolver: Failed to unpack - {}'.format(str(e)))
            
            utils.kodilog('Streamwish Resolver: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('Streamwish Resolver: Error - {}'.format(str(e)))
            return None
