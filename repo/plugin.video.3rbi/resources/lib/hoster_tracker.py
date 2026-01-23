# -*- coding: utf-8 -*-
"""
Hoster Tracking System
Tracks success/failure rates for hosters to identify reliable ones
"""

import os
import json
from resources.lib import utils
from resources.lib.basics import profileDir, addon

class HosterTracker:
    """Track hoster reliability statistics"""
    
    def __init__(self):
        self.stats_file = os.path.join(profileDir, 'hoster_stats.json')
        self.stats = self._load_stats()
    
    def _load_stats(self):
        """Load statistics from file"""
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            utils.kodilog('HosterTracker: Error loading stats - {}'.format(str(e)))
        return {}
    
    def _save_stats(self):
        """Save statistics to file"""
        try:
            # Ensure data directory exists
            if not os.path.exists(utils.dataPath):
                os.makedirs(utils.dataPath)
            
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            utils.kodilog('HosterTracker: Error saving stats - {}'.format(str(e)))
    
    def _extract_hoster_name(self, url):
        """Extract hoster name from URL"""
        try:
            from six.moves import urllib_parse
            domain = urllib_parse.urlparse(url).netloc
            # Remove www. prefix and get base domain
            domain = domain.replace('www.', '')
            # Get main domain (e.g., mixdrop.co from abc.mixdrop.co)
            parts = domain.split('.')
            if len(parts) >= 2:
                return '.'.join(parts[-2:])
            return domain
        except:
            return 'unknown'
    
    def record_success(self, url):
        """Record successful resolution"""
        if not addon.getSetting('track_hoster_success') == 'true':
            return
        
        hoster = self._extract_hoster_name(url)
        if hoster not in self.stats:
            self.stats[hoster] = {'success': 0, 'failure': 0, 'total': 0}
        
        self.stats[hoster]['success'] += 1
        self.stats[hoster]['total'] += 1
        self._save_stats()
        
        utils.kodilog('HosterTracker: Success for {} ({}/{})'.format(
            hoster, self.stats[hoster]['success'], self.stats[hoster]['total']))
    
    def record_failure(self, url):
        """Record failed resolution"""
        if not addon.getSetting('track_hoster_success') == 'true':
            return
        
        hoster = self._extract_hoster_name(url)
        if hoster not in self.stats:
            self.stats[hoster] = {'success': 0, 'failure': 0, 'total': 0}
        
        self.stats[hoster]['failure'] += 1
        self.stats[hoster]['total'] += 1
        self._save_stats()
        
        utils.kodilog('HosterTracker: Failure for {} ({}/{})'.format(
            hoster, self.stats[hoster]['failure'], self.stats[hoster]['total']))
    
    def is_trusted(self, url):
        """Check if hoster is trusted based on success rate"""
        hoster = self._extract_hoster_name(url)
        
        if hoster not in self.stats:
            return False
        
        stats = self.stats[hoster]
        total = stats['total']
        
        # Get threshold settings
        try:
            min_attempts = int(addon.getSetting('min_attempts_trusted') or '5')
            success_threshold = int(addon.getSetting('trusted_threshold') or '80')
        except:
            min_attempts = 5
            success_threshold = 80
        
        # Need minimum attempts
        if total < min_attempts:
            return False
        
        # Calculate success rate
        success_rate = (stats['success'] / float(total)) * 100
        
        return success_rate >= success_threshold
    
    def get_stats(self, url):
        """Get statistics for a hoster"""
        hoster = self._extract_hoster_name(url)
        return self.stats.get(hoster, {'success': 0, 'failure': 0, 'total': 0})
    
    def clear_stats(self):
        """Clear all statistics"""
        self.stats = {}
        self._save_stats()
        utils.kodilog('HosterTracker: Statistics cleared')

# Global instance
_tracker = None

def get_tracker():
    """Get singleton tracker instance"""
    global _tracker
    if _tracker is None:
        _tracker = HosterTracker()
    return _tracker
