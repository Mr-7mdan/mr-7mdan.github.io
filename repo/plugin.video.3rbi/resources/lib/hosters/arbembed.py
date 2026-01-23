# -*- coding: utf-8 -*-
# arb-embed.com (Arab HD) resolver

import re
import json
from resources.lib import utils

class ArbEmbedResolver:
    """Resolver for arb-embed.com (Arab HD)"""
    
    def __init__(self):
        self.name = 'Arab HD'
        self.domains = ['arb-embed.com', 'arbembed.com', 'arab-embed.com']
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url.lower() for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve arb-embed URL to direct video link
        
        Args:
            url: arb-embed embed URL
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('Arab HD Resolver: Attempting {}'.format(url[:100]))
            
            headers = {
                'User-Agent': utils.USER_AGENT,
                'Referer': url,
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            }
            
            # Try to fetch the page
            html = utils.getHtml(url, headers=headers)
            
            # Debug: log response type and size
            utils.kodilog('Arab HD Resolver: Response type: {}'.format(type(html).__name__))
            if html:
                if isinstance(html, str):
                    utils.kodilog('Arab HD Resolver: String length: {}'.format(len(html)))
                    utils.kodilog('Arab HD Resolver: First 200 chars: {}'.format(html[:200]))
                elif isinstance(html, (list, dict)):
                    utils.kodilog('Arab HD Resolver: JSON type received: {}'.format(type(html).__name__))
            
            # Check if response is JSON (note: empty list is falsy, so check isinstance first)
            if isinstance(html, list):
                utils.kodilog('Arab HD Resolver: Received JSON array response')
                utils.kodilog('Arab HD Resolver: Array length: {}'.format(len(html)))
                
                # Sometimes arb-embed returns JSON array
                try:
                    # If it's a list with video info
                    if len(html) > 0:
                        utils.kodilog('Arab HD Resolver: First item type: {}'.format(type(html[0]).__name__))
                        utils.kodilog('Arab HD Resolver: First item: {}'.format(str(html[0])[:200]))
                        
                        item = html[0]
                        if isinstance(item, dict):
                            utils.kodilog('Arab HD Resolver: Dict keys: {}'.format(list(item.keys())))
                            if 'file' in item:
                                video_url = item['file']
                                quality = item.get('label', 'HD')
                                utils.kodilog('Arab HD Resolver: Found video in JSON: {}'.format(video_url[:100]))
                                
                                response_headers = {
                                    'User-Agent': utils.USER_AGENT,
                                    'Referer': url
                                }
                                return (video_url, quality, response_headers)
                            else:
                                utils.kodilog('Arab HD Resolver: No "file" key in dict')
                        else:
                            utils.kodilog('Arab HD Resolver: First item is not a dict')
                    else:
                        utils.kodilog('Arab HD Resolver: Empty array')
                except Exception as e:
                    utils.kodilog('Arab HD Resolver: Error parsing JSON - {}'.format(str(e)))
            
            elif html and isinstance(html, str):
                utils.kodilog('Arab HD Resolver: Received {} bytes of HTML'.format(len(html)))
                
                # Try to parse as JSON first (in case it's a JSON string)
                try:
                    data = json.loads(html)
                    if isinstance(data, list) and len(data) > 0:
                        item = data[0]
                        if 'file' in item:
                            video_url = item['file']
                            quality = item.get('label', 'HD')
                            utils.kodilog('Arab HD Resolver: Found video in JSON string: {}'.format(video_url[:100]))
                            
                            response_headers = {
                                'User-Agent': utils.USER_AGENT,
                                'Referer': url
                            }
                            return (video_url, quality, response_headers)
                except:
                    pass  # Not JSON, continue with HTML parsing
                
                # Look for video sources in HTML
                patterns = [
                    r'file:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                    r'file:\s*["\']([^"\']+\.mp4[^"\']*)["\']',
                    r'"file":\s*"([^"]+)"',
                    r'sources:\s*\[.*?"file":\s*"([^"]+)"',
                    r'src:\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
                    if match:
                        video_url = match.group(1)
                        utils.kodilog('Arab HD Resolver: Found video URL: {}'.format(video_url[:100]))
                        
                        response_headers = {
                            'User-Agent': utils.USER_AGENT,
                            'Referer': url
                        }
                        return (video_url, 'HD', response_headers)
            
            utils.kodilog('Arab HD Resolver: No video URL found')
            return None
            
        except Exception as e:
            utils.kodilog('Arab HD Resolver: Error - {}'.format(str(e)))
            return None
