# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from threading import Thread
import re
#import requests
#import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, wait

# Import the common settings
from resources.lib.settings import Settings
from resources.lib.scraper import IMDBScraper
from resources.lib.settings import log
from resources.lib import cache
from resources.lib.SQLiteCache import SqliteCache
from resources.lib import imdb
from resources.lib.settings import log
from resources.lib.utils import logger
import requests
from bs4 import BeautifulSoup
import time
import datetime

db = SqliteCache()

import json

ADDON = xbmcaddon.Addon(id='script.parentalguide')
CWD = ADDON.getAddonInfo('path')#.decode("utf-8")

def getIsTvShow():
    if xbmc.getCondVisibility("Container.Content(tvshows)"):
        return True
    if xbmc.getCondVisibility("Container.Content(Seasons)"):
        return True
    if xbmc.getCondVisibility("Container.Content(Episodes)"):
        return True
    if xbmc.getInfoLabel("container.folderpath") == "videodb://tvshows/titles/":
        return True  # TvShowTitles

    return False

def setProperty(PropertyName, PropertyVal, WindowID):
    xbmcgui.Window(WindowID).setProperty(PropertyName, PropertyVal)
    logger.info(PropertyName + " was set sucessfully")
    
def Notify(title, msg):
    xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (title, msg , ADDON.getAddonInfo('icon')))

def CleanStr(txt):
    newtxt = txt.replace("<p>","").replace("</p>","").replace(";",".").replace("^","").replace("►\xa0","-").strip()
    return newtxt

def IMDB_Scraper(videoName, IMDBID, session):
    dataScraper = IMDBScraper.parentsguide(IMDBID, videoName)  
    
    return dataScraper
    
def ProvidersRouter(videoName,ID,Session, Provider):
    if Provider == 'IMDB':
        result = IMDB_Scraper(videoName,ID,Session)
    if Provider == 'MovieGuide':
        result = MovieGuideScraper(videoName,ID,Session)
    if Provider == 'CSM':
        result = CSMScraper(videoName,ID,Session)
    if Provider == "RaisingChildren":
        result = RaisingChildrenScraper(videoName,ID,Session)
    if Provider == 'DoveFoundation':
        result = DoveFoundationScraper(videoName,ID,Session)
    if Provider == 'KidsInMind':
        result = KidsInMindScraper(videoName,ID,Session)
    if Provider == 'ParentPreviews':
        result = ParentPreviewsScraper(videoName,ID,Session)
    return result
        
def getData(videoName, ID, Session, wid, Provider, order):
    try:
        RYear = int(xbmc.getInfoLabel("ListItem.Year"))
    except:
        RYear = 0 
        
    today = datetime.date.today()
    year = today.year
    
    try:
        if ID is not None:
            key = ID + "_" + Provider.lower()
        else:
            key = videoName.replace(":","").replace("-","_").replace(" ","_").lower()+ "_" + Provider.lower()
            
        show_info = db.get(key)
    except:
        logger.info("Failed to fetch from cache or cache not found")
        show_info = None
                
    if show_info is None: ##if not in cache
        logger.info('Loading from scratch, no cache found for [%s][%s]' % (videoName, Provider))
        show_info = ProvidersRouter(videoName,ID,Session, Provider)   
        
        if show_info is None:
            logger.info("No Results found for this movie (" + videoName + ") on [" + Provider + "]")
            Xshow_info = {
                        "id": ID,
                        "title": videoName,
                        "provider": Provider,
                        "recommended-age": None,
                        "review-items": None,
                        "review-link": None
                        }
            logger.info("Trying to save blank data for this movie (" + videoName + ") on [" + Provider + "]")
            db.set(Xshow_info, 1*24*60)
            AddFurnitureProperties(Xshow_info, Provider, wid)
        else:
            logger.info('Finished loading new data for [%s][%s] \n' % (videoName, Provider)+ str(show_info))
            # try:
                #cache.cache_details(show_info)
            AddXMLProperties(show_info,wid)
            AddFurnitureProperties(show_info, Provider, wid)
            
            if year == RYear:
                exp = 1*7*24*60*60
            elif year - RYear > 2:
                exp = 0
            else:
                exp = 30*7*24*60*60
                
            db.set(show_info, exp)
            logger.info("Added New Data for "+videoName + "[" + Provider +"] to cache sucessfully" )
    else:
        logger.info("Loading from cache : Cache found for " +videoName + "[" + Provider +"]\n"+ str(show_info))
        AddXMLProperties(show_info,wid)
        AddFurnitureProperties(show_info, Provider, wid)
        logger.info("Data from cache for "+videoName + "[" + Provider +"] \n")
    return show_info

