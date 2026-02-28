from resources.lib.url_dispatcher import URL_Dispatcher
from weakref import WeakSet
import re
import os
import json
from resources.lib import basics


class SiteBase(URL_Dispatcher):
    instances = WeakSet()
    clean_functions = set()
    _sites_config = None
    _sites_json_path = None

    def __init__(self, name, title, url=None, image=None, about=None, webcam=False):
        self.default_mode = ''
        self.name = name
        self.title = title
        
        # Load URL from sites.json if not provided
        if url is None:
            url = self._load_url_from_config(name)
        
        self.url = url
        self.image = basics.addon_image(image) if image else ''
        self.about = about
        self.webcam = webcam
        self.custom = False
        self.add_to_instances()

    @classmethod
    def _load_sites_config(cls):
        """Load sites.json configuration"""
        if cls._sites_config is None:
            if cls._sites_json_path is None:
                cls._sites_json_path = os.path.join(
                    os.path.dirname(__file__), 'sites.json'
                )
            
            try:
                with open(cls._sites_json_path, 'r', encoding='utf-8') as f:
                    cls._sites_config = json.load(f)
            except Exception as e:
                import xbmc
                xbmc.log(f'3rbi: Failed to load sites.json: {e}', xbmc.LOGERROR)
                cls._sites_config = {'sites': {}}
        
        return cls._sites_config

    @classmethod
    def _load_url_from_config(cls, site_name):
        """Load site URL from sites.json"""
        config = cls._load_sites_config()
        site_data = config.get('sites', {}).get(site_name, {})
        url = site_data.get('url', '')
        
        if not url:
            import xbmc
            xbmc.log(f'3rbi: No URL found for site {site_name} in sites.json', xbmc.LOGWARNING)
        
        return url

    @classmethod
    def update_site_url(cls, site_name, new_url):
        """Update site URL in sites.json when redirect detected"""
        try:
            config = cls._load_sites_config()
            
            if site_name in config.get('sites', {}):
                old_url = config['sites'][site_name].get('url', '')
                config['sites'][site_name]['url'] = new_url
                
                # Write back to sites.json
                with open(cls._sites_json_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=4, ensure_ascii=False)
                
                # Update cached config
                cls._sites_config = config
                
                # Update instance URL
                for ins in cls.instances:
                    if ins.name == site_name:
                        ins.url = new_url
                
                import xbmc
                xbmc.log(f'3rbi: Updated {site_name} URL from {old_url} to {new_url}', xbmc.LOGINFO)
                return True
            else:
                import xbmc
                xbmc.log(f'3rbi: Site {site_name} not found in sites.json', xbmc.LOGWARNING)
                return False
        except Exception as e:
            import xbmc
            xbmc.log(f'3rbi: Failed to update site URL: {e}', xbmc.LOGERROR)
            return False

    def add_to_instances(self):
        super(SiteBase, self).__init__(self.name)
        self.__class__.instances.add(self)

    def get_clean_title(self):
        title = self.title
        if ']' in title and '[/' in title:
            title = ''.join(re.compile(r'[\]](.*?)[\[]/').findall(title))
        return title

    def register(self, default_mode=False, clean_mode=False):
        def dec(f):
            if default_mode:
                if self.default_mode:
                    raise Exception('A default mode is already defined')
                self.default_mode = '{}.{}'.format(self.module_name, f.__name__)
            if clean_mode:
                self.__class__.clean_functions.add(f)
            super_register = super(SiteBase, self).register()
            func = super_register(f)
            return func
        return dec

    @classmethod
    def get_sites(cls):
        for ins in cls.instances:
            if ins.default_mode:
                yield ins

    @classmethod
    def get_internal_sites(cls):
        for ins in cls.instances:
            if ins.default_mode and not ins.custom:
                yield ins

    @classmethod
    def get_site_by_name(cls, name):
        for ins in cls.instances:
            if ins.name == name and ins.default_mode:
                return ins
        return None

    @classmethod
    def get_sites_by_name(cls, names):
        for name in names:
            site = cls.get_site_by_name(name)
            if site:
                yield site

    @classmethod
    def get_custom_sites(cls):
        for ins in cls.instances:
            if ins.default_mode and ins.custom:
                yield ins
