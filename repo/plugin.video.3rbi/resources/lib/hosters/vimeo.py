# -*- coding: utf-8 -*-
# Based on vStream vimeo resolver (simplified)

import re
import json
from resources.lib import utils

class VimeoResolver:
    """Resolver for vimeo.com video hosting"""
    
    def __init__(self):
        self.name = 'Vimeo'
        self.domains = ['vimeo.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vimeo URL to direct video link via config API
        
        Args:
            url: Vimeo embed URL (may include |Referer=...)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Vimeo Resolver: Attempting {}'.format(url[:100]))
            
            # Extract Referer if provided
            if '|Referer=' in url:
                parts = url.split('|Referer=')
                clean_url = parts[0]
                referer = parts[1]
            else:
                clean_url = url
                referer = 'https://vimeo.com/'
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 13_3 like Mac OS X) AppleWebKit/605.1.15',
                'Referer': referer,
                'Host': 'vimeo.com'
            }
            
            # Fetch embed page
            html = utils.getHtml(clean_url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Vimeo Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Vimeo Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Extract config URL: "config":"..."
            match = re.search(r'"config":\s*"([^"]+)"', html)
            if not match:
                utils.kodilog('Vimeo Resolver: No config URL found')
                return None
            
            config_url = match.group(1)
            utils.kodilog('Vimeo Resolver: Config URL: {}'.format(config_url[:80]))
            
            # Fetch config JSON
            config_headers = {
                'User-Agent': headers['User-Agent'],
                'Referer': 'https://vimeo.com/'
            }
            
            config_response = utils.getHtml(config_url, headers=config_headers)
            if not config_response:
                utils.kodilog('Vimeo Resolver: No config response')
                return None
            
            # Extract video URLs: "origin":"...","url":"..."
            matches = re.findall(r'"origin":\s*"([^"]+)"\s*,\s*"url":\s*"([^"]+)"', config_response)
            if not matches:
                utils.kodilog('Vimeo Resolver: No video URLs in config')
                return None
            
            # Get highest quality (last in list typically)
            origin, video_url = matches[-1]
            utils.kodilog('Vimeo Resolver: Found video URL: {} ({})'.format(video_url[:100], origin))
            
            # Return with headers
            response_headers = {
                'User-Agent': headers['User-Agent'],
                'Referer': 'https://vimeo.com/'
            }
            
            return (video_url, origin, response_headers)
            
        except Exception as e:
            utils.kodilog('Vimeo Resolver: Error - {}'.format(str(e)))
            return None