#########################
# New Functions
#########################

def prepURL(videoName,Provider):
    #Notify(Provider)
    if Provider == 'CSM':
        movie_id = videoName.replace(":","").replace(" ","-")
        url = "https://www.commonsensemedia.org" + "/movie-reviews/" + str(movie_id)
    if Provider == 'MovieGuide':
        moviename = videoName.replace(":","").replace(" ","-").strip().lower()
        url = 'https://www.movieguide.org/reviews/' + moviename + '.html'
    if Provider == 'KidsInMind':
        videoName = videoName.replace(":", "%3A").replace(" ","+")
        url = 'https://kids-in-mind.com/search-desktop.htm?fwp_keyword=' + videoName
    if Provider == "RaisingChildren":
        if videoName[0:3] in ["The","THE","the"]:
            videoName = re.sub(".","",videoName, count=4)
        moviename = videoName.replace(":","").replace(" ","-").strip().lower()
        url = 'https://raisingchildren.net.au/guides/movie-reviews/' + moviename
    if Provider == 'DoveFoundation':
        url = 'https://dove.org/search/reviews/' + videoName.replace(":","%3A").replace(" ","+").replace("[","%5B").replace("]","%5").replace("(","%28").replace(")","%29")
    
    return url

def CSMScraper(videoName,ID,Session):
    CatsIDs = {
        0: "Clean",
        1: "Mild",
        2: "Moderate",
        3: "Moderate",
        4: "Severe",
        5: "Severe"
    }
    NamesMap = {
        "Positive Messages" :"Positive Messages",
        "Positive Role Models" :"Positive Role Models",
        "Diverse Representations" : "Diverse Representations",
        "Violence & Scariness" : "Violence",
        "Sex, Romance & Nudity" : "Sex & Nudity",
        "Language" : "Language",
        "Products & Purchases" : "Products & Purchases",
        "Drinking, Drugs & Smoking" : "Smoking, Alchohol & Drugs",
        "Educational Value":"Educational Value"
        }
    url = prepURL(videoName, 'CSM')
    response = Session.get(url)

    if '200' in str(response):
        soup = BeautifulSoup(response.text, "html.parser")
        
        if soup is not None:
            try:
                Cats = soup.find("review-view-content-grid").find("div",{"class":"row"}).findAll("span",{"class":"rating__label"})
                age = soup.find("div", {"class": "rating rating--inline rating--xlg"}).find("span", {"class":"rating__age"}).text.strip()
                title = soup.find("div",{"class":"review-view-summary"}).div.h1.string
                jsonData = soup.find('script',{"type":"application/ld+json"}).string
                print(jsonData)
                jsonload = json.loads(jsonData)
                imdburl= jsonload["@graph"][0]["itemReviewed"]["sameAs"]
                age2 = "age"+jsonload["@graph"][0]["typicalAgeRange"]
                isFamilyFriendly = "age"+jsonload["@graph"][0]["isFamilyFriendly"]
                datePublished = "age"+jsonload["@graph"][0]["datePublished"]
                sPattern3 = "http.*imdb.*title.(.*?)\/"
                imdbid = str(re.compile(sPattern3).findall(str(imdburl))).replace("[","").replace("]","").replace("'","")
                Details = []
                namePattern = re.compile(r'data-text="(.*\n*?)')
                CatData = []
                for cat in Cats:
                    try:
                        descparenttag = cat.parent.parent
                        desc = re.findall(namePattern,  str(descparenttag))[0].strip().replace("&lt;","").replace("p&gt;","").replace("&lt;","").replace("/p&gt","").replace("/","").replace("&quot;","'")
                        cparent = cat.parent
                        subs = cparent.findAll("span",{"class":"rating__score"})
                        for sub in subs:
                            try:
                                score = len(sub.findAll("i", {"class" : "icon-circle-solid active"}))
                                #print(score)
                                CatData = {
                                "name" : NamesMap[cat.text],
                                "score": str(score),
                                "description": CleanStr(desc),
                                "cat": CatsIDs[score],
                                "votes": None
                            }
                            except:
                                score = None
                        Details.append(CatData)
                    except:
                        pass
                Review = {
                    "id": imdbid,
                    "title": videoName,
                    "provider": "CSM",
                    "recommended-age": age,
                    "review-items": Details,
                    "review-link": url,
                    "isFamilyFriendly": isFamilyFriendly,
                    "review-date": datePublished
                    }
            except:
                log("Parental Guide [CSM] : Problem connecting to provider")
                Review = None
        else:
            log("Parental Guide [CSM] : Problem connecting to provider")
            Review = None

    else:
        log("Parental Guide [CSM] : Problem connecting to provider")
        Review = None
    return Review

