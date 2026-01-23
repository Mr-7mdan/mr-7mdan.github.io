# -*- coding: utf-8 -*-
"""
SaveFiles.com Hoster Resolver
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver


class SaveFilesResolver(HosterResolver):
    def __init__(self):
        self.name = "SaveFiles"
        self.domains = ['savefiles.com']
    
    def resolve(self, url):
        """
        Resolve SaveFiles embed URL to video stream
        
        Args:
            url: SaveFiles embed URL (e.g., https://savefiles.com/e/xxxxx)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('SaveFiles: Resolving {}'.format(url[:100]))
            
            # Extract file code from URL
            file_code_match = re.search(r'/e/([a-zA-Z0-9]+)', url)
            if not file_code_match:
                utils.kodilog('SaveFiles: Could not extract file code')
                return None
            
            file_code = file_code_match.group(1)
            utils.kodilog('SaveFiles: File code: {}'.format(file_code))
            
            # Submit POST form to get video page
            post_url = 'https://savefiles.com/dl'
            post_data = {
                'op': 'embed',
                'file_code': file_code,
                'auto': '1',
                'referer': 'https://a.asd.homes/'
            }
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Origin': 'https://savefiles.com',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            html = utils.postHtml(post_url, post_data, headers)
            utils.kodilog('SaveFiles: Received {} bytes of HTML'.format(len(html)))
            
            # Extract video source from JWPlayer sources
            # Pattern: sources: [{file:"https://...m3u8?..."}]
            source_match = re.search(r'sources:\s*\[\s*\{\s*file\s*:\s*"([^"]+)"', html)
            
            if not source_match:
                utils.kodilog('SaveFiles: No video source found')
                return None
            
            video_url = source_match.group(1)
            utils.kodilog('SaveFiles: Found video URL: {}'.format(video_url[:100]))
            
            # Detect quality from URL or default to HD
            quality = 'HD'
            if '720' in video_url or '720p' in html:
                quality = '720p'
            elif '1080' in video_url or '1080p' in html:
                quality = '1080p'
            elif '480' in video_url or '480p' in html:
                quality = '480p'
            
            # Headers for playback
            playback_headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': 'https://savefiles.com/',
                'Origin': 'https://savefiles.com'
            }
            
            return (video_url, quality, playback_headers)
            
        except Exception as e:
            utils.kodilog('SaveFiles: Error resolving - {}'.format(str(e)))
            return None
