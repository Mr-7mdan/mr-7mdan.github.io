# -*- coding: utf-8 -*-
"""
Category Mapper - Unified category naming and icon mapping for 3rbi addon
"""

from resources.lib.basics import addon_image

# Unified category names (English)
CATEGORIES = [
    # Movies
    'English Movies',
    'Arabic Movies',
    'Turkish Movies',
    'Indian Movies',
    'Asian Movies',
    'Dubbed Movies',
    'Cartoon Movies',
    'Anime Movies',
    'Documentary Movies',
    'Netflix Movies',
    
    # TV Shows
    'English TV Shows',
    'Arabic TV Shows',
    'Turkish TV Shows',
    'Turkish TV Shows (Dubbed)',
    'Indian TV Shows',
    'Asian TV Shows',
    'Korean TV Shows',
    'Chinese TV Shows',
    'Japanese TV Shows',
    'Thai TV Shows',
    'Latin TV Shows',
    'Cartoon TV Shows',
    'Netflix TV Shows',
    'Ramadan TV Shows',
    
    # Other
    'TV Programs',
    'WWE',
    'Theater',
    'Recently Added',
    
    # Generic
    'Movies',
    'TV Shows',
    'Complete Series',
    'Search',
]

# Icon mapping to professional-icon-pack (using actual file names)
CATEGORY_ICONS = {
    # Movies
    'English Movies': 'professional-icon-pack/MoviesEnglish.png',
    'Arabic Movies': 'professional-icon-pack/MoviesArabic.png',
    'Turkish Movies': 'professional-icon-pack/MoviesTurkish.png',
    'Indian Movies': 'professional-icon-pack/MoviesHindi.png',
    'Asian Movies': 'professional-icon-pack/MoviesAsian.png',
    'Dubbed Movies': 'professional-icon-pack/MoviesAsian-Dubbed.png',
    'Cartoon Movies': 'professional-icon-pack/MoviesCartoon.png',
    'Anime Movies': 'professional-icon-pack/MoviesAnime.png',
    'Documentary Movies': 'professional-icon-pack/MoviesDocumentary.png',
    'Netflix Movies': 'professional-icon-pack/Movies.png',
    
    # TV Shows
    'English TV Shows': 'professional-icon-pack/TVShowsEnglish.png',
    'Arabic TV Shows': 'professional-icon-pack/TVShowsArabic.png',
    'Turkish TV Shows': 'professional-icon-pack/TVShowsTurkish.png',
    'Turkish TV Shows (Dubbed)': 'professional-icon-pack/TVShowsTurkish.png',
    'Indian TV Shows': 'professional-icon-pack/TVShowsHindi.png',
    'Asian TV Shows': 'professional-icon-pack/TVShowsAsian.png',
    'Korean TV Shows': 'professional-icon-pack/TVShowsKorean.png',
    'Chinese TV Shows': 'professional-icon-pack/Chinese.png',
    'Japanese TV Shows': 'professional-icon-pack/Japanese.png',
    'Thai TV Shows': 'professional-icon-pack/Thai.png',
    'Latin TV Shows': 'professional-icon-pack/MoviesLatin.png',
    'Cartoon TV Shows': 'professional-icon-pack/Cartoon.png',
    'Netflix TV Shows': 'professional-icon-pack/TVShows.png',
    'Ramadan TV Shows': 'professional-icon-pack/Ramadan.png',
    
    # Other
    'TV Programs': 'professional-icon-pack/Programs.png',
    'WWE': 'professional-icon-pack/WWE.png',
    'Theater': 'professional-icon-pack/Theater.png',
    'Recently Added': 'professional-icon-pack/News.png',
    
    # Generic
    'Movies': 'professional-icon-pack/Movies.png',
    'TV Shows': 'professional-icon-pack/TVShows.png',
    'Complete Series': 'professional-icon-pack/TVShows.png',
    'Search': 'professional-icon-pack/Search.png',
}

def get_category_icon(category_name):
    """Get icon path for category name"""
    icon_path = CATEGORY_ICONS.get(category_name)
    if icon_path:
        return addon_image(icon_path)
    return None


def get_all_categories():
    """Get all category names"""
    return CATEGORIES


def get_categories_by_type(category_type):
    """Get categories filtered by type (movies, tvshows, other)"""
    if category_type == 'movies':
        return [c for c in CATEGORIES if 'Movies' in c]
    elif category_type == 'tvshows':
        return [c for c in CATEGORIES if 'TV Shows' in c or c == 'Complete Series']
    elif category_type == 'other':
        return [c for c in CATEGORIES if c in ['TV Programs', 'WWE', 'Theater', 'Recently Added']]
    elif category_type == 'special':
        return ['Search']
    return []
