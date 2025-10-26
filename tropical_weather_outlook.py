import sys
import json
import logging
import traceback
import requests
from utils import produce_wav_file

log = logging.getLogger("BMH")

def getTropicalWeatherOutlook():
    twolink = 'https://tgftp.nws.noaa.gov/data/hurricane_products/atlantic/weather/outlook.txt'
    config = json.load(open('config.json', encoding='utf-8'))
    speed = config['ttsSpeed']
    globalTimeout = int(config.get('globalHTTPTimeout', 15))
    phonemeDict = json.load(open('phonemeDB.json', encoding='utf-8'))
    replaceDict = phonemeDict['replace']
    phonemeDict = phonemeDict['phonemes']

    try:
        log.debug('[TWO] Grabbing TWO')
        data = requests.get(twolink, timeout=globalTimeout).text
        data = data.split('\n')
        data = data[8:]
        data = ' '.join(data)
        data = data.split('&&')
        data = data[0]
        data = data.split('$$')
        data = data[0]
        data = data.replace('...', ', ').replace('.', '. \n').replace(':', '. ').replace('*', '') #punctuation fix
        for phoneme in phonemeDict:
            log.debug('[TWO PHONEMES] Replacing %s with %s', phoneme, phonemeDict[phoneme])
            data = str(data).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
        for word in replaceDict:
            log.debug('[TWO PHONEMES] Replacing %s with %s', word, replaceDict[word])
            if '*PAUSE' in replaceDict[word]:
                pauseTime = replaceDict[word].split('*')[1].split('-')[1]
                word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
                data = str(data).replace(word, replaceDict[word])
            else:
                data = str(data).replace(word, replaceDict[word])
        data = f'<vtml_speed value="{speed}"> <vtml_volume value="200"> The tropical weather outlook. {data} <vtml_pause time="1300"/> </vtml_volume> </vtml_speed>'

        data = data.replace('\n', ' ').replace('\r', ' ')

        log.debug('[TWO] Final Text: %s', data)
        produce_wav_file(data, 'TWO.wav')
    except requests.exceptions.Timeout:
        log.error("[TWO] An HTTP Request timed out.")
    except Exception:
        log.error('[TWO] %s', traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[TWO] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
