# -*- coding: utf-8 -*-
# Based on vStream vkplay resolver

import re
from resources.lib import utils

class VkplayResolver:
    """Resolver for vkplay.live streaming service"""
    
    def __init__(self):
        self.name = 'VKPlay'
        self.domains = ['vkplay.live']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vkplay.live URL to direct video link via API
        
        Args:
            url: VKPlay embed URL (may include |Referer=...)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('VKPlay Resolver: Attempting {}'.format(url[:100]))
            
            # Extract Referer if provided
            if '|Referer=' in url:
                parts = url.split('|Referer=')
                clean_url = parts[0]
                referer = parts[1]
            else:
                clean_url = url
                referer = url
            
            # Extract stream ID from embed URL
            if '/embed/' not in clean_url:
                utils.kodilog('VKPlay Resolver: Not an embed URL')
                return None
            
            stream_id = clean_url.split('/embed/')[-1].split('?')[0].strip('/')
            
            # Build API URL
            api_url = 'https://api.vkplay.live/v1/blog/{}/public_video_stream'.format(stream_id)
            utils.kodilog('VKPlay Resolver: API URL: {}'.format(api_url))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer
            }
            
            # Fetch API response
            response = utils.getHtml(api_url, headers=headers)
            if not response:
                utils.kodilog('VKPlay Resolver: No API response')
                return None
            
            utils.kodilog('VKPlay Resolver: Received {} bytes from API'.format(len(response)))
            
            # Extract video URL: "url":"..."
            matches = re.findall(r'"url":\s*"([^"]+)"', response)
            if not matches:
                utils.kodilog('VKPlay Resolver: No URLs found in API response')
                return None
            
            # Filter for valid m3u8 HLS URLs
            video_url = None
            for url_candidate in matches:
                if 'm3u8' in url_candidate and 'hls' in url_candidate and url_candidate.startswith('http'):
                    video_url = url_candidate
                    break
            
            if not video_url:
                utils.kodilog('VKPlay Resolver: No valid HLS URL found')
                return None
            
            utils.kodilog('VKPlay Resolver: Found video URL: {}'.format(video_url[:100]))
            
            # Return with headers
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': referer
            }
            
            return (video_url, 'HD', response_headers)
            
        except Exception as e:
            utils.kodilog('VKPlay Resolver: Error - {}'.format(str(e)))
            return None
