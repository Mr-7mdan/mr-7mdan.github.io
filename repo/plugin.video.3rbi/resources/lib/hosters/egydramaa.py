# -*- coding: utf-8 -*-
"""
EgyDramaa Resolver
URLs: t.egydramaa.life/watch58.html?series=NAME&episode=NUM
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver


class EgyDramaaResolver(HosterResolver):
    name = 'EgyDramaa'
    domains = ['egydramaa.life', 'egydramaa']
    
    def __init__(self):
        super().__init__()
        self.patterns = [
            r'https?://(?:t|w)\.egydramaa\.life/watch\d+\.html\?series=([^&]+)&episode=(\d+)',
            r'https?://egydramaa\.life/watch\d+\.html\?series=([^&]+)&episode=(\d+)',
        ]
    
    def can_resolve(self, url):
        """Check if URL matches egydramaa pattern"""
        for pattern in self.patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
        return False
    
    def resolve(self, url):
        """Resolve egydramaa URL to direct video link"""
        utils.kodilog(f'{self.name}: Resolving {url}')
        
        # Extract series name and episode from URL
        for pattern in self.patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                series_name = match.group(1)
                episode_num = match.group(2).zfill(2)  # Pad to 2 digits
                break
        else:
            utils.kodilog(f'{self.name}: Could not parse URL')
            return None
        
        utils.kodilog(f'{self.name}: Series={series_name}, Episode={episode_num}')
        
        # Fetch the page to get server URLs
        html = utils.getHtml(url, headers={'User-Agent': utils.USER_AGENT})
        
        if not html:
            utils.kodilog(f'{self.name}: Failed to fetch page')
            return None
        
        # Find server URLs with placeholders
        server_pattern = r'(https://[^\s"<>]+\{series\}[^\s"<>]*)'
        servers = re.findall(server_pattern, html)
        
        if not servers:
            utils.kodilog(f'{self.name}: No server URLs found')
            return None
        
        utils.kodilog(f'{self.name}: Found {len(servers)} servers')
        
        # Try each server until one works
        for server_url in servers:
            # Clean up URL (remove trailing backticks, quotes)
            server_url = server_url.rstrip('`\'"')
            
            # Replace placeholders with actual values
            video_url = server_url.replace('{series}', series_name).replace('{episode}', episode_num)
            
            utils.kodilog(f'{self.name}: Trying {video_url}')
            
            # Check if URL is accessible
            try:
                import urllib.request
                req = urllib.request.Request(video_url, method='HEAD')
                req.add_header('User-Agent', utils.USER_AGENT)
                req.add_header('Referer', url)
                response = urllib.request.urlopen(req, timeout=10)
                
                if response.status == 200:
                    utils.kodilog(f'{self.name}: Success! {video_url}')
                    return (video_url, 'HD')
            except Exception as e:
                utils.kodilog(f'{self.name}: Failed - {e}')
                continue
        
        utils.kodilog(f'{self.name}: All servers failed')
        return None


def get_resolver():
    return EgyDramaaResolver()
