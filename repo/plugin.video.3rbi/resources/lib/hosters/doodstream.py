# -*- coding: utf-8 -*-
# Based on vStream dood resolver

import re
import random
import time
from resources.lib import utils

class DoodstreamResolver:
    """Resolver for doodstream/dood hosting sites"""
    
    def __init__(self):
        self.name = 'Doodstream'
        self.domains = ['doodstream.com', 'dood.la', 'dood.to', 'dood.watch', 'dood.pm', 'dood.wf', 'dood.cx']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve doodstream URL to direct video link
        
        Args:
            url: Doodstream embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Doodstream Resolver: Attempting {}'.format(url[:100]))
            
            # Convert /d/ to /e/ and normalize domain
            url = url.replace('/d/', '/e/').replace('doodstream.com', 'dood.la')
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Doodstream Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Doodstream Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Generate random string
            possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
            random_str = ''.join(random.choice(possible) for _ in range(10))
            
            # Extract token pattern: return a+"?token=..."
            token_match = re.search(r'return a\+"(\?token=[^"]+)"', html)
            if not token_match:
                utils.kodilog('Doodstream Resolver: No token pattern found')
                return None
            
            token_param = token_match.group(1)
            utils.kodilog('Doodstream Resolver: Found token parameter')
            
            # Build final URL component
            fin_url = random_str + token_param + str(int(1000 * time.time()))
            
            # Extract pass_md5 endpoint: $.get('/pass_md5...
            pass_match = re.search(r'\$\.get\(\'(\/pass_md5[^\']+)', html)
            if not pass_match:
                utils.kodilog('Doodstream Resolver: No pass_md5 endpoint found')
                return None
            
            pass_endpoint = pass_match.group(1)
            
            # Build pass_md5 URL
            domain = url.split('/')[2]
            pass_url = 'https://' + domain + pass_endpoint
            utils.kodilog('Doodstream Resolver: Fetching pass_md5 from: {}'.format(pass_url[:80]))
            
            # Request pass_md5
            pass_content = utils.getHtml(pass_url, headers=headers)
            if not pass_content:
                utils.kodilog('Doodstream Resolver: Failed to fetch pass_md5')
                return None
            
            # Build final video URL
            video_url = pass_content + fin_url
            utils.kodilog('Doodstream Resolver: Built video URL: {}'.format(video_url[:100]))
            
            # Return with headers (Referer required)
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('Doodstream Resolver: Error - {}'.format(str(e)))
            return None