def getIMDBID(name,year):
    k = "da6c8b4d"
    url = "http://www.omdbapi.com/?t=" + name.strip() +"&y=" + year + "&apikey=" + k +"&plot=full&r=json"
    res = requests.get(url).content
    json_object = json.loads(res)

    if json_object["Response"] != 'False':
        result = json_object["imdbID"]
    else:
        print("Couldn't find IMDB ID")
        result = None
    return result

def getMGDesc(descs, s):
    for i in range(0,len(descs)):
        if str(s) in [descs[i].text.replace(":","").strip()]:
            return CleanStr(descs[i].next_sibling.strip())
    
def MovieGuideScraper(videoName,ID,Session):
    url = prepURL(videoName, 'MovieGuide')
    
    r = Session.get(url)

    Cats = {
        0: "None",
        1: "Mild",
        2: "Moderate",
        3: "Severe"
    }

    NamesMap = {
    "Dominant Worldview and Other Worldview Content/Elements:": "Dominant Worldview",
    "Foul Language": "Language",
    "Language": "Language",
    "Violence" : "Violence",
    "Nudity" : "Nudity",
    "Sex": "Making Love",
    "Alcohol Use" : "Smoking, Alchohol & Drugs",
    "Smoking and/or Drug Use and Abuse" : "Smoking, & Alchohol & Drugs",
    "Miscellaneous Immorality" : "Miscellaneous Immorality"
    }

    ReNamesMap = {
        "Dominant Worldview": "Dominant Worldview and Other Worldview Content/Elements:",
        "Language": "Foul Language",
        "Violence": "Violence",
        "Nudity": "Nudity",
        "Sex": "Sex",
        "Smoking, Alchohol & Drugs": "Alcohol Use",
        "Miscellaneous Immorality" : "Miscellaneous Immorality"
        }
    
    Details, CatData = [], []

    if '200' in str(r):
        Soup = BeautifulSoup(r.text, "html.parser")
        descriptions = Soup.find("div",{"class":"movieguide_review_content"}).findAll("div",{"class":"movieguide_subheading"})
        title = Soup.title.text.replace("- Movieguide | Movie Reviews for Christians","").strip()
        #print(sSoup)
        classifications = Soup.find("table", {"class":"movieguide_content_summary"})
        matches = classifications.findAll("tr")
        #print(matches)
        for match in matches:
            #print(match.text)
            #if match.text.strip() in ["Nudity"]:
            if match.text.replace("\n","").strip() != 'NoneLightModerateHeavy':
                #print(match.text)
                ele = match.findAll("div")
                for i in range(0,4):
                    sPattern =  "movieguide_circle_red"
                    aMatches = re.compile(sPattern).findall(str(ele[i]))
                    sPattern2 =  "movieguide_circle_green"
                    bMatches = re.compile(sPattern2).findall(str(ele[i]))

                    if aMatches or bMatches:
                        CatData = {
                        "name" : NamesMap[str(match.text.replace("\n","").strip())],
                        "score": int(i),
                        "description": getMGDesc(descriptions, match.text.replace("\n","").strip()),
                        "cat": Cats[int(i)],
                        "votes": None
                        }
                    #print(CatData)
                Details.append(CatData)
                    #print(Cats[i])
                    #print("-------------------------------------------------------")

        #print(Details)

        Review = {
            "id": ID,
            "title": videoName,
            "provider": "MovieGuide",
            "recommended-age": None,
            "review-items": Details,
            "review-link": url
        }

        #logger.info(str(Review))
    else:
        Review = None
    return Review

