# -*- coding: utf-8 -*-
#from .LiberAPI import LiberTranslateAPI
import json
import sys
from typing import Any, Dict
from urllib import request, parse
#from .lib.third_party import translate
from .lib.third_party.translate import Translator
from .lib.third_party import pysubs2
import xbmc
import re
import requests
from concurrent.futures import ThreadPoolExecutor
import time

def MTransText(segment, dest,s):
    #print("translating : " + segment)
    #s = requests.Session()
    text = segment
    URL = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=" + dest + "&q=" + text
    with s.get(URL) as res:
        r = res.text.replace("[[","").replace("]]","").split(",")[0].replace('''"''',"").strip()
        print("Translated : .." + r[0:20])
    return r

def trans(text, core, filepath, lang_code):
    # Split the text into 500 characters segments
    segments = re.findall('.{1,3000}', text)
    my_translator = Translator(to_lang="en",from_lang="en")
    translated_text = ''
    for segment in segments:
        translated_text += my_translator.translate(segment)
    return translated_text

    
    
def __download(core, filepath, request):
    request['stream'] = True
    with core.request.execute(core, request) as r:
        with open(filepath, 'wb') as f:
            core.shutil.copyfileobj(r.raw, f)

def __extract_gzip(core, archivepath, filename):
    filepath = core.os.path.join(core.utils.temp_dir, filename)

    if core.utils.py2:
        with open(archivepath, 'rb') as f:
            gzip_file = f.read()

        with core.gzip.GzipFile(fileobj=core.utils.StringIO(gzip_file)) as gzip:
            with open(filepath, 'wb') as f:
                f.write(gzip.read())
                f.flush()
    else:
        with core.gzip.open(archivepath, 'rb') as f_in:
            with open(filepath, 'wb') as f_out:
                core.shutil.copyfileobj(f_in, f_out)

    return filepath

def __extract_zip(core, archivepath, filename, episodeid):
    sub_exts = ['.srt', '.sub']
    sub_exts_secondary = ['.smi', '.ssa', '.aqt', '.jss', '.ass', '.rt', '.txt']

    try:
        using_libvfs = False
        with open(archivepath, 'rb') as f:
            zipfile = core.zipfile.ZipFile(core.BytesIO(f.read()))
        namelist = core.utils.get_zipfile_namelist(zipfile)
    except:
        using_libvfs = True
        archivepath_ = core.utils.quote_plus(archivepath)
        (dirs, files) = core.kodi.xbmcvfs.listdir('archive://%s' % archivepath_)
        namelist = [file.decode(core.utils.default_encoding) if core.utils.py2 else file for file in files]

    subfile = core.utils.find_file_in_archive(core, namelist, sub_exts, episodeid)
    if not subfile:
        subfile = core.utils.find_file_in_archive(core, namelist, sub_exts_secondary, episodeid)

    dest = core.os.path.join(core.utils.temp_dir, filename)
    if not subfile:
        try:
            return __extract_gzip(core, archivepath, filename)
        except:
            try: core.os.remove(dest)
            except: pass
            try: core.os.rename(archivepath, dest)
            except: pass
            return dest

    if not using_libvfs:
        src = core.utils.extract_zipfile_member(zipfile, subfile, core.utils.temp_dir)
        try: core.os.remove(dest)
        except: pass
        try: core.os.rename(src, dest)
        except: pass
    else:
        src = 'archive://' + archivepath_ + '/' + subfile
        core.kodi.xbmcvfs.copy(src, dest)

    return dest

def __insert_lang_code_in_filename(core, filename, lang_code):
    filename_chunks = core.utils.strip_non_ascii_and_unprintable(filename).split('.')
    filename_chunks.insert(-1, lang_code)
    return '.'.join(filename_chunks)

