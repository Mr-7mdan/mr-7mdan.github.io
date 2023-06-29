import requests
import re
from bs4 import BeautifulSoup

def get_scenes(section):
    scenes_raw = section.find_all('li', class_='ipl-zebra-list__item')
    scenes = list()
    for scene in scenes_raw:
        scene = scene.text.replace('\n', '')
        scene = scene.replace('     Edit    ', '')
        scene = scene.replace('                        ', '')
        scenes.append(scene)
    return scenes

def get_cat(section):
    vote_container = section.find(class_='ipl-swapper__content-primary')
    if vote_container:
        vote_container = vote_container.find(class_='advisory-severity-vote__container')
    else:
        return None, None, None, None
    # cat vote examples:
    # 45 of 59 found this to have none
    # 22 of 43 found this mild
    # 32 of 46 found this moderate
    # 241 of 320 found this severe
    if vote_container not in ["",None]:
        try:
            cat = vote_container.find('span').text
            vote = vote_container.find('a').text
            pattern = '([\d,]+)\sof\s([\d,]+)'
            m = re.match(pattern, vote)
            vote = int(m[1].replace(',', ''))
            outof = int(m[2].replace(',', ''))
            percent = round((vote/outof) * 100)
            return cat, vote, outof, percent
        except:
            return '','','',''
    else:
        return '','','',''

def imdb_parentsguide(tid):

    pg_url = f'https://www.imdb.com/title/{tid}/parentalguide'
    r = requests.get(pg_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Certification
    certs = soup.find(id='certificates')
    # Sex & Nudity
    section = soup.find(id='advisory-nudity')
    cat, vote, outof, percent = get_cat(section)
    scenes = get_scenes(section)
    nudity = {
            'name': 'Sex & Nudity',
            'score': '',
            'description': "\n".join(scenes), #scenes,
            'cat': cat,
            'votes': str(vote) + ' of ' + str(outof) + " found this " + cat,
            }
    # Violence & Gore
    section = soup.find(id='advisory-violence')
    cat, vote, outof, percent = get_cat(section)
    scenes = get_scenes(section)
    violence = {
            'name': 'Violence & Gore',
            'score': '',
            'description': "\n".join(scenes), #scenes,
            'cat': cat,
            'votes': str(vote) + ' of ' + str(outof) + " found this " + cat,
            }
    # Profanity
    section = soup.find(id='advisory-profanity')
    cat, vote, outof, percent = get_cat(section)
    scenes = get_scenes(section)
    profanity = {
            'name': 'Profanity',
            'score': '',
            'description': "\n".join(scenes), #scenes,
            'cat': cat,
            'votes': str(vote) + ' of ' + str(outof) + " found this " + cat,
            }
    # Alcohol, Drugs & Smoking
    section = soup.find(id='advisory-alcohol')
    cat, vote, outof, percent = get_cat(section)
    scenes = get_scenes(section)
    alcohol = {
            'name': 'Alcohol, Drugs, & Smoking',
            'score': '',
            'description': "\n".join(scenes), #scenes,
            'cat': cat,
            'votes': str(vote) + ' of ' + str(outof) + " found this " + cat,
            }
    # Frightening & Intense Scenes
    section = soup.find(id='advisory-frightening')
    cat, vote, outof, percent = get_cat(section)
    scenes = get_scenes(section)
    frightening = {
            'name': 'Frightening & Intense Scenes',
            'score': '',
            'description': "\n".join(scenes), #scenes,
            'cat': cat,
            'votes': str(vote) + ' of ' + str(outof) + " found this " + cat,
            }
    # Spoilers
    spoilers = soup.find(id='advisory-spoilers')
    if spoilers:
        # Spoiler-Nudity
        section = spoilers.find(id='advisory-spoiler-nudity')
        if section:
            scenes = get_scenes(section)
            nudity['spoilers'] = scenes
        # Spoiler-Violence
        section = spoilers.find(id='advisory-spoiler-violence')
        if section:
            scenes = get_scenes(section)
            violence['spoilers'] = scenes
        # Spoiler-Profanity
        section = spoilers.find(id='advisory-spoiler-profanity')
        if section:
            scenes = get_scenes(section)
            profanity['spoilers'] = scenes
        # Spoiler-Alcohol
        section = spoilers.find(id='advisory-spoiler-alcohol')
        if section:
            scenes = get_scenes(section)
            alcohol['spoilers'] = scenes
        # Spoiler-Frightening
        section = spoilers.find(id='advisory-spoiler-frightening')
        if section:
            scenes = get_scenes(section)
            frightening['spoilers'] = scenes
    advisory = list()
    if nudity['cat'] not in [None,""]: advisory.append(nudity)
    if violence['cat'] not in [None,""]: advisory.append(violence)
    if profanity['cat'] not in [None,""]: advisory.append(profanity)
    if alcohol['cat'] not in [None,""]: advisory.append(alcohol)
    if frightening['cat'] not in [None,""]: advisory.append(frightening)

    return advisory
