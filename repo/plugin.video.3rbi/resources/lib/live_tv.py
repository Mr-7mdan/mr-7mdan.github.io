# -*- coding: utf-8 -*-
"""
Live TV - IPTV streams from iptv-org/iptv
Parses Arabic M3U playlist for live channels
"""

import re
from resources.lib import utils
from resources.lib.basics import addon_image, addDownLink
from resources.lib.url_dispatcher import URL_Dispatcher

# Create URL dispatcher for live TV
url_dispatcher = URL_Dispatcher('live_tv')

# Arabic M3U playlist URL
ARABIC_M3U_URL = 'https://iptv-org.github.io/iptv/languages/ara.m3u'


def _fetch_m3u():
    """Fetch and parse M3U playlist (will be cached)"""
    try:
        utils.kodilog(f'LiveTV: Fetching M3U from {ARABIC_M3U_URL}')
        html = utils.getHtml(ARABIC_M3U_URL)
        return html
    except Exception as e:
        utils.kodilog(f'LiveTV: Error fetching M3U: {str(e)}')
        return ''


def fetch_m3u():
    """Fetch M3U with caching"""
    return utils.cache.cacheFunction(_fetch_m3u)


def parse_m3u(m3u_content):
    """Parse M3U playlist and extract channel information"""
    channels = []
    
    if not m3u_content:
        return channels
    
    # Split by #EXTINF entries
    lines = m3u_content.split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for #EXTINF lines
        if line.startswith('#EXTINF:'):
            # Extract channel info from EXTINF line
            # Format: #EXTINF:-1 tvg-id="..." tvg-logo="..." group-title="...",Channel Name
            
            # Extract tvg-logo
            logo_match = re.search(r'tvg-logo="([^"]+)"', line)
            logo = logo_match.group(1) if logo_match else ''
            
            # Extract group-title (category)
            group_match = re.search(r'group-title="([^"]+)"', line)
            category = group_match.group(1) if group_match else 'General'
            
            # Extract channel name (after last comma)
            name_match = re.search(r',(.+)$', line)
            name = name_match.group(1).strip() if name_match else 'Unknown'
            
            # Next line should be the stream URL
            i += 1
            if i < len(lines):
                url = lines[i].strip()
                
                if url and url.startswith('http'):
                    channels.append({
                        'name': name,
                        'logo': logo,
                        'category': category,
                        'url': url
                    })
        
        i += 1
    
    utils.kodilog(f'LiveTV: Parsed {len(channels)} channels from M3U')
    return channels


def get_channels_data():
    """Get all channels from M3U playlist"""
    m3u_content = fetch_m3u()
    return parse_m3u(m3u_content)


@url_dispatcher.register()
def Main():
    """Main Live TV menu"""
    utils.kodilog('LiveTV: Showing main menu')
    
    # Add menu options
    url_dispatcher.add_dir(
        'Browse by Category',
        '',
        'show_categories',
        addon_image('matrix-icon-pack/Genres.png')
    )
    
    url_dispatcher.add_dir(
        'All Channels',
        '',
        'show_all_channels',
        addon_image('matrix-icon-pack/LiveTV.png')
    )
    
    utils.eod()


@url_dispatcher.register()
def show_categories():
    """Show channel categories"""
    utils.kodilog('LiveTV: Showing categories')
    
    channels = get_channels_data()
    if not channels:
        utils.notify('Live TV', 'Failed to load channels', icon=addon_image('matrix-icon-pack/LiveTV.png'))
        utils.eod()
        return
    
    # Count channels per category
    categories = {}
    for channel in channels:
        cat = channel['category']
        if cat not in categories:
            categories[cat] = 0
        categories[cat] += 1
    
    # Display categories
    for category, count in sorted(categories.items()):
        label = f'{category} ({count} channels)'
        
        url_dispatcher.add_dir(
            label,
            category,
            'show_channels_by_category',
            addon_image('matrix-icon-pack/Genres.png')
        )
    
    utils.eod()


@url_dispatcher.register()
def show_channels_by_category(url):
    """Show channels in a specific category"""
    category = url
    utils.kodilog(f'LiveTV: Showing channels for category: {category}')
    
    channels = get_channels_data()
    if not channels:
        utils.notify('Live TV', 'Failed to load channels', icon=addon_image('matrix-icon-pack/LiveTV.png'))
        utils.eod()
        return
    
    # Filter channels by category
    category_channels = [ch for ch in channels if ch['category'] == category]
    
    # Display channels
    for channel in sorted(category_channels, key=lambda x: x['name']):
        play_channel(channel)
    
    utils.eod()


@url_dispatcher.register()
def show_all_channels():
    """Show all available channels"""
    utils.kodilog('LiveTV: Showing all channels')
    
    channels = get_channels_data()
    if not channels:
        utils.notify('Live TV', 'Failed to load channels', icon=addon_image('matrix-icon-pack/LiveTV.png'))
        utils.eod()
        return
    
    # Display all channels
    for channel in sorted(channels, key=lambda x: x['name']):
        play_channel(channel)
    
    utils.eod()


def play_channel(channel):
    """Add a playable channel to the list"""
    name = channel['name']
    url = channel['url']
    logo = channel['logo']
    category = channel['category']
    
    # Use logo if available, otherwise use default LiveTV icon
    icon = logo if logo else addon_image('matrix-icon-pack/LiveTV.png')
    
    # Add as playable item
    addDownLink(
        name,
        url,
        'live_tv.play_stream',
        icon,
        desc=category
    )


@url_dispatcher.register()
def play_stream(url):
    """Play a live stream"""
    utils.kodilog(f'LiveTV: Playing stream: {url}')
    
    # Use VideoPlayer to play the stream
    player = utils.VideoPlayer('Live TV', False)
    player.play_from_direct_link(url)
