import sys
import json
import logging
import traceback
import requests
from utils import produce_wav_file

log = logging.getLogger("BMH")

def getForecast():
    try:
        config = json.load(open('config.json', encoding='utf-8'))
        forecastZone = config['Forecast']['forecastZone']
        forecastPre = config['Forecast']['forecastPre']
        forecastPost = config['Forecast']['forecastPost']
        phonemeDict = json.load(open('phonemeDB.json', encoding='utf-8'))
        replaceDict = phonemeDict['replace']
        phonemeDict = phonemeDict['phonemes']
        speed = config['ttsSpeed']
        globalTimeout = int(config.get('globalHTTPTimeout', 15))
        pause = config['endPause']
        apiCall = requests.get(f'https://api.weather.gov/zones/forecast/{forecastZone}/forecast', timeout=globalTimeout).text
        apiCall = json.loads(apiCall)
        forecast = []

        for period in apiCall['properties']['periods']:
            name = str(period['name']).capitalize()
            detailedForecast = str(period['detailedForecast'])
            forecast.append(f'{name}, {detailedForecast}')
        finalForecast = forecast
        finalForecast = ' '.join(finalForecast)
        for phoneme in phonemeDict:
            log.debug('[FORECAST PHONEMES] Replacing %s with %s', phoneme, phonemeDict[phoneme])
            finalForecast = str(finalForecast).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
        for word in replaceDict:
            log.debug('[FORECAST PHONEMES] Replacing %s with %s', word, replaceDict[word])
            if '*PAUSE' in replaceDict[word]:
                pauseTime = replaceDict[word].split('*')[1].split('-')[1]
                word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
                finalForecast = str(finalForecast).replace(word, replaceDict[word])
            else:
                finalForecast = str(finalForecast).replace(word, replaceDict[word])

        finalForecast = f'{forecastPre}\n{finalForecast}\n{forecastPost}'
        finalForecast = f'<vtml_volume value="200"> <vtml_speed value="{speed}"> ' + finalForecast + f'<vtml_pause time="{pause}"/> </vtml_volume> </vtml_speed>'

        finalForecast = finalForecast.replace('\n', ' ').replace('\r', ' ')

        log.debug('[FORECAST] Final Text: %s', finalForecast)
        produce_wav_file(finalForecast, 'Forecast.wav')
    except requests.exceptions.Timeout:
        log.error("[FORECAST] An HTTP Request timed out.")
    except Exception:
        log.error('[FORECAST] %s', traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[FORECAST] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