def __postprocess(core, filepath, lang_code):
    try:
        with open(filepath, 'rb') as f:
            text_bytes = f.read().decode('utf-8')

        if core.kodi.get_bool_setting('general.use_chardet'):
            encoding = ''
            if core.utils.py3:
                detection = core.utils.chardet.detect(text_bytes)
                detected_lang_code = core.kodi.xbmc.convertLanguage(detection['language'], core.kodi.xbmc.ISO_639_2)
                if detection['confidence'] == 1.0 or detected_lang_code == lang_code:
                    encoding = detection['encoding']

            if not encoding:
                encoding = core.utils.code_pages.get(lang_code, core.utils.default_encoding)

            text = text_bytes.decode(encoding)
            text= trans(text)
        else:
            text = text_bytes.decode(core.utils.default_encoding)
            text= trans(text)

        try:
            if all(ch in text for ch in core.utils.cp1251_garbled):
                text = text.encode(core.utils.base_encoding).decode('cp1251')
                text= trans(text)
            elif all(ch in text for ch in core.utils.koi8r_garbled):
                try:
                    text = text.encode(core.utils.base_encoding).decode('koi8-r')
                    text= trans(text)
                except:
                    text = text.encode(core.utils.base_encoding).decode('koi8-u')
                    text= trans(text)
        except: pass

        try:
            clean_text = core.utils.cleanup_subtitles(core, text)
            if len(clean_text) > len(text) / 2:
                text = clean_text
                text= trans(text)
        except: pass

        with open(filepath, 'wb') as f:
            f.write(text.encode(core.utils.default_encoding))
    except: pass

def MTrans(segment, dest, s):
    text = segment.text
    URL = "https://clients5.google.com/translate_a/t?client=dict-chrome-ex&sl=auto&tl=" + dest + "&q=" + text
    res = s.get(URL).text
    r = res.replace("[[","").replace("]]","").split(",")[0].replace('''"''',"").strip()
    segment.text = r
    return r
    
def oldtransfile(core, filepath, lang_code):
    #requests.Session().close()
    text = ''
    #s = requests.Session()
    dest = core.kodi.get_setting('general.use_langcode')
    #xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(filepath))
#try:
    with open(filepath, 'rb') as f:
        text_bytes = f.read().decode('utf-8')
        segments = pysubs2.load(filepath, encoding="utf-8")
        
    ####---------------------------------------------------------
    # #########Trans each line
    
    # i = 1
    # j = len(segments)
    # for seg in segments:
        # progress = str(i) + "/" + str(j)
        # xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(str(progress)))
        # x = MyTrans(seg.text, dest, s)
        # seg.text = x
        # i = i + 1
        # segments.save(filepath)
    
    factor = len(segments)
    with ThreadPoolExecutor(max_workers=10) as executor:
        with requests.Session() as session:
            executor.map(MTrans, segments, [dest]*factor)
            executor.shutdown(wait=True)
        
    segments.save(filepath)
        
    # ####---------------------------------------------------------
    # i = 0
    # ###### Combine Lines into a list
    # for segment in segments[0:Nstep]:
        # segcontents +=  segment.text
    # ###### Join Lines into one string
    # FullSegContent = "[(-)]".join(segcontents)
    # ###### Translate this combined string
    # Fullres = MyTrans(FullSegContent, core, s)
    # ###### Deconstruct the translated text into a new list
    # FullresList = Fullres.split("[(-)]")
    # ###### Edit the original segments with the new translated versions
    # for x in range(i,Nstep):
        # segments[x].text = FullresList[x]
    
    requests.Session().close()
    
    
    
    # with open(filepath, 'wb') as f:
        # f.write(text.encode(core.utils.default_encoding))
#except: pass

