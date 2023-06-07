# -*- coding: utf-8 -*-
#import requests
import xml.etree.ElementTree as ET
import urllib.request
#from urllib import request
from urllib.request import Request, urlopen
import urllib.response
import urllib.parse
from bs4 import BeautifulSoup
import re
import requests
import time
import sys
import xbmc
import xbmcaddon
import xbmcgui
import traceback
from collections import namedtuple
import unicodedata
from html.parser import HTMLParser
# from resources.lib.importlib_metadata.importlib_metadata import *
# from resources.lib.importlib_metadata.importlib_metadata import metadata
# from resources.lib.zipp import *
# from resources.lib.zipp import zipp
# from resources.lib.zipp.zipp import *
# from resources.lib.twine import *
# from resources.lib.wheel import *
# from resources.lib.sniffio import *
# from resources.lib import httpx
from resources.lib.imdb import *
from resources.lib.imdb import imdb_parentsguide

# Import the common settings
from resources.lib.settings import log

ADDON = xbmcaddon.Addon(id='script.parentalguide')

#################################
# Core Scraper class
#################################
class Scrapper():
    def __init__(self, videoName, IMDBID, isTvShow=False):
        self.videoTitle = str(videoName)
        self.isTvShow = isTvShow
        self.IMDBID  = IMDBID
        start_time = time.time()

    def getSelection(self):
        return []

    def getParentalGuideData(self):
        return []

    def _findBetween(self, s, first, last):
        textBlock = s
        try:
            textBlock = s.decode("utf-8")
        except:
            textBlock = s
        try:
            start = textBlock.index(first) + len(first)
            end = textBlock.index(last, start)
            return textBlock[start:end]
        except ValueError:
            return ""
 
            
    def _getHtmlSource(self, url):
        import requests
        #from resources.lib import httpx
        
        with requests.Session() as s:
            client = s.get(url)
        
        
        # with httpx.Client() as hs:
            # client = hs.get(url)
            
    
        
        doc = client.text
        webpage = doc#.decode('utf-8')
        log("Scrapper: Retrieved page: %s" % webpage)
        log("Scrapper: Page Link: %s" % url)
        client.close()
        end_time = time.time()
        return webpage
       
    
    def _narrowDownSearch(self, searchMatches):
        betterMatches = []
        for searchMatch in searchMatches:
            # Check if the whole name as an exact match is in the list
            x = self.videoTitle.lower()
            y = searchMatch["name"].lower()
            
            if x in y:
                betterMatches.append(searchMatch)
                log("Scrapper: Best Match: %s {%s}" % (searchMatch["name"], searchMatch["link"]))
                
        if len(betterMatches) > 0:
            searchMatches = []
            # If there are multiple exact matches, then we want the smallest one as
            # that will be a better match, as sequels will often just append a number
            currentMaxSize = None
            for aMatch in betterMatches:
                if len(searchMatches) < 1:
                    searchMatches = [aMatch]
                    currentMaxSize = len(aMatch["name"])
                elif len(aMatch["name"]) < currentMaxSize:
                    searchMatches = [aMatch]
                # If the size is the same, then we need to display this as well
                elif len(aMatch["name"]) == currentMaxSize:
                    searchMatches.append(str(aMatch))

        return searchMatches

    # Get the text for a given chapter
    def _convertHtmlIntoKodiText(self, htmlText):
        plainText = htmlText.replace('<', ' <')
        plainText = plainText.replace('>', '> ')
        # Replace the bold tags
        plainText = plainText.replace('<b>', '[B]')
        plainText = plainText.replace('</b>', '[/B]')
        plainText = plainText.replace('<B>', '[B]')
        plainText = plainText.replace('</B>', '[/B]')
        # Replace italic tags
        plainText = plainText.replace('<i>', '[I]')
        plainText = plainText.replace('</i>', '[/I]')
        plainText = plainText.replace('<I>', '[I]')
        plainText = plainText.replace('</I>', '[/I]')
        # Add an extra line for paragraphs
        plainText = plainText.replace('</p>', '</p>\n')
        # The html &nbsp; is not handle s well by ElementTree, so replace
        # it with a space before we start
        plainText = plainText.replace('&nbsp;', ' ')

        try:
            plainText = ''.join(ET.fromstring(plainText).itertext())
        except:
            try:
                plainText = ''.join(ET.fromstring(plainText.decode('utf-8', 'ignore').encode('ascii', 'ignore')).itertext())
            except:
                try:
                    log("Scrapper: Failed to strip html text with ElementTree, error: %s" % traceback.format_exc())
                    log("Scrapper: Using regex for content handling (with encoding)")
                    plainText = re.sub(r'<[^>]+>', '', plainText.decode('utf-8', 'ignore').encode('ascii', 'ignore'))
                except:
                    try:
                        log("Scrapper: Unable to process as plain text with regex, try without encoding")
                        plainText = re.sub(r'<[^>]+>', '', plainText)
                    except:
                        log("Scrapper: Failed to process with re-encoding %s" % traceback.format_exc())

        # Replace any quotes or other escape characters
        plainText = plainText.replace('&quote;', '"')
        plainText = plainText.replace('&nbsp;', ' ')
        plainText = plainText.replace('&#039;', "'")
        plainText = plainText.replace('&#8217;', "'")
        plainText = plainText.replace('&amp;', '&')

        # Need to remove double tags as they are not handled very well when
        # displayed, they do not get nested, so the first end will close all
        # instances of this tag
        plainText = plainText.replace('[B][B]', '[B]')
        plainText = plainText.replace('[/B][/B]', '[/B]')
        plainText = plainText.replace('[I][I]', '[I]')
        plainText = plainText.replace('[/I][/I]', '[/I]')

        # Remove empty space between tags, where there is no content
        plainText = re.sub("\[B]\s*\[/B]", "", plainText)
        plainText = re.sub("\[I\]\s*\[/I\]", "", plainText)

        # Remove blank lines at the start of the text
        plainText = plainText.lstrip('\n')
        plainText = plainText.lstrip(' ')

        # Remove extra white space
        plainText = re.sub('\s\s+', ' ', plainText)

        return plainText

    # Get the details in a format to be displayed in kodi
    def getTextView(self, fullDetails):
        displayContent = ""

        parentsAge = fullDetails.get("parentsAge", None)
        if parentsAge not in [None, ""]:
            displayContent = "%s[B]Parents Say:[/B] %s\n" % (displayContent, parentsAge)
            log("ParentalGuide: parentsAge: %s" % parentsAge)

        childsAge = fullDetails.get("childsAge", None)
        if childsAge not in [None, ""]:
            displayContent = "%s[B]Children Say:[/B] %s\n" % (displayContent, childsAge)
            log("ParentalGuide: childsAge: %s" % childsAge)

        summary = fullDetails.get("summary", None)
        if summary not in [None, ""]:
            displayContent = "%s[B]Summary:[/B] %s\n" % (displayContent, summary)
            log("ParentalGuide: Summary: %s" % summary)

        overview = fullDetails.get("overview", None)
        if overview not in [None, ""]:
            overview = self._convertHtmlIntoKodiText(overview)
            if len(displayContent) > 0:
                displayContent = "%s\n" % displayContent
            displayContent = "%s[B]Overview[/B]\n%s\n" % (displayContent, overview)
            log("ParentalGuide: Overview: %s" % overview)

        if len(displayContent) > 0:
            displayContent = "%s\n" % displayContent

        log("ParentalGuide: ******************************")
        for detail in fullDetails["details"]:
            log("ParentalGuide: Overview: %s" % detail)
            displayContent = "%s[B]%s - %d/10[/B]\n" % (displayContent, detail["name"], detail["score"])
            log("ParentalGuide: %s - %d/10" % (detail["name"], detail["score"]))
            if detail["description"] not in [None, ""]:
                displayContent = "%s%s\n\n" % (displayContent, detail["description"])
                log("ParentalGuide: %s" % detail["description"])
            log("ParentalGuide: ******************************")

            #displayContent = "%s[B]%s - %d/10[/B]\n" % (displayContent)
            #log("ParentalGuide: %s - %d/10" % (fullDetails["score"]))
            #if fullDetails["description"] not in [None, ""]:
            #    displayContent = "%s%s\n\n" % (displayContent, fullDetails["description"])
            #    log("ParentalGuide: %s" % fullDetails["description"])
                
        return displayContent