def getDoveDesc(soup, s):
    descs = soup.findAll("h5",{"class":"details-title"})
    if descs not in [None,""]:
        for i in range(0,len(descs)):
            if str(s) in [descs[i].text.strip()]:
                parent = descs[i].parent
                text = parent.find("div",{"class":"details-body"}).p.string
                text = CleanStr(text)
            else:
                text = "None"
    else:
        text = "None"
    return text
    
def DoveFoundationScraper(videoName,ID,Session):
    url = prepURL(videoName, 'DoveFoundation')
    r = Session.get(url)
    Cats = {
        0: "None",
        1: "Mild",
        2: "Moderate",
        3: "Moderate",
        4: "Severe",
        5: "Severe"
    }
    Details, CatData = [], []

    if '200' in str(r):
        sSoup = BeautifulSoup(r.text, "html.parser")
        res = sSoup.find("div", {"class":"movie-cards search-cards"})
        NoRes = re.compile("Nothing matches your search term").findall(str(res))

        try:
            resURL = res.find("a")["href"]
            if len(NoRes) ==0:
                ## Sraping 1st rewsult
                response = Session.get(resURL)
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.text.replace("- Dove.org","").strip()
                
                checktitle = title.replace(":","").replace(" ","-")
                checkvideoName = videoName.replace(":","").replace(" ","-")

                if checktitle == checkvideoName:
                    table = soup.find("div", {"class":"matrix-categories"})
                    items = table.findAll("span",{"class":"item-text"})
                    sections = table.findAll("span",{"class":"categories-item"})
                    descs = soup.find("div",{"class": "main-content details-wrap"})
                    for i in range(0,len(items)):
                        try:
                            IDs = sections[i]["class"][1].replace("categories-item--","").strip()
                            CatData = {
                                "name" : items[i].text.strip(),
                                "score": IDs,
                                "description": getDoveDesc(descs, items[i].text.strip()),
                                "cat": Cats[int(IDs)],
                                "votes": None
                            }
                        except:
                            pass
                        Details.append(CatData)
                else:
                    print("No results found")
                    Details = None
            else:
                print("No results found")
                Details = None
            
            if ID is None:
                xID = title
            else:
                xID = ID
                
            Review = {
                "id": xID,
                "title": title,
                "provider": "DoveFoundation",
                "recommended-age": None,
                "review-items": Details,
                "review-link": resURL,
            }
        except:
            Review = None
    else:
        Review = None
    return Review