def transfile(core, filepath, lang_code):
    CLEANR1 = re.compile('{.*?}')
    CLEANR2 = re.compile('[.*?]')
    CLEANR3 = re.compile('<.*?>')
    InputSet=set()
    
    requests.Session().close
    Transparts =''
    start = time.process_time()
    text = ''
    s = requests.Session()
    dest = core.kodi.get_setting('general.use_langcode')

    # Opening file and conversting subs into a list of pysub2 objects
    with open(filepath, 'rb') as f:
        segments = pysubs2.load(filepath, encoding="utf-8", keep_unknown_html_tags=False)
    print("File opened : "+ str(filepath))
    print("Cleaning Started ..  ")
    # Fixes for some instring issue - will be reconstructed later
    InputList = []
    k = 1
    CountSubs = len(segments)
    Out = []
    for i in range(0,CountSubs):
        progress = str(i+1) + "/" + str(CountSubs)
        xbmc.executebuiltin("Notification(Concentrating,{})".format(progress))
        #segstr = seg.text
        segments[i] = MTrans(segments[i],dest, s)
        #segstr = re.sub(CLEANR1, '', segstr)
        #segstr = re.sub(CLEANR2, '', segstr)
        #segstr = re.sub(CLEANR3, '', segstr)
        #InputSet.add(segstr.replace("\\N"," (:) ").strip().replace("..","."))
        #InputList.append(segstr.replace("\\N"," (:) ").strip().replace("..","."))
        segments.save(filepath)
        #k = k +1
    print("Cleaning Finished ..  ")

    # InputList = list(InputSet)

    # # Concentrating Sublines into one string - (-8-) is a space holder to be used for splitting

    # InputCombinedListStr = " (.) ".join(InputList)
    # #print(InputCombinedListStr)
    # # Split the text into 1800 characters segments
    # parts = re.findall('.{1,1800}', InputCombinedListStr)
    # print("Translating ..  " + str(len(parts)) + " strings")
    # xbmc.executebuiltin("Notification(Translating,{})".format(str(len(parts)) + " strings"))
    # # Translating segments
    # for part in parts:
        # #time.sleep(1)
        # Transparts+= MTransText(part, 'ar', s)
    # requests.Session().close
    # print("Translatintion Completed - Length of response " + str(len(Transparts)))
    # xbmc.executebuiltin("Notification(Translation Completed)")
    # print(Transparts)

    # # Reconstruting the output list from the translated string
    # OutputCombinedListStr = Transparts
    # OutputCombinedListStr = OutputCombinedListStr.replace(" (:) ","\\N")
    # OutputCombinedList = str(OutputCombinedListStr).split(" (.) ")

    # x = len(OutputCombinedList)
    # y = len(InputList)
    # print("Translatintion Results splitted into {}".format(x))
    # print("OutputCombinedList" + str(x))
    # print("InputList" + str(y))

    # # Writing translated version to the same file
    # if y > x or y < x:
        # print("error - 2 files were generated for debuging")
        # for i in range(0, y):
            # segments[i].text = InputList[i]
        # segments.save(filepath.replace(".srt","org.srt"))
        # for i in range(0, x):
            # segments[i].text = OutputCombinedList[i]
        # segments.save(filepath.replace(".srt","output.srt"))
    # else:
        # for i in range(0, CountSubs):
            # segments[i].text = OutputCombinedList[i]
        # print("Saving to file")
        # xbmc.executebuiltin("Notification(Saving File)")
        # segments.save(filepath)

def download(core, params):
    core.logger.debug(lambda: core.json.dumps(params, indent=2))

    core.shutil.rmtree(core.utils.temp_dir, ignore_errors=True)
    core.kodi.xbmcvfs.mkdirs(core.utils.temp_dir)

    actions_args = params['action_args']
    lang_code = core.kodi.xbmc.convertLanguage(actions_args['lang'], core.kodi.xbmc.ISO_639_2)
    filename = __insert_lang_code_in_filename(core, actions_args['filename'], lang_code)
    archivepath = core.os.path.join(core.utils.temp_dir, 'sub.zip')

    service_name = params['service_name']
    service = core.services[service_name]
    request = service.build_download_request(core, service_name, actions_args)

    if actions_args.get('raw', False):
        filepath = core.os.path.join(core.utils.temp_dir, filename)
        __download(core, filepath, request)
    else:
        __download(core, archivepath, request)
        if actions_args.get('gzip', False):
            filepath = __extract_gzip(core, archivepath, filename)
        else:
            episodeid = actions_args.get('episodeid', '')
            filepath = __extract_zip(core, archivepath, filename, episodeid)
    
    if core.kodi.get_bool_setting('general.use_googletranslate'):
        lang_code = core.kodi.get_setting('general.use_langcode')
        transfile(core, filepath, lang_code)
    
    __postprocess(core, filepath, lang_code)

    
    if core.api_mode_enabled:
        return filepath

    
    
    listitem = core.kodi.xbmcgui.ListItem(label=filepath, offscreen=True)
    core.kodi.xbmcplugin.addDirectoryItem(handle=core.handle, url=filepath, listitem=listitem, isFolder=False)