#################################
# Kids In Mind Scraper class
#################################
class KidsInMindScraper(Scrapper):
    ADDON = xbmcaddon.Addon(id='script.parentalguide')
    def getSelection(self, narrowSearch=True):
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("KidsInMind", "Scraping Results...", ADDON.getAddonInfo('icon')))
        # Generate the URL and get the page
        search_url = "https://kids-in-mind.com/search-desktop.htm?fwp_keyword="
        media_name = self.videoTitle
        IMDBID = self.IMDBID
        url = search_url+media_name.lower().replace(" ","+")
        html = self._getHtmlSource(url)
        if html in [None, ""]:
            return []
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # findAll('p', {"style": "font-family: Verdana; font-size: 11px; line-height:19px"})
        className = 'fwpl-layout el-e13muvi sidebar'
        searchResults = soup.findAll('div', {"class": className.split() if '  ' in className else className})
        OrgResultsCount = len(searchResults)
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (IMDBID, "IMDB ID", ADDON.getAddonInfo('icon')))
        searchMatches = []
        
        # Check each of the entries found
        for entries in searchResults:
            entrylist = entries.find('a') 
            videoUrl = entrylist['href']
            videoName = self._convertHtmlIntoKodiText(entrylist.string)
            searchMatches.append({"name": str(videoName), "link": str(videoUrl)})
            log("KidsInMindScraper: Initial Search Match: %s {%s}" % (videoName, videoUrl))
            
            # for link in entrylist:
                ##Get the link
                # videoName = self._convertHtmlIntoKodiText(link.string)
                # videoUrl = entrylist[0]
                # searchMatches.append({"name": str(videoName), "link": str(videoUrl)})
                # log("KidsInMindScraper: Initial Search Match: %s {%s}" % (videoName, videoUrl))

        # The kids in mind search can often return lots of entries that do not
        # contain the words in the requested video, so we can try and narrow it down
        if narrowSearch:
            searchMatches = self._narrowDownSearch(searchMatches)
            msg = str(len(searchResults)) + " Out of " + str(OrgResultsCount) + " Found"
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ( "Results Narrowed down to", str(msg), ADDON.getAddonInfo('icon')))
        return searchMatches
        
    def getDescription(self, Cat, cl):
      ChildCat = self.Cat
      className = self.cl
      Parent = soup.find('div', {'class' : className.split() if '  ' in className else className})
      #1st Child
      p = soup.find("h2", {"id": ChildCat})
      Descls = []
      FirstChild = p.find_next_sibling("p")
      #Other Childs Span
      OtherChilds = FirstChild.children
      Descls.append (str(FirstChild.text.replace("\xa0","").replace("_", " ").replace("<br>","")))
      Desc = ''
      for row in Descls:
          Desc += '\n' + str(row)
      return Desc
      
    def getParentalGuideData(self, videoUrl):
        html = self._getHtmlSource(videoUrl)
        if html in [None, ""]:
            return None
    
        soup = BeautifulSoup(html, "html.parser")
        rating = soup.find("span", {"style" : "font-size:14px !important"}).text

        #Nudity Desc  
        className = 'et_pb_module et_pb_text et_pb_text_3 review  et_pb_text_align_left et_pb_bg_layout_light'
        Parent = soup.find('div', {'class' : className.split() if '  ' in className else className})
        
        try:
          #1st Child
          p = soup.find("h2", {"id": "sex" })
          FirstChild = p.find_next_sibling("p")
          #Other Childs Span
          OtherChilds = FirstChild.children
        except:
          Soup2 = soup.find_all('span')
          # xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("span except :", str(soup2), ADDON.getAddonInfo('icon')))
          text = 'SEX/NUDITY 1'
          for i in Soup2:
            if (i.string ==text):
              FirstChild = i.find_next_sibling.text
              xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("found i  :", str(FirstChild), ADDON.getAddonInfo('icon')))
       
        
        NudityDescls = []
        NudityDescls.append (str(FirstChild.text.replace("\xa0","").replace("_", " ").replace("<br>","").replace('-','')))
        NudityDesc = ''
        for row in NudityDescls:
            NudityDesc += '\n' + str(row.strip().replace('-',''))
            
        #Language Desc 
        className = 'et_pb_module et_pb_text et_pb_text_5 review  et_pb_text_align_left et_pb_bg_layout_light'
        Parent = soup.find('div', {'class' : className.split() if '  ' in className else className})
        #1st Child
        p = soup.find("h2", {"id": "language" })
        LanguageDescls = []
        FirstChild = p.find_next_sibling("p")
        #Other Childs Span
        OtherChilds = FirstChild.children
        LanguageDescls.append (str(FirstChild.text.replace("\xa0","").replace("_", " ").replace("<br>","").replace('-','')))
        LanguageDesc = ''
        for row in LanguageDescls:
            LanguageDesc += '\n' + str(row.strip().replace('-',''))
            
        #Violence Desc  
        className = 'et_pb_module et_pb_text et_pb_text_4 review  et_pb_text_align_left et_pb_bg_layout_light'
        Parent = soup.find('div', {'class' : className.split() if '  ' in className else className})
        #1st Child
        p = soup.find("h2", {"id": "violence" })
        ViolenceDescls = []
        FirstChild = p.find_next_sibling("p")
        #Other Childs Span
        OtherChilds = FirstChild.children
        ViolenceDescls.append (str(FirstChild.text.replace("\xa0","").replace("_", " ").replace("<br>","").replace('-','')))
        ViolenceDesc = ''
        for row in ViolenceDescls:
            ViolenceDesc += '\n' + str(row.strip().replace('-',''))         
            
        # for tag in OtherChilds:
            # NudityDescls.append (str(tag).replace("\xa0","").replace("_", " ").replace("<br>",""))
        
        rating = rating[len(rating)-8:]
        rating = rating.replace('|','').replace('–','').replace('-','').replace('_','').replace(' ','').strip()
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("Rating :", rating, ADDON.getAddonInfo('icon')))
        log(rating)
        data = []
        data = rating.split('.')
        #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("Data :", data[0], ADDON.getAddonInfo('icon')))

        Cats = {
            '0' : 'Clean',
            '1' : 'Mild',
            '2' : 'Mild',
            '3' : 'Moderate',
            '4' : 'Moderate',
            '5' : 'Severe',
            '6' : 'Severe',
            '7' : 'Severe',
            '8' : 'Severe',
            '9' : 'Severe',
            '10' : 'Severe'
            }
            
        Response = {
            'NudityRate': data[0],
            'NudityCat': Cats[data[0]],
            'ViolenceRate': data[1],
            'ViolenceCat': Cats[data[1]],
            'LanguageRate': data[2],
            'LanguageCat': Cats[data[2]],
            'NDesc': NudityDesc,
            'VDesc': ViolenceDesc,
            'LDesc': LanguageDesc
            }

        details = []
        details.append({"provider": "KidsInMind", "name": "Nudity", "score": int(Response['NudityRate']), "description": Response['NDesc'], "Cat": Response['NudityCat']})
        details.append({"provider": "KidsInMind", "name": "Violence", "score": int(Response['ViolenceRate']), "description": Response['VDesc'], "Cat": Response['ViolenceCat']})
        details.append({"provider": "KidsInMind", "name": "Language", "score": int(Response['LanguageRate']), "description": Response['LDesc'], "Cat": Response['LanguageCat']})

        fullDetails = {}
        fullDetails["title"] = str(self.videoTitle)
        fullDetails["details"] = details

        return fullDetails


      
