# Unified Category Mapping for 3rbi Addon

## Unified Category Names (English)

### Movies
- **English Movies** - أفلام أجنبية / أفلام أجنبي
- **Arabic Movies** - أفلام عربية / أفلام عربي
- **Turkish Movies** - أفلام تركية
- **Indian Movies** - أفلام هندية
- **Asian Movies** - أفلام آسيوية / أفلام أسيوية
- **Dubbed Movies** - أفلام مدبلجة
- **Cartoon Movies** - أفلام كرتون
- **Anime Movies** - أفلام إنمي
- **Documentary Movies** - أفلام وثائقية
- **Netflix Movies** - أفلام Netflix

### TV Shows
- **English TV Shows** - مسلسلات أجنبية / مسلسلات أجنبي
- **Arabic TV Shows** - مسلسلات عربية / مسلسلات عربي
- **Turkish TV Shows** - مسلسلات تركية
- **Turkish TV Shows (Dubbed)** - مسلسلات تركية مدبلجة
- **Indian TV Shows** - مسلسلات هندية
- **Asian TV Shows** - مسلسلات آسيوية / مسلسلات أسيوية
- **Korean TV Shows** - مسلسلات كورية
- **Chinese TV Shows** - مسلسلات صينية
- **Japanese TV Shows** - مسلسلات يابانية
- **Thai TV Shows** - مسلسلات تايلاندية
- **Latin TV Shows** - مسلسلات لاتينية
- **Cartoon TV Shows** - مسلسلات كرتون
- **Netflix TV Shows** - مسلسلات Netflix
- **Ramadan TV Shows** - مسلسلات رمضان / مسلسلات رمضان 2025

### Other
- **TV Programs** - برامج تلفزيونية / برامج ترفيهية
- **WWE** - مصارعة / مصارعة حرة
- **Theater** - مسرحيات
- **Recently Added** - مضاف حديثا

### Special
- **Search** - بحث / Search
- **Movies** - أفلام (generic)
- **TV Shows** - مسلسلات (generic)
- **Complete Series** - مسلسلات كاملة
- **Mix** - Mix

## Icon Mapping (from images/matrix-icon-pack)

```python
CATEGORY_ICONS = {
    # Movies
    'English Movies': 'movies-english.png',
    'Arabic Movies': 'movies-arabic.png',
    'Turkish Movies': 'movies-turkish.png',
    'Indian Movies': 'movies-indian.png',
    'Asian Movies': 'movies-asian.png',
    'Dubbed Movies': 'movies-dubbed.png',
    'Cartoon Movies': 'movies-cartoon.png',
    'Anime Movies': 'movies-anime.png',
    'Documentary Movies': 'movies-documentary.png',
    'Netflix Movies': 'movies-netflix.png',
    
    # TV Shows
    'English TV Shows': 'tvshows-english.png',
    'Arabic TV Shows': 'tvshows-arabic.png',
    'Turkish TV Shows': 'tvshows-turkish.png',
    'Turkish TV Shows (Dubbed)': 'tvshows-turkish-dubbed.png',
    'Indian TV Shows': 'tvshows-indian.png',
    'Asian TV Shows': 'tvshows-asian.png',
    'Korean TV Shows': 'tvshows-korean.png',
    'Chinese TV Shows': 'tvshows-chinese.png',
    'Japanese TV Shows': 'tvshows-japanese.png',
    'Thai TV Shows': 'tvshows-thai.png',
    'Latin TV Shows': 'tvshows-latin.png',
    'Cartoon TV Shows': 'tvshows-cartoon.png',
    'Netflix TV Shows': 'tvshows-netflix.png',
    'Ramadan TV Shows': 'tvshows-ramadan.png',
    
    # Other
    'TV Programs': 'tv-programs.png',
    'WWE': 'wwe.png',
    'Theater': 'theater.png',
    'Recently Added': 'recent.png',
    
    # Special
    'Search': 'search.png',
    'Movies': 'movies.png',
    'TV Shows': 'tvshows.png',
    'Complete Series': 'tvshows-complete.png',
    'Mix': 'mix.png',
}
```

## Current Category Usage by Site

### cima4u
- أفلام أجنبية → **English Movies**
- أفلام عربية → **Arabic Movies**
- أفلام هندية → **Indian Movies**
- أفلام تركية → **Turkish Movies**
- أفلام كرتون → **Cartoon Movies**
- مسلسلات أجنبية → **English TV Shows**
- مسلسلات عربية → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- مسلسلات آسيوية → **Asian TV Shows**
- مسلسلات هندية → **Indian TV Shows**
- مسلسلات كرتون → **Cartoon TV Shows**
- مسلسلات رمضان 2025 → **Ramadan TV Shows**
- برامج تلفزيونية → **TV Programs**
- مصارعة حرة → **WWE**
- بحث → **Search**

