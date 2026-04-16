import re
import sys
import json
import logging
import traceback
import requests
from utils import produce_wav_file

log = logging.getLogger("BMH")

config = json.load(open('config.json', encoding='utf-8'))
office = config['HWO']['office']
preambleStatus = config['HWO']['preambleEnable']
preamble = config['HWO']['preamble']
speed = config['ttsSpeed']
pause = config['endPause']
phonemeDict = json.load(open('phonemeDB.json', encoding='utf-8'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']
globalTimeout = int(config.get('globalHTTPTimeout', 15))

def getHazardousWeatherOutlook():
    try:
        log.debug('[HWO] Grabbing HWO')
        apiCall = requests.get(f'https://api.weather.gov/products/types/HWO/locations/{office}', timeout=globalTimeout).text
        apiCall = json.loads(apiCall)
        thing = apiCall['@graph']
        hwo = thing[0]
        hwo = hwo['@id']
        hwo = requests.get(f'{hwo}', timeout=globalTimeout).text
        hwo = json.loads(hwo)
        hwo = hwo['productText']
        hwo = hwo.split('\n')
        index = [idx for idx, s in enumerate(hwo) if 'this hazardous weather outlook is for' in s.lower()][0]
        if preambleStatus: #if preamble is enabled, don't include the default NWS HWO header!
            log.debug('[HWO] Preamble enabled!')
            hwo = hwo[int(index) + 1:-2]
            while hwo and not hwo[0].strip():
                hwo.pop(0)
            hwo = '\n'.join(hwo)
        else: #if preamble disabled, pull default NWS HWO header
            hwo = hwo[int(index):-2]
            hwo = '\n'.join(hwo)
        for phoneme in phonemeDict:
            log.debug('[HWO PHONEMES] Replacing %s with %s', phoneme, phonemeDict[phoneme])
            hwo = str(hwo).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
        for word in replaceDict:
            log.debug('[HWO PHONEMES] Replacing %s with %s', word, replaceDict[word])
            if '*PAUSE' in replaceDict[word]:
                pauseTime = replaceDict[word].split('*')[1].split('-')[1]
                word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
                hwo = str(hwo).replace(word, replaceDict[word])
            else:
                hwo = str(hwo).replace(word, replaceDict[word])

        hwo = re.sub(r'\$\$.*\b(20\d{2})\b', '', hwo, flags=re.DOTALL)
        hwo = hwo.replace('\n', ' ').replace('\r', ' ')
        
        if preambleStatus:
            log.debug('[HWO] Adding HWO preamble.')
            hwo = f'{preamble} {hwo}'
        log.debug('[HWO] Final Text: %s', hwo)
        produce_wav_file(hwo, 'HWO.wav')
    except requests.exceptions.Timeout:
        log.error("[HWO] An HTTP Request timed out.")
    except Exception:
        log.error('[HWO] %s', traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[HWO] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