#################################
# imdb class
#################################
class IMDBScraper(Scrapper):
    def parentsguide(IMDBID, videoName):
        details = imdb_parentsguide(IMDBID)
        # CatCount = len(Desc[0])
        # i = 0
        # details = []
        # listingstr = ''
        
        # for i in range(0,CatCount):
          # item = Desc[0][i]
          
          # listingitem = item['listings']
          # #xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (item['title'],str(item['votes']), ADDON.getAddonInfo('icon')))
          # for row in listingitem:
            # listingstr += '\n' + str(row.strip().replace('-',''))
          # details.append({
                # "name": item['title'].replace(",",""),
                # "score": "",
                # "description": listingstr,
                # "cat": item['ranking'],
                # "votes" : item['votes']
                # })
        
        Review = {
            "id": IMDBID,
            "title": videoName,
            "provider": "imdb",
            "recommended-age": None,
            "review-items": details,
            "review-link": f'https://www.imdb.com/title/{IMDBID}/parentalguide',
        }
        
        return Review

#################################
# Dove Foundation Scraper class
#################################
class DoveFoundationScraper(Scrapper):
    def getSelection(self, narrowSearch=True):
        # Generate the URL and get the page
        search_url = "https://www.dove.org/?s=%s"
        url = str(search_url % urllib.parse.quote_plus(self.videoTitle))
        html = self._getHtmlSource(url)
        if html in [None, ""]:
            return []

        soup = BeautifulSoup(html, "html.parser")

        searchResults = soup.findAll('h1', {"class": "entry-title"})

        searchMatches = []

        # Check each of the entries found
        for entries in searchResults:
            for link in entries.findAll('a'):
                # Get the link
                videoName = self._convertHtmlIntoKodiText(link.string)
                videoUrl = link['href']
                searchMatches.append({"name": str(videoName), "link": str(videoUrl)})
                log("DoveFoundationScraper: Initial Search Match: %s {%s}" % (videoName, videoUrl))

        # The kids in mind search can often return lots of entries that do not
        # contain the words in the requested video, so we can try and narrow it down
        if narrowSearch:
            searchMatches = self._narrowDownSearch(searchMatches)

        return searchMatches

    def getParentalGuideData(self, videoUrl):
        html = self._getHtmlSource(videoUrl)
        if html in [None, ""]:
            return None

        soup = BeautifulSoup(html, "html.parser")

        ratingChart = soup.find('div', {"class": "rating-chart"})

        details = []

        if ratingChart is not None:
            # Get all the rating entries
            imgEntries = ratingChart.findAll('img')

            for img in imgEntries:
                # Get the rating based off of the image used
                srcImg = img.get('src', None)
                # Skip anything that doesn't have an image
                if srcImg in [None, ""]:
                    continue
                # Calculate the score using the name of the image
                score = -1
                if srcImg.endswith("/g0.jpg"):
                    score = 0
                elif srcImg.endswith("/g1.jpg"):
                    score = 2
                elif srcImg.endswith("/g2.jpg"):
                    score = 4
                elif srcImg.endswith("/g3.jpg"):
                    score = 6
                elif srcImg.endswith("/g4.jpg"):
                    score = 8
                elif srcImg.endswith("/g5.jpg"):
                    score = 10
                else:
                    continue

                # Get the name of the rating type
                name = img.get('alt', None)
                if name in [None, ""]:
                    continue

                # Get the text description of each rating
                description = img.get('title', None)
                if description not in [None, ""]:
                    removeSection = "<b>%s: </b>" % name
                    if removeSection in description:
                        description = description.replace(removeSection, "")
                    else:
                        # If it is a 2 word name the key is just the first word
                        if " " in name:
                            removeSection = "<b>%s: </b>" % name.split(" ")[0]
                            description = description.replace(removeSection, "")

                details.append({"name": name, "score": score, "description": description})

        fullDetails = {}
        fullDetails["details"] = details

        # Get the summary
        approvalText = soup.find('div', {"class": "approved-text"})
        if approvalText not in [None, ""]:
            fullDetails["summary"] = approvalText.getText()
            print (str(fullDetails["summary"]))

        return fullDetails


