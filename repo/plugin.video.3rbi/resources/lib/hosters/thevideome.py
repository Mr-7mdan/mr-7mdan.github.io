# -*- coding: utf-8 -*-
# Based on vStream thevideo_me resolver

import re
import json
from resources.lib import utils

class ThevideoMeResolver:
    """Resolver for thevideo.me/vev.io hosting sites"""
    
    def __init__(self):
        self.name = 'TheVideoMe'
        self.domains = ['thevideo.me', 'vev.io', 'video.tt']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def _extract_video_id(self, url):
        """Extract video ID from various URL formats"""
        match = re.search(r'/(?:embed-)?(\w+)(?:-\d+x\d+)?(?:\.html)?$', url)
        if match:
            return match.group(1)
        return None
    
    def _extract_from_html(self, embed_url, video_id):
        """Fallback: Extract video URL directly from HTML page"""
        headers = {
            'User-Agent': utils.USER_AGENT,
            'Referer': embed_url
        }
        
        try:
            utils.kodilog('TheVideoMe Resolver: Trying HTML extraction')
            
            html = utils.getHtml(embed_url, headers=headers)
            if not html:
                utils.kodilog('TheVideoMe Resolver: No HTML response')
                return None
            
            # Try to find video sources in HTML
            # Pattern 1: sources: [{file:"URL"}]
            match = re.search(r'sources:\s*\[\s*{\s*file:\s*["\']([^"\']+)["\']', html)
            if match:
                video_url = match.group(1)
                utils.kodilog('TheVideoMe Resolver: Found video URL from HTML: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Pattern 2: file:"URL"
            match = re.search(r'file:\s*["\']([^"\']+\.mp4[^"\']*)["\']', html)
            if match:
                video_url = match.group(1)
                utils.kodilog('TheVideoMe Resolver: Found video URL from HTML (pattern 2): {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            utils.kodilog('TheVideoMe Resolver: No video found in HTML')
            return None
            
        except Exception as e:
            utils.kodilog('TheVideoMe Resolver: HTML extraction error - {}'.format(str(e)))
            return None
    
    def resolve(self, url):
        """
        Resolve thevideo.me URL to direct video link via vev.io API
        
        Args:
            url: TheVideo.me embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('TheVideoMe Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT
            }
            
            # Get video ID
            video_id = self._extract_video_id(url)
            if not video_id:
                utils.kodilog('TheVideoMe Resolver: Could not extract video ID')
                return None
            
            # Build vev.io embed URL
            if 'video.' in url:
                embed_url = 'http://thevideo.me/embed-' + video_id + '.html'
            else:
                embed_url = 'https://vev.io/embed/' + video_id
            
            utils.kodilog('TheVideoMe Resolver: Checking redirect from: {}'.format(embed_url[:80]))
            
            # Follow redirect to vev.io (if needed)
            # Most modern implementations will redirect automatically
            
            # Build API URL
            api_url = 'https://vev.io/api/serve/video/' + video_id
            utils.kodilog('TheVideoMe Resolver: Fetching from API: {}'.format(api_url))
            
            # Fetch JSON response with better headers
            api_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': embed_url,
                'Accept': 'application/json, text/javascript, */*; q=0.01',
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = utils.getHtml(api_url, headers=api_headers)
            if not response:
                utils.kodilog('TheVideoMe Resolver: No API response, trying HTML fallback')
                # Try HTML extraction as fallback
                return self._extract_from_html(embed_url, video_id)
            
            # Parse JSON
            try:
                data = json.loads(response)
            except:
                utils.kodilog('TheVideoMe Resolver: Invalid JSON response, trying HTML fallback')
                return self._extract_from_html(embed_url, video_id)
            
            if not data or 'qualities' not in data:
                utils.kodilog('TheVideoMe Resolver: No qualities in response, trying HTML fallback')
                return self._extract_from_html(embed_url, video_id)
            
            # Get highest quality available
            qualities = data['qualities']
            if not qualities:
                return None
            
            # Get highest quality (try common resolutions)
            for quality_key in ['1080', '720', '480', '360']:
                if quality_key in qualities:
                    video_url = qualities[quality_key]
                    utils.kodilog('TheVideoMe Resolver: Found video URL: {} ({}p)'.format(video_url[:100], quality_key))
                    
                    response_headers = {
                        'User-Agent': utils.USER_AGENT,
                        'Referer': embed_url
                    }
                    
                    return (video_url, quality_key + 'p', response_headers)
            
            # If no standard quality, get first available
            first_quality = list(qualities.keys())[0]
            video_url = qualities[first_quality]
            utils.kodilog('TheVideoMe Resolver: Found video URL: {} ({})'.format(video_url[:100], first_quality))
            
            response_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': embed_url
            }
            
            return (video_url, first_quality, response_headers)
            
        except Exception as e:
            utils.kodilog('TheVideoMe Resolver: Error - {}'.format(str(e)))
            return None
