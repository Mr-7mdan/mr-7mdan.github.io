# Professional Icon Pack for 3rbi Kodi Addon

## Design System

**Background:** Navy blue (#1e3a5f)
**Main Icons:** White (#FFFFFF)
**Cultural Symbols:** Dark yellow (#F5A623)
**Text:** White (#FFFFFF), 56px, Arial Bold

## Design Rules

1. **Flat navy background** - No gradients, solid #1e3a5f
2. **No circles** - Rectangular/organic shapes only
3. **Simple, modern, flat** - Minimalist design approach
4. **White symbols and text** - High contrast for readability
5. **Cultural symbols in dark yellow** - Positioned in top right corner
6. **Consistent text placement** - All text at y=420, font-size 56px
7. **Proper spacing** - Icon ends around y=330, text starts at y=420
8. **Single-line text** - No text wrapping
9. **English text only** - Clear, professional labels

## Icons Created

### Movies
- ✅ Movies.svg - Generic film reel
- ✅ MoviesArabic.svg - Film reel + crescent moon (yellow)
- ✅ MoviesEnglish.svg - Film reel + Big Ben (yellow)
- ✅ MoviesTurkish.svg - Film reel + crescent & star (yellow)
- ✅ MoviesHindi.svg - Film reel + Taj Mahal (yellow)
- ✅ MoviesAsian.svg - Film reel + pagoda (yellow)
- ✅ MoviesAnime.svg - Film reel + anime eyes (yellow)
- ✅ MoviesCartoon.svg - Film reel + balloon (yellow)
- ✅ MoviesDocumentary.svg - Film reel + camera (yellow)

### TV Shows
- ✅ TVShows.svg - Generic TV with play button
- ✅ TVShowsArabic.svg - TV + crescent moon (yellow)
- ✅ TVShowsEnglish.svg - TV + Big Ben (yellow)
- ✅ TVShowsTurkish.svg - TV + crescent & star (yellow)
- ✅ TVShowsKorean.svg - TV + Taeguk symbol (yellow)

### Other
- ✅ Search.svg - Magnifying glass
- ✅ Programs.svg - Microphone
- ✅ Ramadan.svg - Large crescent & star
- ✅ LiveTV.svg - TV with antenna waves
- ✅ WWE.svg - Wrestling ring + championship belt (yellow)

## Still Needed

Based on category_mapper.py, these icons still need to be created:
- MoviesAsian-Dubbed.svg
- MoviesCarton.svg (note: different from Cartoon)
- MoviesKorean.svg
- MoviesPakistani.svg
- MoviesLatin.svg
- TVShowsHindi.svg
- TVShowsAsian.svg
- TVShowsPakistani.svg
- Chinese.svg
- Japanese.svg
- Thai.svg
- Cartoon.svg (for TV Shows)
- Theater.svg
- News.svg (for Recently Added)

## Converting to PNG

Once all SVG files are created, bulk convert to PNG at 512x512:

```bash
# Using ImageMagick
for file in *.svg; do
  convert -background none -density 300 "$file" -resize 512x512 "${file%.svg}.png"
done

# Or using Inkscape
for file in *.svg; do
  inkscape "$file" --export-type=png --export-width=512 --export-height=512
done
```

## Cultural Symbols Reference

- **Arabic/Middle East:** Crescent moon
- **Turkey:** Crescent moon + star
- **India:** Taj Mahal dome
- **Asia (General):** Pagoda
- **Japan/Anime:** Anime-style eyes
- **UK/English:** Big Ben tower
- **Korea:** Taeguk (yin-yang)
- **Cartoon:** Balloon
- **Documentary:** Video camera
- **WWE:** Championship belt
