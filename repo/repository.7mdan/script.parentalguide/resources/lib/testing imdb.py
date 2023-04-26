#-------------------------------------------------------------------------------
# Name:        module3
# Purpose:
#
# Author:      MHamdan
#
# Created:     16/02/2023
# Copyright:   (c) MHamdan 2023
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import cache
#from scraper import IMDBScraper

IMDBID = "tt11138512"
show_info = cache.load_cache(IMDBID)

if show_info is None:
    print('no cache file found, loading from scratch')
    dataScraper = {
    "id": IMDBID,
    "title": "test",
    "provider": "imdb",
    "recommended-age": "15",
    "review-items": {"name":"Nudity", "score":"1"},
    "review-link": "httttttttttp",
}


    show_info = dataScraper

    print("Fetching new data.....")
    print(str(show_info))
    cache.cache_details(show_info)
else:
    print("cash found \n" + str(show_info))