import json
import os

# Load active sites from JSON config
# sites.json is in parent directory (resources/lib/)
_sites_json_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sites.json')

try:
    with open(_sites_json_path, 'r') as f:
        _sites_config = json.load(f)
    
    # Get list of active sites
    __all__ = [site_name for site_name, site_data in _sites_config.get('sites', {}).items() 
               if site_data.get('active', False) is True]
except Exception as e:
    # Fallback to hardcoded list if JSON loading fails
    import xbmc
    xbmc.log('3rbi: Failed to load sites.json, using fallback list: {}'.format(str(e)), xbmc.LOGWARNING)
    __all__ = ['aksv', 'fajershow', 'daktna', 'shoofvod', 'asia2tv', 'arabseed', 'cima4u']
