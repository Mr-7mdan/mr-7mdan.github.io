# -*- coding: utf-8 -*-
"""
Streamtape Resolver
Extracts video URLs from streamtape.com embed pages
"""

import re
from resources.lib import utils

class StreamtapeResolver:
    """Resolver for streamtape.com"""
    
    def __init__(self):
        self.name = "Streamtape"
        self.domains = ['streamtape.com', 'streamtape.to', 'streamtape.net']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve streamtape.com embed URL to video URL
        
        Args:
            url: Streamtape embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page with headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://fajer.show/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            html = utils.getHtml(url, headers=headers)
            
            utils.kodilog('Streamtape: Received {} bytes of HTML'.format(len(html)))
            
            # Streamtape obfuscates URL in JavaScript
            # Pattern: document.getElementById('robotlink').innerHTML = '//streamtape.co'+ ('xcdm/get_video?...&token=XXX').substring(2).substring(1);
            # The final token is in the JavaScript string, not the initial robotlink div
            
            # Extract the JavaScript manipulation pattern for robotlink
            # Pattern: getElementById('robotlink').innerHTML = '//stream'+ ('xcdtape.com/get_video?...').substring(2).substring(1);
            # After substring ops: 'xcdtape.com/get_video' -> 'tape.com/get_video'
            # Combined with '//stream' prefix = '//streamtape.com/get_video'
            js_pattern = r"getElementById\s*\(\s*['\"]robotlink['\"]\s*\)\s*\.\s*innerHTML\s*=\s*['\"]([^'\"]+)['\"]\s*\+\s*\(['\"]([^'\"]+)['\"]\s*\)\s*\.substring\s*\(\s*2\s*\)\s*\.substring\s*\(\s*1\s*\)"
            js_match = re.search(js_pattern, html)
            
            if js_match:
                prefix = js_match.group(1)  # e.g., '//stream'
                obfuscated_url = js_match.group(2)  # e.g., 'xcdtape.com/get_video?...'
                utils.kodilog('Streamtape: Found prefix={}, obfuscated={}'.format(prefix, obfuscated_url[:50]))
                
                # Apply substring(2).substring(1) = skip first 3 characters
                # e.g., 'xcdtape.com/get_video?...' -> 'tape.com/get_video?...'
                deobfuscated = obfuscated_url[3:]
                video_url = 'https:' + prefix + deobfuscated
                utils.kodilog('Streamtape: Deobfuscated URL: {}'.format(video_url[:100]))
                
                # Add stream parameter
                if '?' in video_url:
                    video_url += '&stream=1'
                else:
                    video_url += '?stream=1'
                
                utils.kodilog('Streamtape: Final video URL: {}'.format(video_url[:100]))
                
                quality = 'HD'
                
                # Video requires headers
                playback_headers = {
                    'Referer': url,
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Origin': 'https://streamtape.com'
                }
                
                return (video_url, quality, playback_headers)
            
            utils.kodilog('Streamtape: No robotlink found')
            return None
            
        except Exception as e:
            utils.kodilog('Streamtape: Error resolving - {}'.format(str(e)))
            return None