### shoofvod
- أفلام أجنبية → **English Movies**
- أفلام عربية → **Arabic Movies**
- أفلام تركية → **Turkish Movies**
- أفلام هندية → **Indian Movies**
- أفلام إنمي → **Anime Movies**
- أفلام وثائقية → **Documentary Movies**
- مسلسلات عربية → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- مسلسلات تركية مدبلجة → **Turkish TV Shows (Dubbed)**
- مسلسلات هندية → **Indian TV Shows**
- مسلسلات كرتون → **Cartoon TV Shows**
- مسلسلات رمضان → **Ramadan TV Shows**
- برامج تلفزيونية → **TV Programs**
- مسرحيات → **Theater**
- Search → **Search**

### egydead
- أفلام أجنبي → **English Movies**
- أفلام عربي → **Arabic Movies**
- أفلام تركية → **Turkish Movies**
- أفلام أسيوية → **Asian Movies**
- أفلام مدبلجة → **Dubbed Movies**
- أفلام كرتون → **Cartoon Movies**
- أفلام هندية → **Indian Movies**
- أفلام وثائقية → **Documentary Movies**
- مسلسلات أجنبي → **English TV Shows**
- مسلسلات عربي → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- مسلسلات أسيوية → **Asian TV Shows**
- مسلسلات لاتينية → **Latin TV Shows**
- مسلسلات كرتون → **Cartoon TV Shows**
- بحث → **Search**

### arabseed
- أفلام أجنبية → **English Movies**
- أفلام عربية → **Arabic Movies**
- أفلام Netflix → **Netflix Movies**
- مسلسلات أجنبية → **English TV Shows**
- مسلسلات عربية → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- مسلسلات Netflix → **Netflix TV Shows**
- مصارعة → **WWE**
- مضاف حديثا → **Recently Added**
- Search Movies → **Search**
- Search Series → **Search**

### asia2tv
- أفلام آسيوية → **Asian Movies**
- مسلسلات آسيوية → **Asian TV Shows**
- مسلسلات كورية → **Korean TV Shows**
- مسلسلات صينية → **Chinese TV Shows**
- مسلسلات يابانية → **Japanese TV Shows**
- مسلسلات تايلاندية → **Thai TV Shows**
- برامج ترفيهية → **TV Programs**
- Search Movies → **Search**
- Search Series → **Search**

### fajershow
- أفلام أجنبية → **English Movies**
- أفلام عربية → **Arabic Movies**
- أفلام تركية → **Turkish Movies**
- أفلام هندية → **Indian Movies**
- أفلام كرتون → **Cartoon Movies**
- مسلسلات أجنبية → **English TV Shows**
- مسلسلات عربية → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- مسلسلات هندية → **Indian TV Shows**
- مسرحيات → **Theater**
- Search → **Search**

### daktna
- مسلسلات رمضان → **Ramadan TV Shows**
- مسلسلات عربية → **Arabic TV Shows**
- مسلسلات تركية → **Turkish TV Shows**
- Search → **Search**

### qrmzi
- مسلسلات تركية → **Turkish TV Shows**
- بحث → **Search**

### shoofmax
- أفلام → **Movies**
- مسلسلات → **TV Shows**
- بحث → **Search**

### esseq
- أفلام → **Movies**
- مسلسلات كاملة → **Complete Series**
- بحث → **Search**

### akwam
- Movies → **Movies**
- Series → **TV Shows**
- TV Shows → **TV Programs**
- Mix → **Mix**
- Search → **Search**

### faselhd
- جميع الافلام / Movies → **Movies**
- افلام اجنبي → **English Movies**
- افلام مدبلجة → **Dubbed Movies**
- افلام هندية → **Indian Movies**
- افلام اسيوية → **Asian Movies**
- افلام انمي → **Anime Movies**
- Top Voted Movies → **Movies**
- Most Viewed Movies → **Movies**
- Top IMDB Movies → **Movies**
- Movie Collections → **Movies**
- جميع المسلسلات / TV Shows → **TV Shows**
- مسلسلات اسيوية → **Asian TV Shows**
- Short TV Shows → **TV Shows**
- Most Viewed TV Shows → **TV Shows**
- Top IMDB TV Shows → **TV Shows**
- احدث الحلقات → **Recently Added**
- Anime TV Shows → **TV Shows**
- برامج تلفزيونية → **TV Programs**
- Search → **Search**

## Implementation Plan

1. **Create category mapping utility** (`resources/lib/category_mapper.py`)
2. **Update each site module** to use unified category names
3. **Create category-based navigation** in main menu
4. **Map categories to icons** from matrix-icon-pack
5. **Test all sites** with new category structure
