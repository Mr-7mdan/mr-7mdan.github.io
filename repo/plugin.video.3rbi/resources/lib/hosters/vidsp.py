# -*- coding: utf-8 -*-
"""
VidSP Resolver
Extracts video URLs from vidsp.net pages
"""

import re
from resources.lib import utils

class VidspResolver:
    """Resolver for vidsp.net hosting"""
    
    def __init__(self):
        self.name = "VidSP"
        self.domains = ['vidsp.net']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve vidsp URL to direct video link
        
        Args:
            url: VidSP download or embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('VidSP Resolver: Attempting {}'.format(url[:100]))
            
            # Extract file ID from URL
            file_id_match = re.search(r'/(?:d|e)/([a-zA-Z0-9_-]+)', url)
            if not file_id_match:
                utils.kodilog('VidSP Resolver: Could not extract file ID')
                return None
            
            file_id = file_id_match.group(1)
            utils.kodilog('VidSP Resolver: File ID: {}'.format(file_id))
            
            # Try embed URL format first
            embed_url = 'https://v.vidsp.net/e/{}'.format(file_id)
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(embed_url, headers=headers)
            if not html:
                utils.kodilog('VidSP Resolver: No HTML response from embed URL')
                # Try original download page
                html = utils.getHtml(url, headers=headers)
                if not html:
                    return None
            
            # Method 1: Extract from player sources array
            sources_match = re.search(r'sources\s*:\s*\[\s*["\']([^"\']+)["\']', html)
            if sources_match:
                video_url = sources_match.group(1)
                utils.kodilog('VidSP Resolver: Found video URL from sources: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Method 2: Extract file: property
            file_match = re.search(r'file\s*:\s*["\']([^"\']+)', html)
            if file_match:
                video_url = file_match.group(1)
                utils.kodilog('VidSP Resolver: Found video URL from file: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Method 3: Extract direct .mp4 or .m3u8 URL
            direct_match = re.search(r'(https?://[^"\'<>\s]+\.(?:mp4|m3u8)[^"\'<>\s]*)', html)
            if direct_match:
                video_url = direct_match.group(1)
                utils.kodilog('VidSP Resolver: Found direct video URL: {}'.format(video_url[:100]))
                return (video_url, 'HD', headers)
            
            # Method 4: Try to extract original download link
            # Pattern: href="xxx_o" for original quality
            orig_link_match = re.search(r'href="([^"]+_o)"', html)
            if orig_link_match:
                orig_url = orig_link_match.group(1)
                if not orig_url.startswith('http'):
                    orig_url = 'https://v.vidsp.net' + orig_url
                
                utils.kodilog('VidSP Resolver: Found original download link, attempting POST')
                
                # Try POST request to get direct link
                post_data = {'op': 'download_orig'}
                post_html = utils.getHtml(orig_url, headers=headers, data=post_data)
                
                if post_html:
                    # Look for direct download link in response
                    download_match = re.search(r'href="(https?://[^"]+\.mp4[^"]*)"', post_html)
                    if download_match:
                        video_url = download_match.group(1)
                        utils.kodilog('VidSP Resolver: Found direct download URL: {}'.format(video_url[:100]))
                        return (video_url, 'HD', headers)
            
            utils.kodilog('VidSP Resolver: No video URL found')
            return None
            
        except Exception as e:
            utils.kodilog('VidSP Resolver: Error - {}'.format(str(e)))
            return None