def KidsInMindScraper(videoName,ID,Session):
    url = prepURL(videoName, 'KidsInMind')
    r = Session.get(url)
    Cats = {
        0: "None",
        1: "Clean",
        2: "Mild",
        3: "Mild",
        4: "Mild",
        5: "Moderate",
        6: "Moderate",
        7: "Moderate",
        8: "Severe",
        9: "Severe",
        10: "Severe",
    }
    NamesMap = {
        "SEX/NUDITY" : "Sex & Nudity",
        "VIOLENCE/GORE": "Violence",
        "LANGUAGE":"Language",
        "SUBSTANCE USE":"Smoking, Alchohol & Drugs",
        "DISCUSSION TOPICS": "Discussion Topics",
        "MESSAGE":"Message",
    }
    AcceptedNames = ['SEX/NUDITY','VIOLENCE/GORE','LANGUAGE','SUBSTANCE USE','DISCUSSION TOPICS','MESSAGE']
    Details = []
    CatData = []
    sURLs = []
    if '200' in str(r):
        sSoup = BeautifulSoup(r.text, "html.parser")
        res = sSoup.find("div", {"class":"facetwp-template"})
        #resURL = res.find("a")["href"]
        sResults = res.findAll("a")

        for sRes in sResults:
            sURLs.append(sRes["href"])
            
        NoRes = re.compile("Nothing matches your search term").findall(str(res))

        if len(NoRes) ==0:
            for k in range(0,len(sURLs)-1):
                ## Sraping 1st result
                resURL = sURLs[k]
                response = Session.get(resURL)
                logger.info("KidsInMind trying .." + resURL)
                soup = BeautifulSoup(response.text, "html.parser")
                
                sPattern3 = "href.*imdb.*title.(.*?)\/"
                imdbid = str(re.compile(sPattern3).findall(str(soup)))
                
                if ID in imdbid:
                    logger.info("KidsInMind Found a match in the seach results .." + resURL)
                    try:    
                        title = soup.find("div",{"class":"title"}).h1.text.split("|")[0].strip()
                    except:
                        title = videoName
                    
                    
                    ratingstr = soup.title.string#.split("|")[0].split("-")[1].strip().split(".")[0] + "/10"
                    sPattern =  "(\d)\.(\d)\.(\d)"
                    aMatches = re.compile(sPattern).findall(ratingstr)
                    
                    try:
                        NudeRating = round(int(aMatches[0][0])/2)
                    except:
                        NudeRating = 0
                      
                    #print(title)
                    blocks = soup.findAll("div",{"class":"et_pb_text_inner"})
                    #print(blocks)
                    i=1
                    for block in blocks:
                        if block.p is not None and i <=7:
                            #print("New Block ............")
                            #print(block.p.text)
                            items = block.findAll("h2")
                            if len(items) < 1:
                                items = block.findAll("span")
                            #print(str(items))

                            for item in items:
                                #print("Processing : " + item.text + "from " + str(len(items)))
                                xitem = item.text.replace(title,"").strip()
                                itemtxt = ''.join((x for x in xitem if not x.isdigit())).strip()
                                if itemtxt in AcceptedNames:
                                    #print(xitem)
                                    #print(itemtxt)

                                    for x in xitem:
                                        if x.isdigit():
                                            ratetxt= int(''.join(x))
                                        else:
                                            ratetxt = 0
                                    parent = item.parent
                                    try:
                                        desc = parent.p.text
                                    except:
                                        desc = parent.text

                                    if block:
                                        CatData = {
                                                "name" : NamesMap[itemtxt],
                                                "score": int(ratetxt)/2,
                                                "description": desc,
                                                "cat": Cats[ratetxt],
                                                "votes": None
                                            }
                                        Details.append(CatData)
                            i = i +1
                    #print(Details)

                    Review = {
                        "id": imdbid.replace("['","").replace("']",""),
                        "title": videoName,
                        "provider": "KidsInMind",
                        "recommended-age": None,
                        "review-items": Details,
                        "review-link": resURL,
                    }
                    break
                else:
                    ## if not the same movie in this search result
                    Review = None
                    k = k + 1
        else:
            Review = None
    else:
        Review = None
    return Review
  
def RaisingChildrenScraper(videoName,ID,Session):
    url = prepURL(videoName, 'RaisingChildren')
    r = Session.get(url)

    Cats = {
        0: "None",
        1: "Mild",
        2: "Moderate",
        3: "Severe"
    }

    NamesMap = {
        "Sexual references": "Sex",
        "Alcohol, drugs and other substances": "Smoking, Alchohol & Drugs",
        "Nudity and sexual activity": "Nudity",
        "Product placement" : "Products & Purchases",
        "Coarse language": "Language",
        "Ideas to discuss with your children":"Discuss with children"
        }

    Details, CatData = [], []

    if '200' in str(r):
        sSoup = BeautifulSoup(r.text, "html.parser")
        title = sSoup.title.text.replace("| Raising Children Network","").strip()
        
        sPattern =  ".ageSuitability.:.(.*?).}"
        aMatches = re.compile(sPattern).findall(str(sSoup))
        age = "age " + aMatches[0]

        sPattern2 =  "<div.id..sexual_references,_etc_.*.>\n*.*\n*.*\n*.*\n*.*\n*.*\n*.*\n*.*"
        NewSoup = re.compile(sPattern2).findall(str(sSoup))

        fsoup = BeautifulSoup(str(NewSoup), "html.parser")
        items = fsoup.findAll("h2")

        for item in items:
            desc = item.nextSibling.text
            try:
                nextsib = item.nextSibling.nextSibling.text
                desc = desc + "\n" + nextsib
            except:
                pass

            CatData = {
            "name" : NamesMap[item.text],
            "score": "Unknown",
            "description": CleanStr(desc),
            "cat": "Unknown",
            "votes": None
            }
            Details.append(CatData)

        Review = {
            "id": ID,
            "title": videoName,
            "provider": "RaisingChildren",
            "recommended-age": age,
            "review-items": Details,
            "review-link": url,
        }
    else:
        Review = None
        logger.info("ParentalGuide [RaisingChildren] : Invalid Response")
    return Review

