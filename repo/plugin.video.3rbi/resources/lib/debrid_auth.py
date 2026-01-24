# -*- coding: utf-8 -*-
"""
Debrid Authentication Module
Implements OAuth device flow for debrid services (Real-Debrid, AllDebrid, etc.)
Based on Umbrella addon's implementation
"""

import requests
import time
import json
from resources.lib import utils
from resources.lib.basics import addon
from kodi_six import xbmcgui

class DebridAuth:
    """Base class for debrid authentication"""
    
    def __init__(self):
        self.name = "Debrid"
        self.token = None
        self.client_id = None
        self.secret = None
        self.device_code = None
        self.progress_dialog = None
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return bool(self.token)
    
    def reset(self):
        """Reset all authentication data"""
        raise NotImplementedError


class RealDebridAuth(DebridAuth):
    """Real-Debrid OAuth authentication"""
    
    def __init__(self):
        super(RealDebridAuth, self).__init__()
        self.name = "Real-Debrid"
        self.base_url = "https://api.real-debrid.com/rest/1.0/"
        self.oauth_url = "https://api.real-debrid.com/oauth/v2/"
        self.client_id = addon.getSetting('rd_client_id') or 'X245A4XAIBGVM'
        self.token = addon.getSetting('rd_token')
        self.secret = addon.getSetting('rd_secret')
        self.refresh_token_val = addon.getSetting('rd_refresh_token')
    
    def auth(self):
        """Start OAuth device flow authentication"""
        try:
            # Reset credentials
            self.secret = ''
            self.client_id = 'X245A4XAIBGVM'
            
            # Get device code
            url = self.oauth_url + 'device/code?client_id={}&new_credentials=yes'.format(self.client_id)
            response = requests.get(url, timeout=10).json()
            
            self.device_code = response['device_code']
            user_code = response['user_code']
            verification_url = response['direct_verification_url']
            expires_in = int(response['expires_in'])
            interval = int(response['interval'])
            
            # Show auth dialog
            self.progress_dialog = xbmcgui.DialogProgress()
            message = ('Go to: [B]https://real-debrid.com/device[/B]\n'
                      'Enter code: [B]{}[/B]\n'
                      'Or scan QR code at: {}'.format(user_code, verification_url))
            self.progress_dialog.create('Real-Debrid Authorization', message)
            
            # Poll for authorization
            elapsed = 0
            while elapsed < expires_in and not self.progress_dialog.iscanceled():
                if self._check_auth():
                    break
                time.sleep(interval)
                elapsed += interval
                percent = int((elapsed / float(expires_in)) * 100)
                self.progress_dialog.update(percent)
            
            self.progress_dialog.close()
            
            if self.secret:
                # Get token
                return self._get_token()
            
            return False
            
        except Exception as e:
            utils.kodilog('RealDebrid Auth Error: {}'.format(str(e)))
            if self.progress_dialog:
                self.progress_dialog.close()
            xbmcgui.Dialog().ok('Real-Debrid', 'Authentication failed: {}'.format(str(e)))
            return False
    
    def _check_auth(self):
        """Check if user has authorized the device"""
        try:
            url = self.oauth_url + 'device/credentials?client_id={}&code={}'.format(
                self.client_id, self.device_code)
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                self.client_id = data['client_id']
                self.secret = data['client_secret']
                return True
            
            return False
        except:
            return False
    
    def _get_token(self):
        """Exchange device code for access token"""
        try:
            url = self.oauth_url + 'token'
            data = {
                'client_id': self.client_id,
                'client_secret': self.secret,
                'code': self.device_code,
                'grant_type': 'http://oauth.net/grant_type/device/1.0'
            }
            
            response = requests.post(url, data=data, timeout=10).json()
            
            if 'error' in response:
                xbmcgui.Dialog().ok('Real-Debrid', 'Token error: {}'.format(response['error']))
                return False
            
            self.token = response['access_token']
            refresh_token = response['refresh_token']
            
            # Get account info
            account = self._get_account_info()
            if account:
                username = account.get('username', '')
                
                # Save credentials
                utils.setSetting('rd_client_id', self.client_id)
                utils.setSetting('rd_secret', self.secret)
                utils.setSetting('rd_token', self.token)
                utils.setSetting('rd_refresh_token', refresh_token)
                utils.setSetting('rd_username', username)
                
                xbmcgui.Dialog().ok('Real-Debrid',
                                   'Authorization successful!\nUsername: {}'.format(username))
                return True
            
            return False
            
        except Exception as e:
            utils.kodilog('RealDebrid Token Error: {}'.format(str(e)))
            xbmcgui.Dialog().ok('Real-Debrid', 'Failed to get token: {}'.format(str(e)))
            return False
    
    def _get_account_info(self):
        """Get account information"""
        try:
            url = self.base_url + 'user?auth_token={}'.format(self.token)
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def refresh_token(self):
        """Refresh expired token"""
        try:
            if not self.refresh_token_val or not self.client_id or not self.secret:
                return False
            
            url = self.oauth_url + 'token'
            data = {
                'client_id': self.client_id,
                'client_secret': self.secret,
                'code': self.refresh_token_val,
                'grant_type': 'http://oauth.net/grant_type/device/1.0'
            }
            
            response = requests.post(url, data=data, timeout=10).json()
            
            if 'error' in response:
                utils.kodilog('RealDebrid Token Refresh Failed: {}'.format(response['error']))
                return False
            
            self.token = response['access_token']
            refresh_token = response['refresh_token']
            
            utils.setSetting('rd_token', self.token)
            utils.setSetting('rd_refresh_token', refresh_token)
            
            utils.kodilog('RealDebrid Token Refreshed Successfully')
            return True
            
        except Exception as e:
            utils.kodilog('RealDebrid Refresh Error: {}'.format(str(e)))
            return False
    
    def reset(self):
        """Clear all authentication data"""
        utils.setSetting('rd_client_id', '')
        utils.setSetting('rd_secret', '')
        utils.setSetting('rd_token', '')
        utils.setSetting('rd_refresh_token', '')
        utils.setSetting('rd_username', '')
        self.token = None
        self.secret = None
        self.client_id = None


