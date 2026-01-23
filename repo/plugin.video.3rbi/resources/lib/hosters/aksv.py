# -*- coding: utf-8 -*-
"""
AKSV (ak.sv) Hoster Resolver
Resolves go.ak.sv/watch/* URLs to direct video streams
"""

import re
from resources.lib import utils
from resources.lib.hoster_resolver import HosterResolver


class AKSVResolver(HosterResolver):
    def __init__(self):
        self.name = "AKSV"
        self.domains = ['go.ak.sv', 'ak.sv']
    
    def resolve(self, url):
        """
        Resolve AKSV watch URL to direct video stream
        
        Args:
            url: AKSV watch URL (e.g., http://go.ak.sv/watch/XXXX)
            
        Returns:
            (video_url, quality, headers) tuple or None if failed
        """
        try:
            utils.kodilog('AKSV Resolver: Resolving {}'.format(url[:100]))
            
            # Fetch the go.ak.sv/watch page
            html = utils.getHtml(url)
            
            # Find redirect to actual watch page
            # Example: href="https://ak.sv/watch/170172/10704/the-confession"
            final_link_match = re.search(r'href="(https?://ak\.sv/watch/[^"]+)"', html)
            
            if final_link_match:
                final_url = final_link_match.group(1)
                utils.kodilog('AKSV Resolver: Following redirect to: {}'.format(final_url[:100]))
                final_html = utils.getHtml(final_url)
            else:
                # Already on final page
                final_html = html
            
            # Extract video sources from <source> tags
            # <source src="https://..." size="1080" type="video/mp4" />
            sources = re.findall(r'<source\s+src="([^"]+)"[^>]*size="([^"]+)"', final_html)
            
            if not sources:
                # Fallback without size attribute
                sources_urls = re.findall(r'<source\s+src="([^"]+)"', final_html)
                sources = [(s, 'Unknown') for s in sources_urls]
            
            if not sources:
                utils.kodilog('AKSV Resolver: No video sources found')
                return None
            
            # Sort by quality (descending) and pick best
            def quality_sort_key(item):
                try:
                    return int(item[1]) if item[1].isdigit() else 0
                except:
                    return 0
            
            sources.sort(key=quality_sort_key, reverse=True)
            stream_url, size = sources[0]
            
            utils.kodilog('AKSV Resolver: Found video URL: {}'.format(stream_url[:100]))
            
            # Encode spaces and special characters
            from six.moves.urllib_parse import quote
            stream_url = quote(stream_url, safe=':/?&=+')
            
            # Determine quality from size
            quality = '{}p'.format(size) if size and size.isdigit() else 'HD'
            
            # AKSV requires User-Agent and SSL verification bypass
            headers = {
                'User-Agent': utils.USER_AGENT,
                'verifypeer': 'false'  # Bypass SSL cert verification
            }
            
            return (stream_url, quality, headers)
            
        except Exception as e:
            utils.kodilog('AKSV Resolver: Error resolving - {}'.format(str(e)))
            return None
