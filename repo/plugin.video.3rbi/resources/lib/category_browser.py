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


def get_site_categories():
    """
    Dynamically discover which categories each site offers.
    Returns: dict mapping category_name -> list of site info dicts
    """
    from resources.lib.sites import __all__ as site_modules
    
    category_sites = {}
    
    for site_module_name in site_modules:
        try:
            # Import the site module
            site_module = importlib.import_module(f'resources.lib.sites.{site_module_name}')
            
            # Get the site instance
            if not hasattr(site_module, 'site'):
                continue
            
            site = site_module.site
            
            # Skip if site URL is not configured
            if not site.url:
                continue
            
            # Get the Main function to extract categories
            if not hasattr(site_module, 'Main'):
                continue
            
            # Parse the Main function source to extract add_dir calls
            try:
                main_source = inspect.getsource(site_module.Main)
            except:
                continue
            
            # Extract site.add_dir calls with category names
            # Pattern: site.add_dir('Category Name', url_expression, 'mode', ...)
            pattern = r"site\.add_dir\(['\"]([^'\"]+)['\"],\s*([^,]+),\s*['\"]([^'\"]+)['\"]"
            matches = re.findall(pattern, main_source)
            
            for category_name, url_expr, mode in matches:
                # Skip search functions
                if 'search' in mode.lower():
                    continue
                
                # Evaluate the URL expression to get the actual URL
                # This handles expressions like: site.url + '/category/movies/'
                try:
                    # Create a safe evaluation context with site object
                    eval_context = {'site': site}
                    actual_url = eval(url_expr, {"__builtins__": {}}, eval_context)
                except:
                    # If evaluation fails, use the expression as-is
                    actual_url = url_expr
                
                # Add this site to the category
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
