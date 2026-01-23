# -*- coding: utf-8 -*-
"""
Generic Hoster Resolver Framework
Resolves video URLs from various hosting services
"""

import re
import os
import importlib
from resources.lib import utils
from resources.lib.basics import addon
from resources.lib.hoster_tracker import get_tracker

class HosterResolver:
    """Base class for hoster resolvers"""
    
    def __init__(self):
        self.name = "Generic"
        self.domains = []
    
    def can_resolve(self, url):
        """Check if this resolver can handle the given URL"""
        return any(domain in url for domain in self.domains)
    
    def resolve(self, url):
        """
        Resolve the hoster URL to a direct playable URL
        Returns: (video_url, quality) tuple or (video_url, quality, headers) tuple or None if failed
        """
        return None

class HosterManager:
    """Manages all hoster resolvers"""
    
    def __init__(self):
        self.resolvers = []
        self._init_resolvers()
    
    def _init_resolvers(self):
        """Initialize all available resolvers by auto-loading from hosters/ directory"""
        try:
            # Get the hosters directory path
            hosters_dir = os.path.join(os.path.dirname(__file__), 'hosters')
            
            if not os.path.exists(hosters_dir):
                utils.kodilog('HosterManager: hosters/ directory not found')
                return
            
            # Get all .py files in hosters directory (excluding __init__.py)
            hoster_files = [f[:-3] for f in os.listdir(hosters_dir) 
                           if f.endswith('.py') and f != '__init__.py']
            
            utils.kodilog('HosterManager: Found {} hoster modules'.format(len(hoster_files)))
            
            # Import each hoster module and instantiate its resolver
            for hoster_name in hoster_files:
                try:
                    # Import the module
                    module = importlib.import_module('resources.lib.hosters.{}'.format(hoster_name))
                    
                    # Find the resolver class (should match pattern: XxxResolver)
                    resolver_class = None
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if (isinstance(attr, type) and 
                            attr_name.endswith('Resolver') and 
                            attr_name != 'HosterResolver'):
                            resolver_class = attr
                            break
                    
                    if resolver_class:
                        resolver = resolver_class()
                        self.resolvers.append(resolver)
                        utils.kodilog('HosterManager: Loaded {} from {}'.format(
                            resolver.name, hoster_name))
                    else:
                        utils.kodilog('HosterManager: No resolver class found in {}'.format(hoster_name))
                        
                except Exception as e:
                    utils.kodilog('HosterManager: Error loading {} - {}'.format(hoster_name, str(e)))
            
            utils.kodilog('HosterManager: Loaded {} resolvers total'.format(len(self.resolvers)))
            
        except Exception as e:
            utils.kodilog('HosterManager: Error initializing resolvers - {}'.format(str(e)))
    
    def get_resolver(self, url):
        """Find appropriate resolver for URL"""
        for resolver in self.resolvers:
            if resolver.can_resolve(url):
                return resolver
        return None
    
    def has_resolver(self, url):
        """
        Check if any resolver (custom or ResolveURL) can handle this URL
        
        Args:
            url: The URL to check
            
        Returns:
            True if resolvable, False otherwise
        """
        # Check custom resolvers
        if self.get_resolver(url):
            return True
        
        # Check ResolveURL if enabled
        enable_resolveurl = addon.getSetting('enable_resolveurl') == 'true'
        if enable_resolveurl:
            try:
                import resolveurl
                from resolveurl import HostedMediaFile
                hmf = HostedMediaFile(url=url)
                return bool(hmf)
            except:
                pass
        
        return False
    
    def is_trusted_hoster(self, url):
        """Check if URL is from a trusted hoster"""
        tracker = get_tracker()
        return tracker.is_trusted(url)
    
    def resolve(self, url, referer=None, max_depth=3):
        """
        Resolve a hoster URL to playable video URL (supports chained resolution)
        
        Args:
            url: The hoster URL to resolve
            referer: Optional referer header
            max_depth: Maximum recursion depth for chained resolvers
            
        Returns:
            dict with 'url', 'quality', 'headers' or None if failed
        """
        utils.kodilog('HosterResolver: Attempting to resolve: {}'.format(url[:100]))
        tracker = get_tracker()
        
        # Check if URL is already a direct video file - skip resolution
        import re
        if re.search(r'\.(m3u8|mp4|avi|mkv|flv|ts)(\?|$)', url, re.IGNORECASE):
            utils.kodilog('HosterResolver: Found direct video URL')
            # Add verifypeer=false for HTTPS URLs to bypass SSL certificate checks
            final_url = url
            if url.startswith('https://'):
                separator = '&' if '?' in url else '|'
                final_url = url + separator + 'verifypeer=false'
            return {
                'url': final_url,
                'quality': 'Unknown',
                'headers': {}
            }
        
        current_url = url
        quality = 'Unknown'
        
        # Try to resolve up to max_depth times (for chained resolvers like play.php → reviewrate.net → video.mp4)
        headers = {}
        last_resolver_name = None
        for depth in range(max_depth):
            resolver = self.get_resolver(current_url)
            
            # If no specific resolver found, try generic resolver as fallback
            if not resolver:
                utils.kodilog('HosterResolver: No specific resolver found at depth {}'.format(depth))
                # Look for generic resolver
                generic_resolver = None
                for r in self.resolvers:
                    if r.name == 'Generic':
                        generic_resolver = r
                        break
                
                if generic_resolver:
                    utils.kodilog('HosterResolver: Trying Generic resolver as fallback')
                    resolver = generic_resolver
                else:
                    utils.kodilog('HosterResolver: No Generic resolver available')
                    break
            
            if resolver:
                # Prevent same resolver from running twice in a row (e.g., Streamtape resolving its own output)
                if last_resolver_name and resolver.name == last_resolver_name:
                    utils.kodilog('HosterResolver: Same resolver ({}) would run twice, stopping'.format(resolver.name))
                    break
                
                utils.kodilog('HosterResolver: Using resolver: {} (depth {})'.format(resolver.name, depth))
                last_resolver_name = resolver.name
                result = resolver.resolve(current_url)
                
                if result:
                    # Handle both 2-tuple and 3-tuple returns
                    if len(result) == 3:
                        resolved_url, resolved_quality, resolved_headers = result
                        # Merge headers (later resolvers override earlier ones)
                        headers.update(resolved_headers)
                    else:
                        resolved_url, resolved_quality = result
                    
                    # Update quality if not Unknown
                    if resolved_quality != 'Unknown':
                        quality = resolved_quality
                    
                    # If resolved URL is same as input, we're done
                    if resolved_url == current_url:
                        break
                    
                    current_url = resolved_url
                    utils.kodilog('HosterResolver: Resolved to: {}'.format(current_url[:100]))
                    
                    # If it's a direct video URL, we're done (check with regex to handle query params)
                    import re
                    if re.search(r'\.(m3u8|mp4|avi|mkv|flv|ts|mpd)(\?|$)', current_url, re.IGNORECASE):
                        utils.kodilog('HosterResolver: Found direct video URL')
                        break
                else:
                    # Resolver failed
                    break
            else:
                # This should not happen after generic fallback logic above
                break
        
        # Check if we got a valid result from custom resolvers
        custom_resolved = current_url != url or current_url.endswith(('.mp4', '.m3u8', '.mpd'))
        
        if custom_resolved:
            tracker.record_success(url)
            return {
                'url': current_url,
                'quality': quality,
                'headers': headers
            }
        
        # Try ResolveURL as fallback based on priority setting
        enable_resolveurl = addon.getSetting('enable_resolveurl') == 'true'
        resolver_priority = int(addon.getSetting('resolver_priority') or '0')
        
        # 0=Custom First, 1=ResolveURL First, 2=Custom Only, 3=ResolveURL Only
        use_resolveurl_fallback = enable_resolveurl and resolver_priority in [0, 1, 3]
        
        if use_resolveurl_fallback and not custom_resolved:
            utils.kodilog('HosterResolver: Trying ResolveURL fallback')
            try:
                import resolveurl
                video_url = resolveurl.resolve(url)
                if video_url and video_url != url:
                    utils.kodilog('HosterResolver: ResolveURL resolved to: {}'.format(video_url[:100]))
                    tracker.record_success(url)
                    return {
                        'url': video_url,
                        'quality': 'Unknown',
                        'headers': {}
                    }
            except Exception as e:
                utils.kodilog('HosterResolver: ResolveURL failed - {}'.format(str(e)))
        
        utils.kodilog('HosterResolver: Failed to resolve URL')
        tracker.record_failure(url)
        return None

