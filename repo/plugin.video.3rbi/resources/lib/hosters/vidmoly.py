# -*- coding: utf-8 -*-
"""
VidMoly Resolver
Extracts m3u8 video URLs from vidmoly.net embed pages
"""

import re
from resources.lib import utils

class VidMolyResolver:
    """Resolver for vidmoly.net"""
    
    def __init__(self):
        self.name = "VidMoly"
        self.domains = ['vidmoly.net', 'vidmoly.to', 'vidmoly.me']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vidmoly.net embed URL to video URL
        
        Args:
            url: VidMoly embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page with headers (VidMoly blocks requests without proper headers)
            # Use dynamic referer based on URL source
            referer = 'https://fajer.show/' if 'vidmoly.to' in url else 'https://a.asd.homes/'
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': referer,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5'
            }
            html = utils.getHtml(url, headers=headers)
            
            # Debug: Check if we got HTML
            utils.kodilog('VidMoly: Received {} bytes of HTML'.format(len(html)))
            
            # Check for JavaScript redirect (VidMoly.to uses this)
            redirect_match = re.search(r"window\.location\.replace\(['\"]([^'\"]+)['\"]\)", html)
            if redirect_match:
                redirect_url = redirect_match.group(1)
                utils.kodilog('VidMoly: Following redirect to: {}'.format(redirect_url[:100]))
                html = utils.getHtml(redirect_url, headers=headers)
                utils.kodilog('VidMoly: After redirect received {} bytes of HTML'.format(len(html)))
            
            # VidMoly uses JWPlayer with sources defined in JavaScript
            # Pattern: sources: [{file:"https://...m3u8?..."}]
            # Use DOTALL to handle multiline matches
            source_match = re.search(r'sources:\s*\[\s*\{\s*file\s*:\s*"([^"]+)"', html, re.DOTALL)
            
            # Debug: Check if sources key exists
            if 'sources:' in html:
                utils.kodilog('VidMoly: Found "sources:" in HTML')
                # Find and log context around sources
                idx = html.index('sources:')
                context = html[idx:idx+200]
                utils.kodilog('VidMoly: Context around sources: {}'.format(context[:150]))
            else:
                utils.kodilog('VidMoly: "sources:" NOT found in HTML')
            
            if source_match:
                video_url = source_match.group(1)
                utils.kodilog('VidMoly: Found video URL: {}'.format(video_url[:100]))
                
                # Determine quality - look for HD marker or default
                quality = 'HD'
                if '1080' in html or '"1080"' in html:
                    quality = '1080p'
                elif '720' in html or '"720"' in html:
                    quality = '720p'
                
                # Video requires Referer and User-Agent headers
                headers = {
                    'Referer': url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://vidmoly.net'
                }
                
                return (video_url, quality, headers)
            
            utils.kodilog('VidMoly: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('VidMoly: Error resolving - {}'.format(str(e)))
            return None
