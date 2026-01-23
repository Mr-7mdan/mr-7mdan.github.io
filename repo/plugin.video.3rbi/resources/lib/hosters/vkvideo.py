# -*- coding: utf-8 -*-
"""
VKVideo Resolver
Extracts video URLs from vkvideo.ru embed pages
"""

import re
import json
from resources.lib import utils

class VKVideoResolver:
    """Resolver for vkvideo.ru hosting"""
    
    def __init__(self):
        self.name = "VKVideo"
        self.domains = ['vkvideo.ru', 'vk.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vkvideo.ru URL to direct video link
        
        Args:
            url: VKVideo embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('VKVideo Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            if not html:
                utils.kodilog('VKVideo Resolver: No HTML response')
                return None
            
            # Extract files object with quality variants
            # Pattern: "files":{"mp4_240":"URL","mp4_360":"URL",...}
            files_match = re.search(r'"files"\s*:\s*({[^}]+})', html)
            if not files_match:
                utils.kodilog('VKVideo Resolver: No files object found')
                return None
            
            files_json = files_match.group(1)
            
            try:
                files = json.loads(files_json)
            except:
                utils.kodilog('VKVideo Resolver: Failed to parse files JSON')
                return None
            
            # Quality priority order
            quality_order = ['mp4_1080', 'mp4_720', 'mp4_480', 'mp4_360', 'mp4_240']
            
            video_url = None
            quality = 'HD'
            
            for q in quality_order:
                if q in files and files[q]:
                    video_url = files[q]
                    quality = q.replace('mp4_', '') + 'p'
                    break
            
            if not video_url:
                utils.kodilog('VKVideo Resolver: No video URL found in files')
                return None
            
            utils.kodilog('VKVideo Resolver: Found video URL: {} ({})'.format(video_url[:100], quality))
            
            return (video_url, quality, headers)
            
        except Exception as e:
            utils.kodilog('VKVideo Resolver: Error - {}'.format(str(e)))
            return None