# Common hoster extraction patterns
def extract_iframe_sources(html):
    """Extract iframe sources from HTML"""
    iframes = []
    # Pattern 1: Standard iframe
    pattern1 = r'<iframe[^>]+src=["\']([^"\']+)["\']'
    iframes.extend(re.findall(pattern1, html))
    
    # Pattern 2: Data attributes
    pattern2 = r'data-src=["\']([^"\']+)["\']'
    iframes.extend(re.findall(pattern2, html))
    
    return iframes

def extract_video_sources(html):
    """Extract video source URLs from HTML"""
    sources = []
    # Pattern 1: video source tags
    pattern1 = r'<source[^>]+src=["\']([^"\']+)["\']'
    sources.extend(re.findall(pattern1, html))
    
    # Pattern 2: Direct video URLs
    pattern2 = r'["\']([^"\']*\.(?:mp4|m3u8|mpd)[^"\']*)["\']'
    sources.extend(re.findall(pattern2, html))
    
    return sources

def extract_embed_urls(html):
    """Extract embed URLs from HTML"""
    embeds = []
    # Common embed patterns
    patterns = [
        r'(?:embed|player|watch)\?.*?url=([^&"\'\s]+)',
        r'embed/([^/"\'\s]+)',
    ]
    
    for pattern in patterns:
        embeds.extend(re.findall(pattern, html))
    
    return embeds

# Global instance
_hoster_manager = None

def get_hoster_manager():
    """Get singleton hoster manager instance"""
    global _hoster_manager
    if _hoster_manager is None:
        _hoster_manager = HosterManager()
    return _hoster_manager

def reload_resolvers():
    """Reload all resolvers (useful for development)"""
    global _hoster_manager
    _hoster_manager = None
    return get_hoster_manager()