def ParentPreviewsScraper(videoName,ID,Session):
    strName = videoName.replace(":", "").replace(" ","-")
    url = 'https://parentpreviews.com/movie-reviews/' + strName
    r = Session.get(url)
    Cats = {
        "A": "None",
        "B": "Mild",
        "C": "Moderate",
        "D": "Severe"
    }
    
    Scores = {
        "A": 0,
        "B": 1,
        "C": 3,
        "D": 4
    }
    
    NamesMap = {
        "Sexual Content" : "Sex & Nudity",
        "Violence": "Violence",
        "Profanity":"Language",
        "Substance Use":"Smoking, Alchohol & Drugs"
    }

    Details, CatData, Reviews, cats = [] ,[], [] ,[]
    Review = {}

    namePattern = re.compile(r'<b>(.*?): ?<\/b>(.*?)[\n]')

    if '200' in str(r):
        Soup = BeautifulSoup(r.text, "html.parser")
        res = Soup.find("a", {"href":"#content-details"})
        if res is not None:
            blocks = res.findAll("div",{"class":"criteria_row theme_field"})
            DescSoup = Soup#.find("div",{"class":"post_text_area"})
            Desc = re.findall(namePattern,  str(DescSoup))

            for item in Desc:
                Review.update({item[0] : item[1]})

            for block in blocks:
                score = block.find("span", {"class":"criteria_mark theme_accent_bg"}).text.replace("-","").replace("+","").strip()

                try:
                    if Review[block.span.text.strip()]:
                        x = Review[block.span.text.strip()]
                    else:
                        x = ''
                except:
                    x = ''
                    pass

                CatData = {
                    "name" : NamesMap[block.span.text],
                    "score": Scores[block.find("span", {"class":"criteria_mark theme_accent_bg"}).text.replace("-","").replace("+","").strip()],
                    "description": x.replace("<p>","").replace("<br/>","").replace("</br>","").replace("</p>","").replace("<b>","").replace("</b>","").replace("<p>","").strip(),
                    "cat": Cats[score],
                    "votes": None
                    }

                Details.append(CatData)

            Review = {
                "id": ID,
                "title": videoName,
                "provider": "ParentPreviews",
                "recommended-age": '',
                "review-items": Details,
                "review-link": url,
            }
        else:
            Review = None
    else:
        Review = None
        logger.info("ParentalGuide [ParentPreviews] : Invalid Response")
    return Review


def AddXMLProperties(review, WindowID):    
    i = 0
    
    WID = xbmcgui.Window(WindowID)
    # if review['review-items'] is not None:
        # for item in review['review-items']:
            # y = i + 1
            # WID.setProperty("ParentalGuide.%s.Section" %y, review['review-items'][i]['name'])
            # WID.setProperty("ParentalGuide.%s.Desc" %y, review['review-items'][i]['description'])
            # WID.setProperty("ParentalGuide.%s.Score" %y, str(review['review-items'][i]['score']))
            # WID.setProperty("ParentalGuide.%s.Votes" %y, review['review-items'][i]['votes'])
            # WID.setProperty("ParentalGuide.%s.Cat" %y, review['review-items'][i]['cat'])
            # i = i+1
        #WID.setProperty("PG.Age".format(i), review['recommended-age'])
        #WID.setProperty("PG.URL".format(i), review['review-link'])
        #WID.setProperty("PG.Provider".format(i), review['provider'])