class AllDebridAuth(DebridAuth):
    """AllDebrid authentication (API key based)"""
    
    def __init__(self):
        super(AllDebridAuth, self).__init__()
        self.name = "AllDebrid"
        self.base_url = "https://api.alldebrid.com/v4/"
        self.token = addon.getSetting('ad_api_key')
    
    def auth(self):
        """Get API key from user"""
        keyboard = xbmcgui.Dialog()
        api_key = keyboard.input('Enter AllDebrid API Key:', type=xbmcgui.INPUT_ALPHANUM)
        
        if not api_key:
            return False
        
        # Test API key
        try:
            url = self.base_url + 'user?agent=3rbi&apikey={}'.format(api_key)
            response = requests.get(url, timeout=10).json()
            
            if response.get('status') == 'success':
                username = response['data']['user']['username']
                utils.setSetting('ad_api_key', api_key)
                utils.setSetting('ad_username', username)
                xbmcgui.Dialog().ok('AllDebrid',
                                   'Authorization successful!\nUsername: {}'.format(username))
                return True
            else:
                xbmcgui.Dialog().ok('AllDebrid', 'Invalid API key')
                return False
                
        except Exception as e:
            utils.kodilog('AllDebrid Auth Error: {}'.format(str(e)))
            xbmcgui.Dialog().ok('AllDebrid', 'Authentication failed: {}'.format(str(e)))
            return False
    
    def reset(self):
        """Clear authentication data"""
        utils.setSetting('ad_api_key', '')
        utils.setSetting('ad_username', '')
        self.token = None


class PremiumizeAuth(DebridAuth):
    """Premiumize authentication (API key based)"""
    
    def __init__(self):
        super(PremiumizeAuth, self).__init__()
        self.name = "Premiumize"
        self.base_url = "https://www.premiumize.me/api/"
        self.token = addon.getSetting('pm_api_key')
    
    def auth(self):
        """Get API key from user"""
        keyboard = xbmcgui.Dialog()
        api_key = keyboard.input('Enter Premiumize API Key:', type=xbmcgui.INPUT_ALPHANUM)
        
        if not api_key:
            return False
        
        # Test API key
        try:
            url = self.base_url + 'account/info?apikey={}'.format(api_key)
            response = requests.get(url, timeout=10).json()
            
            if response.get('status') == 'success':
                username = response.get('customer_id', 'User')
                utils.setSetting('pm_api_key', api_key)
                utils.setSetting('pm_username', username)
                xbmcgui.Dialog().ok('Premiumize',
                                   'Authorization successful!\nCustomer ID: {}'.format(username))
                return True
            else:
                xbmcgui.Dialog().ok('Premiumize', 'Invalid API key')
                return False
                
        except Exception as e:
            utils.kodilog('Premiumize Auth Error: {}'.format(str(e)))
            xbmcgui.Dialog().ok('Premiumize', 'Authentication failed: {}'.format(str(e)))
            return False
    
    def reset(self):
        """Clear authentication data"""
        utils.setSetting('pm_api_key', '')
        utils.setSetting('pm_username', '')
        self.token = None


def get_debrid_auth(service_index=0):
    """Get debrid auth instance based on service selection"""
    services = [
        RealDebridAuth,
        AllDebridAuth,
        PremiumizeAuth,
        AllDebridAuth  # Debrid-Link uses same pattern as AllDebrid
    ]
    
    if service_index < len(services):
        return services[service_index]()
    
    return None
