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

# Icon mapping to matrix-icon-pack (using actual file names)
CATEGORY_ICONS = {
    # Movies
    'English Movies': 'matrix-icon-pack/MoviesEnglish.png',
    'Arabic Movies': 'matrix-icon-pack/MoviesArabic.png',
    'Turkish Movies': 'matrix-icon-pack/MoviesTurkish.png',
    'Indian Movies': 'matrix-icon-pack/MoviesHindi.png',
    'Asian Movies': 'matrix-icon-pack/MoviesAsian.png',
    'Dubbed Movies': 'matrix-icon-pack/MoviesAsian-Dubbed.png',
    'Cartoon Movies': 'matrix-icon-pack/MoviesCarton.png',
    'Anime Movies': 'matrix-icon-pack/MoviesAnime.png',
    'Documentary Movies': 'matrix-icon-pack/MoviesDocumentary.png',
    'Netflix Movies': 'matrix-icon-pack/Movies.png',  # No specific Netflix icon
    
    # TV Shows
    'English TV Shows': 'matrix-icon-pack/TVShowsEnglish.png',
    'Arabic TV Shows': 'matrix-icon-pack/TVShowsArabic.png',
    'Turkish TV Shows': 'matrix-icon-pack/TVShowsTurkish.png',
    'Turkish TV Shows (Dubbed)': 'matrix-icon-pack/TVShowsTurkish-Dubbed.png',
    'Indian TV Shows': 'matrix-icon-pack/TVShowsHindi.png',
    'Asian TV Shows': 'matrix-icon-pack/TVShowsAsian.png',
    'Korean TV Shows': 'matrix-icon-pack/TVShowsKorean.png',
    'Chinese TV Shows': 'matrix-icon-pack/Chinese.png',
    'Japanese TV Shows': 'matrix-icon-pack/Japanese.png',
    'Thai TV Shows': 'matrix-icon-pack/Thai.png',
    'Latin TV Shows': 'matrix-icon-pack/MoviesLatin.png',  # Using Movies icon as fallback
    'Cartoon TV Shows': 'matrix-icon-pack/Cartoon.png',
    'Netflix TV Shows': 'matrix-icon-pack/TVShows.png',  # No specific Netflix icon
    'Ramadan TV Shows': 'matrix-icon-pack/Ramadan.png',
    
    # Other
    'TV Programs': 'matrix-icon-pack/Programs.png',
    'WWE': 'matrix-icon-pack/WWE.png',
    'Theater': 'matrix-icon-pack/Theater.png',
    'Recently Added': 'matrix-icon-pack/News.png',
    
    # Generic
    'Movies': 'matrix-icon-pack/Movies.png',
    'TV Shows': 'matrix-icon-pack/TVShows.png',
    'Complete Series': 'matrix-icon-pack/TVShows.png',
    'Search': 'matrix-icon-pack/Search.png',
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
