# -*- coding: utf-8 -*-
"""
Site Manager Module
Manages built-in sites (enable/disable, updates from GitHub)
"""

import json
import os
import xbmc
from resources.lib import basics
from resources.lib import utils
from resources.lib.url_dispatcher import URL_Dispatcher

url_dispatcher = URL_Dispatcher('site_manager')
dialog = utils.dialog

SITES_JSON_PATH = os.path.join(basics.rootDir, 'resources', 'lib', 'sites.json')
GITHUB_BASE_URL = 'https://raw.githubusercontent.com/Mr-7mdan/mr-7mdan.github.io/master/repo/plugin.video.3rbi'


def load_sites_config():
    """Load sites.json configuration"""
    try:
        with open(SITES_JSON_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        utils.kodilog('Site Manager: Failed to load sites.json: {}'.format(str(e)))
        return {'sites': {}}


def save_sites_config(config):
    """Save sites.json configuration"""
    try:
        with open(SITES_JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        utils.kodilog('Site Manager: Failed to save sites.json: {}'.format(str(e)))
        dialog.ok('Error', 'Failed to save configuration', str(e))
        return False


@url_dispatcher.register()
def list_sites():
    """List all sites with their status"""
    config = load_sites_config()
    sites = config.get('sites', {})
    
    if not sites:
        utils.notify('No Sites Found', 'sites.json is empty')
        return
    
    enabled_sites = []
    disabled_sites = []
    
    for site_name, site_data in sorted(sites.items(), key=lambda x: x[1].get('label', x[0]).lower()):
        label = site_data.get('label', site_name)
        url = site_data.get('url', 'N/A')
        is_active = site_data.get('active', False)
        
        site_info = '{} - {}'.format(label, url)
        
        if is_active:
            enabled_sites.append(site_info)
        else:
            disabled_sites.append(site_info)
    
    text = ''
    if enabled_sites:
        text += 'ENABLED SITES ({}):[CR]'.format(len(enabled_sites))
        text += '[CR]'.join(enabled_sites) + '[CR][CR]'
    
    if disabled_sites:
        text += 'DISABLED SITES ({}):[CR]'.format(len(disabled_sites))
        text += '[CR]'.join(disabled_sites)
    
    utils.textBox('Installed Sites', text.strip())


@url_dispatcher.register()
def enable_site():
    """Enable a disabled site"""
    config = load_sites_config()
    sites = config.get('sites', {})
    
    disabled_sites = {site_data.get('label', name): name 
                     for name, site_data in sites.items() 
                     if not site_data.get('active', False)}
    
    if not disabled_sites:
        utils.notify('No Disabled Sites', 'All sites are already enabled')
        return
    
    chosen = utils.selector("Select site to enable", disabled_sites, show_on_one=True)
    if not chosen:
        return
    
    site_name = chosen
    config['sites'][site_name]['active'] = True
    
    if save_sites_config(config):
        label = config['sites'][site_name].get('label', site_name)
        xbmc.executebuiltin('Container.Refresh')
        utils.notify(label, 'Site enabled. Restart Kodi to apply changes.')


@url_dispatcher.register()
def disable_site():
    """Disable an enabled site"""
    config = load_sites_config()
    sites = config.get('sites', {})
    
    enabled_sites = {site_data.get('label', name): name 
                    for name, site_data in sites.items() 
                    if site_data.get('active', False)}
    
    if not enabled_sites:
        utils.notify('No Enabled Sites', 'All sites are already disabled')
        return
    
    chosen = utils.selector("Select site to disable", enabled_sites, show_on_one=True)
    if not chosen:
        return
    
    site_name = chosen
    config['sites'][site_name]['active'] = False
    
    if save_sites_config(config):
        label = config['sites'][site_name].get('label', site_name)
        xbmc.executebuiltin('Container.Refresh')
        utils.notify(label, 'Site disabled. Restart Kodi to apply changes.')


@url_dispatcher.register()
def enable_all_sites():
    """Enable all sites"""
    if not dialog.yesno('Enable All Sites', 'Enable all sites?', 'This will activate all available sites.'):
        return
    
    config = load_sites_config()
    sites = config.get('sites', {})
    
    count = 0
    for site_name in sites:
        if not sites[site_name].get('active', False):
            sites[site_name]['active'] = True
            count += 1
    
    if save_sites_config(config):
        xbmc.executebuiltin('Container.Refresh')
        utils.notify('Sites Enabled', '{} sites enabled. Restart Kodi to apply changes.'.format(count))


@url_dispatcher.register()
def disable_all_sites():
    """Disable all sites"""
    if not dialog.yesno('Disable All Sites', 'Disable all sites?', 
                       'This will deactivate all sites. You can re-enable them later.'):
        return
    
    config = load_sites_config()
    sites = config.get('sites', {})
    
    count = 0
    for site_name in sites:
        if sites[site_name].get('active', False):
            sites[site_name]['active'] = False
            count += 1
    
    if save_sites_config(config):
        xbmc.executebuiltin('Container.Refresh')
        utils.notify('Sites Disabled', '{} sites disabled. Restart Kodi to apply changes.'.format(count))


@url_dispatcher.register()
def check_updates():
    """Check for site updates from GitHub"""
    progress = utils.progress
    progress.create('Checking for Updates', 'Connecting to GitHub...')
    
    try:
        # Download sites.json from GitHub
        github_json_url = '{}/resources/lib/sites.json'.format(GITHUB_BASE_URL)
        utils.kodilog('Site Manager: Checking updates from: {}'.format(github_json_url))
        
        progress.update(25, 'Downloading sites.json...')
        github_json = utils.getHtml(github_json_url, headers={'User-Agent': utils.USER_AGENT})
        
        if not github_json:
            progress.close()
            dialog.ok('Update Check Failed', 'Could not download sites.json from GitHub', 
                     'Please check your internet connection.')
            return
        
        progress.update(50, 'Comparing versions...')
        
        # Parse GitHub JSON
        try:
            github_config = json.loads(github_json)
            github_sites = github_config.get('sites', {})
        except:
            progress.close()
            dialog.ok('Update Check Failed', 'Invalid sites.json from GitHub')
            return
        
        # Load local config
        local_config = load_sites_config()
        local_sites = local_config.get('sites', {})
        
        # Find new sites and updates
        new_sites = []
        updated_sites = []
        
        for site_name, github_data in github_sites.items():
            if site_name not in local_sites:
                new_sites.append(github_data.get('label', site_name))
            else:
                # Check if URL changed (simple version check)
                if github_data.get('url') != local_sites[site_name].get('url'):
                    updated_sites.append(github_data.get('label', site_name))
        
        progress.close()
        
        # Show results
        text = ''
        if new_sites:
            text += 'NEW SITES AVAILABLE ({}):[CR]'.format(len(new_sites))
            text += '[CR]'.join(new_sites) + '[CR][CR]'
        
        if updated_sites:
            text += 'SITES WITH UPDATES ({}):[CR]'.format(len(updated_sites))
            text += '[CR]'.join(updated_sites) + '[CR][CR]'
        
        if not new_sites and not updated_sites:
            text = 'All sites are up to date!'
        else:
            text += '[CR]Use "Update All Sites" to download updates.'
        
        utils.textBox('Update Check Results', text.strip())
        
    except Exception as e:
        progress.close()
        utils.kodilog('Site Manager: Update check failed: {}'.format(str(e)))
        dialog.ok('Update Check Failed', 'An error occurred', str(e))


@url_dispatcher.register()
def update_all_sites():
    """Update all sites from GitHub"""
    if not dialog.yesno('Update All Sites', 
                       'This will download the latest sites.json and site modules from GitHub.',
                       'Continue?'):
        return
    
    progress = utils.progress
    progress.create('Updating Sites', 'Downloading sites.json...')
    
    try:
        # Download sites.json
        github_json_url = '{}/resources/lib/sites.json'.format(GITHUB_BASE_URL)
        github_json = utils.getHtml(github_json_url, headers={'User-Agent': utils.USER_AGENT})
        
        if not github_json:
            progress.close()
            dialog.ok('Update Failed', 'Could not download sites.json from GitHub')
            return
        
        # Parse and save sites.json
        try:
            github_config = json.loads(github_json)
            github_sites = github_config.get('sites', {})
        except:
            progress.close()
            dialog.ok('Update Failed', 'Invalid sites.json from GitHub')
            return
        
        # Load current config to preserve active states
        local_config = load_sites_config()
        local_sites = local_config.get('sites', {})
        
        # Merge: keep existing active states, add new sites as inactive by default
        for site_name, github_data in github_sites.items():
            if site_name in local_sites:
                # Keep existing active state
                github_data['active'] = local_sites[site_name].get('active', False)
            else:
                # New site - add as inactive by default
                github_data['active'] = False
        
        progress.update(25, 'Saving sites.json...')
        
        # Save updated sites.json
        if not save_sites_config(github_config):
            progress.close()
            return
        
        progress.update(50, 'Downloading site modules...')
        
        # Download site .py files
        sites_dir = os.path.join(basics.rootDir, 'resources', 'lib', 'sites')
        downloaded = []
        failed = []
        
        for idx, site_name in enumerate(github_sites.keys()):
            progress.update(50 + int((idx / len(github_sites)) * 40), 
                          'Downloading {}...'.format(site_name))
            
            # Download .py file
            py_url = '{}/resources/lib/sites/{}.py'.format(GITHUB_BASE_URL, site_name)
            py_content = utils.getHtml(py_url, headers={'User-Agent': utils.USER_AGENT})
            
            if py_content:
                try:
                    py_path = os.path.join(sites_dir, '{}.py'.format(site_name))
                    with open(py_path, 'w', encoding='utf-8') as f:
                        f.write(py_content)
                    downloaded.append(site_name)
                except Exception as e:
                    utils.kodilog('Site Manager: Failed to save {}.py: {}'.format(site_name, str(e)))
                    failed.append(site_name)
            else:
                failed.append(site_name)
            
            # Try to download icon (optional)
            icon_url = '{}/resources/images/sites/{}.png'.format(GITHUB_BASE_URL, site_name)
            icon_content = utils.getHtml(icon_url, headers={'User-Agent': utils.USER_AGENT}, error='ignore')
            
            if icon_content:
                try:
                    icons_dir = os.path.join(basics.rootDir, 'resources', 'images', 'sites')
                    if not os.path.exists(icons_dir):
                        os.makedirs(icons_dir)
                    icon_path = os.path.join(icons_dir, '{}.png'.format(site_name))
                    with open(icon_path, 'wb') as f:
                        f.write(icon_content.encode('latin1') if isinstance(icon_content, str) else icon_content)
                except:
                    pass  # Icon is optional
        
        progress.close()
        
        # Show results
        text = 'Downloaded: {} sites[CR]'.format(len(downloaded))
        if failed:
            text += 'Failed: {} sites[CR]'.format(len(failed))
            text += '[CR]Failed sites:[CR]' + '[CR]'.join(failed)
        
        text += '[CR][CR]Restart Kodi to apply changes.'
        
        dialog.ok('Update Complete', text)
        xbmc.executebuiltin('Container.Refresh')
        
    except Exception as e:
        progress.close()
        utils.kodilog('Site Manager: Update failed: {}'.format(str(e)))
        dialog.ok('Update Failed', 'An error occurred', str(e))
