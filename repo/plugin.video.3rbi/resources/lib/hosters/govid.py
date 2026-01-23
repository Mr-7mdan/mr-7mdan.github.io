# -*- coding: utf-8 -*-
# Based on vStream govid resolver (CimaClub)

import re
from resources.lib import utils

class GovidResolver:
    """Resolver for govid/CimaClub hosting sites"""
    
    def __init__(self):
        self.name = 'Govid'
        self.domains = ['govid.co', 'go.telvod.site']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve govid URL to direct video link
        
        Args:
            url: Govid embed URL (may include |Referer=...)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Govid Resolver: Attempting {}'.format(url[:100]))
            
            # Extract Referer if provided
            if '|Referer=' in url:
                parts = url.split('|Referer=')
                clean_url = parts[0]
                referer = parts[1]
            else:
                clean_url = url
                referer = url
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer
            }
            
            html = utils.getHtml(clean_url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('Govid Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('Govid Resolver: Received {} bytes of HTML'.format(len(html)))
            
            # Pattern 1: Extract playbackUrl API endpoint
            match = re.search(r'"playbackUrl":\s*"([^"]+)"', html)
            if match:
                api_url = match.group(1).replace('hhttps', 'https').replace('api.govid.co/api', 'go.telvod.site/api')
                utils.kodilog('Govid Resolver: Found playbackUrl: {}'.format(api_url[:80]))
                
                # Fetch m3u8 playlist
                playlist = utils.getHtml(api_url, headers=headers)
                if playlist:
                    # Extract quality variants: ,NAME="...",<URL>
                    matches = re.findall(r',NAME="([^"]+)"[^\n]+\n(https[^\n]+\.m3u8)', playlist)
                    if matches:
                        # Get highest quality (last in list)
                        quality, video_url = matches[-1]
                        utils.kodilog('Govid Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
                        
                        response_headers = {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': clean_url
                        }
                        
                        return (video_url, quality, response_headers)
            
            # Pattern 2: Direct link in anchor tag
            match = re.search(r'<a target="_blank"[^>]+href="([^"]+)"', html)
            if match:
                video_url = match.group(1)
                utils.kodilog('Govid Resolver: Found direct link: {}'.format(video_url[:100]))
                
                response_headers = {
                    'User-Agent': utils.USER_AGENT,
                    'Referer': clean_url
                }
                
                return (video_url, 'HD', response_headers)
            
            # Pattern 3: file:"...",label pattern
            match = re.search(r'file:\s*"([^"]+)"\s*,\s*label', html)
            if match:
                video_url = match.group(1).replace('["', '').replace('"]', '')
                utils.kodilog('Govid Resolver: Found file URL: {}'.format(video_url[:100]))
                
                response_headers = {
                    'User-Agent': utils.USER_AGENT,
                    'Referer': clean_url
                }
                
                return (video_url, 'HD', response_headers)
            
            # Pattern 4: sources: [...] pattern
            match = re.search(r'sources:\s*([^\,]+)', html)
            if match:
                video_url = match.group(1).replace('["', '').replace('"]', '')
                utils.kodilog('Govid Resolver: Found sources URL: {}'.format(video_url[:100]))
                
                response_headers = {
                    'User-Agent': utils.USER_AGENT,
                    'Referer': clean_url
                }
                
                return (video_url, 'HD', response_headers)
            
            utils.kodilog('Govid Resolver: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('Govid Resolver: Error - {}'.format(str(e)))
            return None