def AddFurnitureProperties(review, provider, WindowID):
    Suffix = provider
    WID = xbmcgui.Window(WindowID)
    name = xbmc.getInfoLabel("ListItem.Title")
    li = xbmcgui.ListItem(name)
    #WID = li
    #li.setProperty("PG","hi")
    
    #logger.info(li.getProperty("PG"))
    #Notify("res",li.getProperty("PG"))
    
    #q = {"jsonrpc":"2.0","id":15,"method":"Files.GetDirectory","params":{"directory":"plugin://script.parentalguide/", "media":"video", "properties":["genre","director"],"additionalProperties":["tmdb_id"]}}
    
    #xbmc.executeJSONRPC('{"jsonrpc": "2.0", "method": "Files.GetDirectory", "params": {"directory": "plugin://script.parentalguide/", "media":"video", "properties":["genre", "director"], "additionalProperties":["PG", "HI2"]}, "id": 1}')
    
    #Notify("res",WID.getProperty("PG"))
    WID.setProperty('CurrentItem',name)
    WID.setProperty('CurrentId',xbmc.getInfoLabel("ListItem.IMDBNumber"))
    
    WID.setProperty('PGFurnitureTitle',"Ratings: ")
    WID.setProperty('PGFurnitureIcon',"special://home/addons/script.parentalguide/resources/skins/Default/media/icons/icon.png")
    
    logger.info("Setting Property for %s" % provider)
    #logger.info("Trying Property for %s" % review)
    if review in [None,""," "]:
        WID.setProperty(Suffix+'-NRate', " NA")
        WID.setProperty(Suffix+'-NVotes', " NA")
        WID.setProperty(Suffix+'-Age', " NA")
        WID.setProperty(provider+'-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/Unknown.png")
        WID.clearProperty(provider+'-Status')
    else:
        WID.setProperty(provider+'-Icon', "special://home/addons/script.parentalguide/resources/skins/Default/media/providers/" + provider + ".png")
        WID.setProperty(provider+'-Status','true')
        if review['review-items'] not in [None,""," "]:
            if provider in ["CSM","RaisingChildren"]:
                WID.setProperty(Suffix+'-Age', Suffix+ ":"+review['recommended-age'])
                
            if provider in ["KidsInMind","IMDB","RaisingChildren","MovieGuide","DoveFoundation","ParentPreviews"]:
                for entry in review['review-items']:
                    if entry['name'] in ["Nudity","Sex & Nudity"]:
                        WID.setProperty(Suffix+'-toggle', "true")
                        WID.setProperty(Suffix+'-NRate', " " + entry['cat'] + " (" + str(entry['score']) + "/5)")
                        WID.setProperty(provider+'-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/"+ entry['cat'] +".png")
                        #"special://home/addons/script.parentalguide/resources/skins/Default/media/providers/" + provider + ".png")
                        if provider == "IMDB":
                            try:
                                xMainVotes = [int(s) for s in re.findall(r'\b\d+\b', entry['votes'])]
                                WID.setProperty(Suffix+'-NVotes', " " + (str(entry['cat']) + " (" + str(xMainVotes[0]) + "/" + str(xMainVotes[1]) + ")"))
                            except:
                                pass
                            #logger.info("Property Name = " + Suffix+'-NVotes' + ", Val = " + WID.getProperty(Suffix+'-NVotes'))
                            #Notify(Suffix+'-NVotes',WID.getProperty(Suffix+'-NVotes'))
                    if WID.getProperty(Suffix+'-NRate') in [None,""]:      
                        WID.setProperty(Suffix+'-NVotes', " NA")
                        WID.setProperty(Suffix+'-NRate', " NA")
                        WID.setProperty(Suffix+'-Age', " NA")
                        WID.setProperty(provider+'-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/Unknown.png")
        else:
            WID.setProperty(Suffix+'-NRate', " NA")
            WID.setProperty(Suffix+'-NVotes', " NA")
            WID.setProperty(Suffix+'-Age', " NA")
            WID.setProperty(provider+'-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/Unknown.png")
            WID.clearProperty(provider+'-Status')
    
    if review['review-items'] == []:
        WID.setProperty(Suffix+'-NRate', " NA")
        WID.setProperty(Suffix+'-NVotes', " NA")
        WID.setProperty(Suffix+'-Age', " NA")
        WID.setProperty(provider+'-NIcon', "special://home/addons/script.parentalguide/resources/skins/Default/media/tags/Unknown.png")
        WID.clearProperty(provider+'-Status')
    
#########################
# Main
#########################
if __name__ == '__main__':
    logger.info("ParentalGuide: Started")
    starttime = time.time()
    
    IMDBID = None
    IMDBID = xbmc.getInfoLabel("ListItem.IMDBNumber")
    year = xbmc.getInfoLabel("ListItem.Year")
    videoName = None
    isTvShow = getIsTvShow()
    s = requests.Session()
    wid = xbmcgui.getCurrentWindowId()
    order = -1
    ProvidersList, Threads, Results = [] , [], []

    # First check to see if we have a TV Show of a Movie
    if isTvShow:
        videoName = xbmc.getInfoLabel("ListItem.TVShowTitle")

    # If we do not have the title yet, get the default title
    if videoName in [None, ""]:
        videoName = xbmc.getInfoLabel("ListItem.Title")
        logger.info("ParentalGuide: Video Name detected %s" % videoName)
    
    if IMDBID in [None, ""]:
        logger.info("ParentalGuide: Video ID not found for %s, trying to loaded it from OMDB" % videoName)
        IMDBID = getIMDBID(videoName,year)
        
    if IMDBID not in [None, ""]:
        logger.info("ParentalGuide: Video ID detected %s" % IMDBID)
        
        if ADDON.getSetting("IMDBProvider")== "true":
            order = order + 1 
            ProvidersList.append("IMDB")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid,"IMDB", order)))
            Threads[order].start()
        
    if videoName not in [None, ""]:

        if ADDON.getSetting("kidsInMindProvider")== "true":
            order = order + 1 
            ProvidersList.append("KidsInMind")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "KidsInMind", order)))
            Threads[order].start()
        if ADDON.getSetting("movieGuideOrgProvider")== "true":
            order = order +1 
            ProvidersList.append("MovieGuide")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "MovieGuide", order)))
            Threads[order].start()
        if ADDON.getSetting("DoveFoundationProvider")== "true":
            order = order +1 
            ProvidersList.append("DoveFoundation")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "DoveFoundation", order)))
            Threads[order].start()
        if ADDON.getSetting("ParentPreviewsProvider")== "true":
            order = order +1 
            ProvidersList.append("ParentPreviews")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "ParentPreviews", order)))
            Threads[order].start()
        if ADDON.getSetting("RaisingChildrenProvider")== "true":
            order = order +1 
            ProvidersList.append("RaisingChildren")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "RaisingChildren", order)))
            Threads[order].start()
        if ADDON.getSetting("CSMProvider")== "true":
            order = order +1 
            ProvidersList.append("CSM")
            Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "CSM", order)))
            Threads[order].start()

            
        for i in range(0,len(Threads)):
            Threads[i].join()
            #logger.info(Threads[i].result)
            
        
        #logger.info(Results)
            
        
        # with ThreadPoolExecutor(max_workers=100) as p:
            # p.map(getData, [videoName]*(order-1), [IMDBID]*(order-1), [s]*(order-1), [wid]*(order-1), ProvidersList , [0,1,2,3,4,5,6])

        logger.info("ParentalGuide Finished in {s}s".format(s=time.time()-starttime))
        logger.info("InfoLabel: " + xbmc.getInfoLabel("ListItem.ParentalGuide"))
    else:
        log("ParentalGuide: Failed to detect selected video")
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("ParentalGuide", "Failed to detect a video" , ADDON.getAddonInfo('icon')))

    log("ParentalGuide: Ended")

