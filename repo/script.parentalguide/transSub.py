import xbmc
import xbmcgui
import xbmcaddon
import googletrans
import re
import time

def translate_text(text, dest='ar'):
    # Split the text into 500 characters segments
    segments = re.findall('.{1,500}', text)
    translator = googletrans.Translator(service_urls=['translate.google.com'])
    translated_text = ''
    for segment in segments:
        translated_text += translator.translate(segment, dest=dest).text
    return translated_text

def get_selected_subtitle():
    player = xbmc.Player()
    if player.isPlaying():
        subs = player.getAvailableSubtitleStreams(1)[1]
        #subs = player.getSubtitles()
        subs = translate_text("Hi this me")
        xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(subs))
        # path = subs.getSubtitleServerPath()
        # xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(path))
        # subtitle = player.getSubtitles()
        # if subtitle:
            # subtitle_path = subtitle[0].getPath()
            # xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(subtitle_path))
            # with open(subtitle_path, 'r', encoding='utf-8') as f:
                # subtitle_text = f.read()
                # # Check if the subtitle language is not Arabic
                # if not googletrans.LANGUAGES['ar'] in googletrans.detect(subtitle_text[:100]).lang:
                    # translated_text = translate_text(subtitle_text)
                    # # Save the translated text to a new file
                    # new_path = subtitle_path.replace('.srt','.ar.srt')
                    # with open(new_path, 'w', encoding='utf-8') as f:
                        # f.write(translated_text)
                    # # Load the new file into Kodi
                    # time.sleep(250)
                    # xbmc.Player().setSubtitles(new_path)
                    # xbmcaddon.Addon().setSetting("subtitles.lang.1", "ar")
                    # xbmc.executebuiltin("Notification(Translated Subtitle,{})".format(new_path))
                # else:
                    # xbmc.executebuiltin("Notification(Selected Subtitle,{})".format(subtitle_path))

get_selected_subtitle()
