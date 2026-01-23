# -*- coding: utf-8 -*-
# Based on vStream fembed resolver

import re
from resources.lib import utils

class FembedResolver:
    """Resolver for fembed and related video hosting sites"""
    
    def __init__(self):
        self.name = 'Fembed'
        self.domains = ['fembed.com', 'diasfem.com', 'feurl.com', 'femax20.com', 'fem.tohds', 'fvs.io']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve fembed URL to direct video link
        
        Args:
            url: Fembed embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Fembed Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url
            }
            
            # Determine API base URL based on domain
            if 'fem.tohds' in url:
                api_base = 'https://feurl.com/api/source/'
            elif 'fembed' in url or 'femax20' in url:
                api_base = 'https://www.diasfem.com/api/source/'
            else:
                domain = url.split('/')[2]
                api_base = 'https://' + domain + '/api/source/'
            
            # Extract video ID from URL
            video_id = url.rsplit('/', 1)[-1].split('.')[0]
            if 'embed-' in video_id:
                video_id = video_id.replace('embed-', '')
            
            # Build API URL
            api_url = api_base + video_id
            utils.kodilog('Fembed Resolver: API URL: {}'.format(api_url))
            
            # Prepare POST data
            post_data = "r=''&d=" + url.split('/')[2]
            
            # Make API request
            import json
            try:
                # Use getHtml with POST simulation (if supported) or direct request
                response = utils.getHtml(api_url, headers=headers)
                if response:
                    data = json.loads(response)
                    if data and 'data' in data and len(data['data']) > 0:
                        # Get highest quality available
                        video_url = data['data'][-1]['file']
                        quality = data['data'][-1].get('label', 'HD')
                        utils.kodilog('Fembed Resolver: Found video URL: {}'.format(video_url[:100]))
                        
                        response_headers = {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': url
                        }
                        
                        return (video_url, quality, response_headers)
            except:
                pass
            
            # Fallback: Try direct HTML extraction
            html = utils.getHtml(url, headers=headers)
            if html and isinstance(html, str):
                match = re.search(r'var video_source\s*=\s*["\']([^"\']+)["\']', html)
                if match:
                    video_url = match.group(1)
                    utils.kodilog('Fembed Resolver: Found video_source: {}'.format(video_url[:100]))
                    
                    response_headers = {
                        'User-Agent': utils.USER_AGENT,
                        'Referer': url
                    }
                    
                    return (video_url, 'HD', response_headers)
            
            utils.kodilog('Fembed Resolver: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('Fembed Resolver: Error - {}'.format(str(e)))
            return None