#########################
# Main
#########################
# class ParentalGuideCore():
    # @staticmethod
    
    # def __init__(self,videoName, IMDBID):
        # logger.info("Initiaing ParentalGuideCore with %s %s" % (videoName, IMDBID))
        # if IMDBID not in [None, ""]:
            # log("ParentalGuide: Video detected %s" % IMDBID)
            
            # if ADDON.getSetting("IMDBProvider")== "true":
                # order = order + 1 
                # ProvidersList.append("IMDB")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid,"IMDB", order)))
                # Threads[order].start()
            
        # if videoName not in [None, ""]:

            # if ADDON.getSetting("kidsInMindProvider")== "true":
                # order = order + 1 
                # ProvidersList.append("KidsInMind")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "KidsInMind", order)))
                # Threads[order].start()
            # if ADDON.getSetting("movieGuideOrgProvider")== "true":
                # order = order +1 
                # ProvidersList.append("MovieGuide")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "MovieGuide", order)))
                # Threads[order].start()
            # if ADDON.getSetting("DoveFoundationProvider")== "true":
                # order = order +1 
                # ProvidersList.append("DoveFoundation")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "DoveFoundation", order)))
                # Threads[order].start()
            # if ADDON.getSetting("RaisingChildrenProvider")== "true":
                # order = order +1 
                # ProvidersList.append("RaisingChildren")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "RaisingChildren", order)))
                # Threads[order].start()
            # if ADDON.getSetting("CSMProvider")== "true":
                # order = order +1 
                # ProvidersList.append("CSM")
                # Threads.append(Thread(target = getData(videoName, IMDBID, s, wid, "CSM", order)))
                # Threads[order].start()
                
            # # for i in range(0,len(Threads)):
                # # Threads[i].start()
                
            # for i in range(0,len(Threads)):
                # Threads[i].join()
                
            # logger.info(Threads[order].result())
        # return Threads[order].result()
