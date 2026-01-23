# -*- coding: utf-8 -*-
"""
OK.ru Resolver
Extracts video URLs from ok.ru embed pages
"""

import re
import json
from resources.lib import utils

class OKResolver:
    """Resolver for ok.ru (Odnoklassniki)"""
    
    def __init__(self):
        self.name = "OK.ru"
        self.domains = ['ok.ru']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve ok.ru embed URL to video URL
        
        Args:
            url: OK.ru embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            # Fetch embed page
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': url,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            html = utils.getHtml(url, headers=headers)
            
            if not html:
                return None
                
            utils.kodilog('OK.ru: Received {} bytes of HTML'.format(len(html)))
            
            # Log snippet to debug
            snippet_start = html.find('data-')
            if snippet_start != -1:
                utils.kodilog('OK.ru: Found data- at position {}, snippet: {}'.format(snippet_start, html[snippet_start:snippet_start+200]))
            
            # Extract data-options section - try multiple patterns
            # Pattern 1: data-options="..."
            delimiter = '"'
            start = html.find('data-options="')
            if start == -1:
                # Pattern 2: data-options='...'
                start = html.find("data-options='")
                delimiter = "'"
            if start == -1:
                # Pattern 3: data-options=&quot;...
                start = html.find('data-options=&quot;')
                delimiter = '&quot;'
            
            if start == -1:
                utils.kodilog('OK.ru: data-options not found in HTML')
                return None
            
            utils.kodilog('OK.ru: Found data-options at position {}, delimiter: {}'.format(start, delimiter))
            
            # Skip past the attribute name and opening delimiter
            start = html.find('=', start) + 1
            if delimiter == '&quot;':
                start += len('&quot;')
            else:
                start += 1  # Skip opening quote
            
            # Find closing delimiter
            if delimiter == '&quot;':
                end = html.find('&quot;', start)
            else:
                end = html.find(delimiter, start)
            
            if end == -1:
                utils.kodilog('OK.ru: Could not find end delimiter')
                return None
            
            options_html = html[start:end]
            
            # Decode HTML entities
            options_html = options_html.replace('&quot;', '"')
            options_html = options_html.replace('&amp;', '&')
            options_html = options_html.replace('&#39;', "'")
            
            try:
                options = json.loads(options_html)
                flashvars = options.get('flashvars', {})
                
                # Parse metadata (double-encoded JSON)
                metadata_str = flashvars.get('metadata', '{}')
                if isinstance(metadata_str, str):
                    metadata = json.loads(metadata_str)
                else:
                    metadata = metadata_str
                
                # Try HLS master playlist first (best quality)
                video_url = metadata.get('hlsMasterPlaylistUrl') or metadata.get('hlsManifestUrl')
                quality = 'HD'
                
                if not video_url:
                    # Try videos array with quality selection
                    videos = metadata.get('videos', [])
                    if videos:
                        # Quality priority order (OK.ru uses: mobile, lowest, low, sd, hd, full)
                        quality_order = ['full', 'hd', 'sd', 'low', 'lowest', 'mobile']
                        best_video = None
                        
                        for q in quality_order:
                            for v in videos:
                                if v.get('name') == q:
                                    best_video = v
                                    break
                            if best_video:
                                break
                        
                        if not best_video and videos:
                            best_video = videos[0]
                        
                        if best_video:
                            video_url = best_video.get('url')
                            quality = best_video.get('name', 'HD')
                
                if not video_url:
                    # Last resort: try ondemand URLs
                    video_url = metadata.get('ondemandHls') or metadata.get('ondemandDash')
                
                if video_url:
                    utils.kodilog('OK.ru: Found video URL: {} ({})'.format(video_url[:100], quality))
                    
                    playback_headers = {
                        'Referer': url,
                        'User-Agent': headers['User-Agent']
                    }
                    
                    return (video_url, quality, playback_headers)
                    
            except (json.JSONDecodeError, ValueError) as e:
                utils.kodilog('OK.ru: JSON parse error: {}'.format(str(e)))
            
            utils.kodilog('OK.ru: No video source found')
            return None
            
        except Exception as e:
            utils.kodilog('OK.ru: Error resolving - {}'.format(str(e)))
            return None