#################################
# Movie Guide Org Scraper class
#################################
class MovieGuideOrgScraper(Scrapper):
    def getSelection(self, narrowSearch=True):
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ("", "MovieGuideOrg is running", ADDON.getAddonInfo('icon')))
        # Generate the URL and get the page
        search_url = "https://www.movieguide.org/?s=%s"
        url = str(search_url % urllib.parse.quote_plus(self.videoTitle))
        html = self._getHtmlSource(url)
        if html in [None, ""]:
            return []

        soup = BeautifulSoup(html, "html.parser")

        searchResults = soup.findAll('h2')
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % (len(searchResults), " Results Found", ADDON.getAddonInfo('icon')))
        searchMatches = []

        # Check each of the entries found
        for entries in searchResults:
            for link in entries.findAll('a'):
                # Get the link
                videoName = self._convertHtmlIntoKodiText(link.string)
                try:
                    videoName = videoName.encode('ascii', 'ignore')
                except:
                    pass
                videoUrl = link['href']
                searchMatches.append({"name": str(videoName), "link": str(videoUrl)})
                log("MovieGuideOrgScraper: Initial Search Match: %s {%s}" % (videoName, videoUrl))

        # The kids in mind search can often return lots of entries that do not
        # contain the words in the requested video, so we can try and narrow it down
        if narrowSearch:
            searchMatches = self._narrowDownSearch(searchMatches)
        xbmc.executebuiltin('Notification(%s,%s,3000,%s)' % ( "Results Narrowed down to", len(searchResults), ADDON.getAddonInfo('icon')))
        return searchMatches

    def getParentalGuideData(self, videoUrl):
        html = self._getHtmlSource(videoUrl)
        if html in [None, ""]:
            return None

        soup = BeautifulSoup(html, "html.parser")

        ratingTable = soup.find('table', {"class": "content-qual-tbl"})
        if ratingTable in [None, '']:
            ratingTable = soup.find('table', {"class": "movieguide_content_summary"})

        details = []

        if ratingTable is not None:
            # Get all the rows in the table
            tableRows = ratingTable.findAll('tr')

            for row in tableRows:
                # Get the title of the row
                ratingTitle = row.find('td', {"class": "param-cell"})
                if ratingTitle in [None, ""]:
                    ratingTitle = row.find('td')

                if ratingTitle not in [None, ""]:
                    # Now we have the section title work out what the rating is
                    dtEntries = row.findAll('td')
                    rating = 0
                    ratingCount = 0
                    for entry in dtEntries:
                        if entry != ratingTitle:
                            # Check for the case where there is none
                            if ("circle-green" in str(entry)) or ("movieguide_circle_green" in str(entry)):
                                rating = ratingCount
                                break
                            ratingCount = ratingCount + 1
                            # Bad entries are marked with red
                            if ("circle-red" in str(entry)) or ("movieguide_circle_red" in str(entry)):
                                rating = ratingCount
                                break
                    # convert the ratings into an out-of-10 score
                    if rating == 2:
                        rating = 3
                    elif rating == 3:
                        rating = 6
                    elif rating == 4:
                        rating = 10
                    details.append({"name": ratingTitle.string, "score": rating, "description": ""})

        fullDetails = {}
        fullDetails["title"] = str(self.videoTitle)
        fullDetails["details"] = details

        # Now get the details about the video
        contentHeader = soup.find('div', {"class": "content-qual-header"})

        if contentHeader is not None:
            summarySection = contentHeader.find('div', {"class": "content"})
            if summarySection is not None:
                category = summarySection.find('strong', {"style": "color:#545454;"})
                if category is not None:
                    fullDetails["summary"] = category.getText().strip()
                    if summarySection.get('title', None) not in [None, ""]:
                        fullDetails["summary"] = "%s - %s " % (fullDetails["summary"], summarySection['title'])
                        log("MovieGuideOrgScraper: Summary details = %s" % fullDetails["summary"])
        else:
            summarySection = soup.find('div', {"class": "movieguide_review_section movieguide_review_summary"})
            if summarySection is not None:
                fullDetails["summary"] = summarySection.getText().strip()

        # Now get the text description
        contentBreakdown = soup.find('div', {"class": "content_content"})

        if contentBreakdown in [None, ""]:
            contentBreakdown = soup.find('div', {"class": "movieguide_review_section movieguide_review_content"})

        if contentBreakdown is not None:
            content = contentBreakdown.string
            if content in [None, ""]:
                content = str(contentBreakdown)
            if content not in [None, ""]:
                if content.startswith("CONTENT:"):
                    content = content[8:]
                try:
                    content = content.encode('utf-8', 'ignore')
                except:
                    pass
                try:
                    content = content.decode('utf-8', 'ignore')
                except:
                    pass
                fullDetails["overview"] = content.strip()



        Response = {
            'NudityRate': data[0],
            'ViolenceRate': data[1],
            'LanguageRate': data[2],
            'NDesc': NudityDesc,
            'VDesc': ViolenceDesc,
            'LDesc': LanguageDesc
            }

        details = []
        details.append({"name": "Nudity", "score": int(Response['NudityRate']), "description": Response['NDesc']})
        details.append({"name": "Violence", "score": int(Response['ViolenceRate']), "description": Response['VDesc']})
        details.append({"name": "Language", "score": int(Response['LanguageRate']), "description": Response['LDesc']})

        fullDetails = {}
        fullDetails["title"] = str(self.videoTitle)
        fullDetails["details"] = details
        
        return fullDetails
