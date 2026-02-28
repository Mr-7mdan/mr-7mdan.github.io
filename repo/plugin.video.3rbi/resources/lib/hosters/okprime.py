# -*- coding: utf-8 -*-
"""
OKPrime Hoster Resolver
Resolves videos from okprime.site and related domains
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver

class OkprimeResolver(HosterResolver):
    """Resolver for okprime.site streaming service"""
    
    def __init__(self):
        self.name = 'OKPrime'
        self.domains = ['okprime.site', 'qq.okprime.site', 'okprimeone.site']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve okprime URL to direct video link
        
        Args:
            url: OKPrime embed URL (e.g., https://qq.okprime.site/embed-xxx.html)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('OKPrime Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            html = utils.getHtml(url, headers=headers)
            
            if not html or not isinstance(html, str):
                utils.kodilog('OKPrime Resolver: Invalid HTML response')
                return None
            
            utils.kodilog('OKPrime Resolver: Received {} bytes'.format(len(html)))
            
            # Extract file_id from cookie setting
            file_id_match = re.search(r"\$\.cookie\('file_id',\s*'(\d+)'", html)
            if not file_id_match:
                # Try alternative pattern
                file_id_match = re.search(r"file_id['\"]?\s*[:=]\s*['\"]?(\d+)", html)
            
            # Extract file_code from embed URL
            file_code_match = re.search(r'embed-([a-zA-Z0-9]+)\.html', url)
            
            if file_id_match:
                file_id = file_id_match.group(1)
                utils.kodilog('OKPrime Resolver: Found file_id={}'.format(file_id))
                
                # Try to get download page
                download_url = 'https://okprime.site/dl?file_id={}'.format(file_id)
                if file_code_match:
                    download_url += '&file_code={}'.format(file_code_match.group(1))
                
                utils.kodilog('OKPrime Resolver: Trying download URL: {}'.format(download_url))
                
                dl_html = utils.getHtml(download_url, headers=headers)
                if dl_html:
                    # Look for direct video URL in download page
                    video_match = re.search(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)(?:\?[^\s"\'<>]*)?', dl_html, re.IGNORECASE)
                    if video_match:
                        video_url = video_match.group(0)
                        utils.kodilog('OKPrime Resolver: Found video URL: {}'.format(video_url[:100]))
                        
                        return (video_url, 'HD', {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': download_url
                        })
                    
                    # Look for download button with video link
                    dl_link_match = re.search(r'href=["\']([^"\']*(?:\.mp4|\.mkv|\.avi)[^"\']*)["\']', dl_html, re.IGNORECASE)
                    if dl_link_match:
                        video_url = dl_link_match.group(1)
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        utils.kodilog('OKPrime Resolver: Found download link: {}'.format(video_url[:100]))
                        
                        return (video_url, 'HD', {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': download_url
                        })
            
            # Try to find video URL directly in embed page
            video_match = re.search(r'file:\s*["\']([^"\']+\.(?:mp4|m3u8)[^"\']*)["\']', html, re.IGNORECASE)
            if video_match:
                video_url = video_match.group(1)
                utils.kodilog('OKPrime Resolver: Found file property: {}'.format(video_url[:100]))
                
                return (video_url, 'HD', headers)
            
            # Try JWPlayer sources
            sources_match = re.search(r'sources:\s*\[\s*\{\s*file:\s*["\']([^"\']+)["\']', html, re.IGNORECASE)
            if sources_match:
                video_url = sources_match.group(1)
                utils.kodilog('OKPrime Resolver: Found JWPlayer source: {}'.format(video_url[:100]))
                
                return (video_url, 'HD', headers)
            
            # Try generic video URL pattern
            video_match = re.search(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)(?:\?[^\s"\'<>]*)?', html, re.IGNORECASE)
            if video_match:
                video_url = video_match.group(0)
                utils.kodilog('OKPrime Resolver: Found generic video URL: {}'.format(video_url[:100]))
                
                return (video_url, 'HD', headers)
            
            utils.kodilog('OKPrime Resolver: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('OKPrime Resolver: Error - {}'.format(str(e)))
            return None
