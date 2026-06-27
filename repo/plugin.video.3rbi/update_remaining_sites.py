#!/usr/bin/env python3
"""
Batch update script to unify category names across all remaining site modules
"""

import os
import re

# Site updates mapping: site_name -> list of (old_arabic, new_english, url_path)
SITE_UPDATES = {
    'egydead': [
        ('أفلام أجنبي', 'English Movies', '/category/افلام-اجنبي/'),
        ('أفلام عربي', 'Arabic Movies', '/category/افلام-عربي/'),
        ('أفلام تركية', 'Turkish Movies', '/category/افلام-تركية/'),
        ('أفلام أسيوية', 'Asian Movies', '/category/افلام-اسيوية/'),
        ('أفلام مدبلجة', 'Dubbed Movies', '/category/افلام-مدبلجة/'),
        ('أفلام كرتون', 'Cartoon Movies', '/category/افلام-كرتون/'),
        ('أفلام هندية', 'Indian Movies', '/category/افلام-هندية/'),
        ('أفلام وثائقية', 'Documentary Movies', '/category/افلام-وثائقية/'),
        ('مسلسلات أجنبي', 'English TV Shows', '/category/مسلسلات-اجنبي/'),
        ('مسلسلات عربي', 'Arabic TV Shows', '/category/مسلسلات-عربي/'),
        ('مسلسلات تركية', 'Turkish TV Shows', '/category/مسلسلات-تركية/'),
        ('مسلسلات أسيوية', 'Asian TV Shows', '/category/مسلسلات-اسيوية/'),
        ('مسلسلات لاتينية', 'Latin TV Shows', '/category/مسلسلات-لاتينية/'),
        ('مسلسلات كرتون', 'Cartoon TV Shows', '/category/مسلسلات-كرتون/'),
        ('بحث', 'Search', ''),
    ],
    'arabseed': [
        ('Search Movies', 'Search', ''),
        ('Search Series', 'Search', ''),
        ('مضاف حديثا', 'Recently Added', '/recently-added/'),
        ('أفلام أجنبية', 'English Movies', '/category/movies/foreign/'),
        ('أفلام عربية', 'Arabic Movies', '/category/movies/arabic/'),
        ('أفلام Netflix', 'Netflix Movies', '/category/movies/netflix/'),
        ('مسلسلات أجنبية', 'English TV Shows', '/category/series/foreign/'),
        ('مسلسلات عربية', 'Arabic TV Shows', '/category/series/arabic/'),
        ('مسلسلات تركية', 'Turkish TV Shows', '/category/series/turkish/'),
        ('مسلسلات Netflix', 'Netflix TV Shows', '/category/series/netflix/'),
        ('مصارعة', 'WWE', '/category/wwe/'),
    ],
    'asia2tv': [
        ('Search Movies', 'Search', ''),
        ('Search Series', 'Search', ''),
        ('أفلام آسيوية', 'Asian Movies', '/category/asian-movies/'),
        ('مسلسلات آسيوية', 'Asian TV Shows', '/category/asian-series/'),
        ('مسلسلات كورية', 'Korean TV Shows', '/category/korean-series/'),
        ('مسلسلات صينية', 'Chinese TV Shows', '/category/chinese-series/'),
        ('مسلسلات يابانية', 'Japanese TV Shows', '/category/japanese-series/'),
        ('مسلسلات تايلاندية', 'Thai TV Shows', '/category/thai-series/'),
        ('برامج ترفيهية', 'TV Programs', '/category/variety-shows/'),
    ],
    'fajershow': [
        ('Search', 'Search', ''),
        ('أفلام أجنبية', 'English Movies', '/category/foreign-movies/'),
        ('أفلام عربية', 'Arabic Movies', '/category/arabic-movies/'),
        ('أفلام تركية', 'Turkish Movies', '/category/turkish-movies/'),
        ('أفلام هندية', 'Indian Movies', '/category/indian-movies/'),
        ('أفلام كرتون', 'Cartoon Movies', '/category/cartoon-movies/'),
        ('مسلسلات أجنبية', 'English TV Shows', '/category/foreign-series/'),
        ('مسلسلات عربية', 'Arabic TV Shows', '/category/arabic-series/'),
        ('مسلسلات تركية', 'Turkish TV Shows', '/category/turkish-series/'),
        ('مسلسلات هندية', 'Indian TV Shows', '/category/indian-series/'),
        ('مسرحيات', 'Theater', '/category/theater/'),
    ],
    'daktna': [
        ('Search', 'Search', ''),
        ('مسلسلات رمضان', 'Ramadan TV Shows', '/category/ramadan/'),
        ('مسلسلات عربية', 'Arabic TV Shows', '/category/arabic-series/'),
        ('مسلسلات تركية', 'Turkish TV Shows', '/category/turkish-series/'),
    ],
    'shoofmax': [
        ('أفلام', 'Movies', '/genre/فيلم'),
        ('مسلسلات', 'TV Shows', '/genre/مسلسل'),
        ('بحث', 'Search', ''),
    ],
    'esseq': [
        ('أفلام', 'Movies', '/movies/'),
        ('مسلسلات كاملة', 'Complete Series', '/series/'),
        ('بحث', 'Search', ''),
    ],
    'akwam': [
        ('Movies', 'Movies', '/movies'),
        ('Series', 'TV Shows', '/series'),
        ('TV Shows', 'TV Programs', '/shows'),
        ('Mix', 'Recently Added', '/'),
        ('Search', 'Search', ''),
    ],
}

def update_site_main_menu(site_name, updates):
    """Update a site's Main menu with unified categories"""
    filepath = f'resources/lib/sites/{site_name}.py'
    
    if not os.path.exists(filepath):
        print(f'❌ {site_name}.py not found')
        return False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add import if not present
    if 'from resources.lib.category_mapper import get_category_icon' not in content:
        # Find Main function and add import
        main_pattern = r'(@site\.register\(default_mode=True\)\s*\ndef Main\(\):)'
        replacement = r'\1\n    from resources.lib.category_mapper import get_category_icon'
        content = re.sub(main_pattern, replacement, content)
    
    # Update each category
    for old_name, new_name, url_path in updates:
        # Pattern to match site.add_dir with the old category name
        old_pattern = rf"site\.add_dir\(['\"]({re.escape(old_name)})['\"],\s*([^,]+),\s*([^,]+),\s*site\.image\)"
        new_line = f"site.add_dir('{new_name}', \\2, \\3, get_category_icon('{new_name}'))"
        content = re.sub(old_pattern, new_line, content)
    
    # Write updated content
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'✅ Updated {site_name}.py ({len(updates)} categories)')
    return True

def main():
    print('🔄 Updating remaining site modules with unified categories...\n')
    
    updated = 0
    failed = 0
    
    for site_name, updates in SITE_UPDATES.items():
        if update_site_main_menu(site_name, updates):
            updated += 1
        else:
            failed += 1
    
    print(f'\n📊 Summary: {updated} sites updated, {failed} failed')
    
    if updated > 0:
        print('\n✅ Run the following to deploy:')
        print('python3 -m py_compile resources/lib/sites/*.py')
        print('cp resources/lib/sites/*.py "/Users/mohammed/Library/Application Support/Kodi/addons/plugin.video.3rbi/resources/lib/sites/"')

if __name__ == '__main__':
    main()
