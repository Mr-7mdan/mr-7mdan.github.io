# -*- coding: utf-8 -*-
"""
Category Browser - Dynamic Category → Sites → Content navigation
Automatically discovers which sites offer which categories
"""

import importlib
import re
import inspect
from resources.lib import utils
from resources.lib.basics import addon_image
from resources.lib.site_base import SiteBase
from resources.lib.category_mapper import get_category_icon
from resources.lib.url_dispatcher import URL_Dispatcher

# Create URL dispatcher for category browser
url_dispatcher = URL_Dispatcher('category_browser')


_ADD_DIR_PATTERN = r"site\.add_dir\(['\"]([^'\"]+)['\"],\s*([^,]+),\s*['\"]([^'\"]+)['\"]"
_NAV_MODE_KEYWORDS = ('categories', 'category', 'menu', 'submenu')


def _is_nav_mode(mode):
    """Return True if mode is a navigation/submenu function, not a content function."""
    return any(k in mode.lower() for k in _NAV_MODE_KEYWORDS)


def _extract_add_dirs(source, site):
    """Parse site.add_dir calls from function source. Returns list of (label, url, mode)."""
    results = []
    for label, url_expr, mode in re.findall(_ADD_DIR_PATTERN, source):
        if 'search' in mode.lower():
            continue
        try:
            actual_url = eval(url_expr, {'__builtins__': {}}, {'site': site})
        except Exception:
            actual_url = url_expr
        results.append((label, actual_url, mode))
    return results


def get_site_categories():
    """
    Dynamically discover which categories each site offers.
    Returns: dict mapping category_name -> list of site info dicts
    """
    from resources.lib.sites import __all__ as site_modules

    category_sites = {}

    for site_module_name in site_modules:
        try:
            site_module = importlib.import_module(f'resources.lib.sites.{site_module_name}')

            if not hasattr(site_module, 'site'):
                continue
            site = site_module.site
            if not site.url:
                continue
            if not hasattr(site_module, 'Main'):
                continue

            try:
                main_source = inspect.getsource(site_module.Main)
            except Exception:
                continue

            top_entries = _extract_add_dirs(main_source, site)

            for category_name, actual_url, mode in top_entries:
                # If mode is a navigation-only function, scan one level deeper
                if _is_nav_mode(mode) and hasattr(site_module, mode):
                    try:
                        nav_source = inspect.getsource(getattr(site_module, mode))
                        sub_entries = _extract_add_dirs(nav_source, site)
                        for sub_label, sub_url, sub_mode in sub_entries:
                            if sub_label not in category_sites:
                                category_sites[sub_label] = []
                            category_sites[sub_label].append({
                                'site_name': site.name,
                                'site_title': site.title,
                                'site_image': site.image,
                                'mode': sub_mode,
                                'url': sub_url,
                            })
                    except Exception:
                        pass
                    continue  # don't also add the nav entry itself

                if category_name not in category_sites:
                    category_sites[category_name] = []
                category_sites[category_name].append({
                    'site_name': site.name,
                    'site_title': site.title,
                    'site_image': site.image,
                    'mode': mode,
                    'url': actual_url,
                })

        except Exception as e:
            utils.kodilog(f'CategoryBrowser: Error processing {site_module_name}: {str(e)}')
            continue

    return category_sites


@url_dispatcher.register()
def show_categories():
    """Show all available categories"""
    utils.kodilog('CategoryBrowser: Showing categories')
    
    # Get all categories with their sites
    category_sites = get_site_categories()
    
    # Get unique categories that have at least one site
    available_categories = sorted([cat for cat in category_sites.keys() if category_sites[cat]])
    
    utils.kodilog(f'CategoryBrowser: Found {len(available_categories)} categories')
    
    # Display each category
    for category_name in available_categories:
        sites = category_sites[category_name]
        site_count = len(sites)
        
        # Create label with site count
        label = f'{category_name} ({site_count} sites)'
        
        # Get category icon
        icon = get_category_icon(category_name)
        if not icon:
            icon = addon_image('professional-icon-pack/Genres.png')
        
        # Add directory for this category
        url_dispatcher.add_dir(
            label,
            category_name,
            'show_sites',
            icon
        )
    
    utils.eod()


@url_dispatcher.register()
def show_sites(url):
    """Show all sites that offer a specific category"""
    # The category name comes through the 'url' parameter
    category = url
    utils.kodilog(f'CategoryBrowser: Showing sites for category: {category}')
    
    # Get all categories with their sites
    category_sites = get_site_categories()
    
    if category not in category_sites:
        utils.kodilog(f'CategoryBrowser: Category not found: {category}')
        utils.eod()
        return
    
    sites = category_sites[category]
    utils.kodilog(f'CategoryBrowser: Found {len(sites)} sites for {category}')
    
    # Display each site
    for site_info in sites:
        site_name = site_info['site_name']
        site_title = site_info['site_title']
        site_image = site_info['site_image']
        mode = site_info['mode']
        site_url = site_info['url']
        
        # Create label
        label = f'{site_title} - {category}'
        
        # Get site icon
        icon = addon_image(site_image) if site_image else addon_image('matrix-icon-pack/All.png')
        
        # Add directory that will call the site's specific mode
        # The mode should be the full path like 'cima4u.getMovies'
        full_mode = f'{site_name}.{mode}'
        
        url_dispatcher.add_dir(
            label,
            site_url,  # Pass the actual category URL to the site's function
            full_mode,
            icon
        )
    
    utils.eod()
