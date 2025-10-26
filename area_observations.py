import sys
import json
import random
import logging
import traceback
from datetime import datetime
import requests
from utils import produce_wav_file

# If you touch stuff below, it might break. Be nice to it, it's fragile. Like me. I'm kidding. Why are you still reading this?

now = datetime.now()
config = json.load(open('config.json', encoding='utf-8'))
localObsCode = config['Observations']['mainObsCode']
currentTimeFormat = now.strftime('%I %p')
regionalObsCodes = config['Observations']['regionalObsCodes']
formatFile = 'obsFormat.txt'
speed = config['ttsSpeed']
pause = config['endPause']
globalTimeout = int(config.get('globalHTTPTimeout', 15))
openerlist = config['Observations']['openerList']
openers = config['Observations']['openers']
cityNameDef = config['Observations']['cityNameDef']
dividers = config['Observations']['dividers']
phonemeDict = json.load(open('phonemeDB.json', encoding='utf-8'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']
observations = []
recap = ''

log = logging.getLogger("BMH")

def getMain(airportCode):
    global recap
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/latest', timeout=globalTimeout).text
    apiCall = json.loads(apiCall)
    cityName = cityNameDef[airportCode]
    try:
        log.debug('[OBSERVATIONS] Grabbing main report for %s.', airportCode)
        skyCondition = str(apiCall['properties']['textDescription']).replace('fog', 'foggy')
        tempInF = str(toCelcius(apiCall['properties']['temperature']['value']))
        dewpointInF = str(toCelcius(apiCall['properties']['dewpoint']['value']))
        relativeHumidity = str(round(apiCall['properties']['relativeHumidity']['value'], 0)).replace('.0', '')
        windSpeed = str(toMPH(apiCall['properties']['windSpeed']['value']))
        try:
            windGust = str(toMPH(apiCall['properties']['windGust']['value']))
        except Exception:
            windGust = 'null'
        windDirection = str(degToCompass(round(apiCall['properties']['windDirection']['value'], 0)))
        Pressure = str(toinHG(apiCall['properties']['barometricPressure']['value']))
        PressureDirection = getPressureDirection(airportCode)
        time = now.strftime('%I %p').lstrip('0')
        if windGust == 'null':
            fullObservation = f'At {time} in {cityName}, it was {skyCondition}. The temperature was {tempInF}, the dewpoint {dewpointInF}, and the relative humidity was {relativeHumidity} percent. The wind was {windDirection} at {windSpeed} miles an hour. The pressure was {Pressure} inches and {PressureDirection}.'
        else:
            fullObservation = f'At {time} in {cityName}, it was {skyCondition}. The temperature was {tempInF}, the dewpoint {dewpointInF}, and the relative humidity was {relativeHumidity} percent. The wind was {windDirection} at {windSpeed} miles an hour, gusting to {windGust}. The pressure was {Pressure} inches and {PressureDirection}.'
        recap = f'Once again, at {time} in {cityName} it was {tempInF} degrees under {skyCondition} skies.'
    except Exception:
        log.error('[OBSERVATIONS] No report for %s. %s', airportCode, traceback.format_exc())
        fullObservation = f'The report from {cityName} was not available. '
        recap = ''
    observations.append(str(fullObservation))

def getRegional(airportCode):
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/latest', timeout=globalTimeout).text
    apiCall = json.loads(apiCall)
    cityName = cityNameDef[airportCode]
    try:
        log.debug('[OBSERVATIONS] Grabbing report for %s.', airportCode)
        skyCondition = apiCall['properties']['textDescription']
        tempInF = str(toCelcius(apiCall['properties']['temperature']['value']))[0:3].replace('.', '')
        windSpeed = str(toMPH(apiCall['properties']['windSpeed']['value']))
        try:
            windGust = str(toMPH(apiCall['properties']['windGust']['value']))
        except Exception:
            windGust = 'null'
        windDirection = str(degToCompass(round(apiCall['properties']['windDirection']['value'], 0)))
        if airportCode in dividers:
            if windGust == 'null':
                fullObservation = f'{dividers[airportCode]} {cityName}, it was {skyCondition}, with a temperature of {tempInF}. The <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> was {windDirection} at {windSpeed} miles an hour.'
            else:
                fullObservation = f'{dividers[airportCode]} {cityName}, it was {skyCondition}, with a temperature of {tempInF}. The <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> was {windDirection} at {windSpeed} miles an hour, gusting to {windGust} miles an hour.'
        else:
            randomDivider = random.choice(['In ', 'At '])
            log.debug('[OBSERVATIONS] Using random divider for %s: %s', airportCode, randomDivider)
            if windGust == 'null':
                fullObservation = f'{randomDivider}{cityName}, it was {skyCondition}, with a temperature of {tempInF}. The <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> was {windDirection} at {windSpeed} miles an hour.'
            else:
                fullObservation = f'{randomDivider}{cityName}, it was {skyCondition}, with a temperature of {tempInF}. The <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> was {windDirection} at {windSpeed} miles an hour, gusting to {windGust} miles an hour.'
    except Exception:
        log.error('[OBSERVATIONS] No report for %s.', airportCode)
        if airportCode in dividers:
            fullObservation = f'{dividers[airportCode]} {cityName}, the weather conditions were not available.'
        else:
            fullObservation = f'The report from {cityName} was not available. '
    observations.append(str(fullObservation))

def toCelcius(temp):
    temp = (temp * 1.8) + 32
    temp = round(temp, 0)
    temp = str(temp).replace('.0', '')
    return temp

def toMPH(kmh):
    mph = 0.6214 * kmh
    mph = round(mph, 0)
    mph = str(mph).replace('.0', '')
    return mph

def degToCompass(num):
    val=int((num/22.5)+.5)
    arr=["North", "Northeast", "East", "Southeast", "South", "Southwest","West","Northwest"]
    return arr[(val % 8)]

def toinHG(kpa):
    inHG = kpa / 3386.3886666667
    inHG = round(inHG, 2)
    return inHG

def getPressureDirection(airportCode):
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/latest', timeout=globalTimeout).text
    apiCall = json.loads(apiCall)
    currentPressure = toinHG(apiCall['properties']['barometricPressure']['value'])
    lastPressure = toinHG(apiCall['properties']['barometricPressure']['value'])
    if currentPressure > lastPressure:
        return 'rising'
    elif currentPressure < lastPressure:
        return 'falling'
    elif currentPressure == lastPressure:
        return 'steady'

def getObservations():
    try:
        global observations
        getMain(localObsCode)
        for location in regionalObsCodes:
            getRegional(location)
        observations.append(recap)
        observations = '\n'.join(observations)
        if len(openerlist) > 0:
            openerChoice = str(random.choice(openerlist))
            log.debug('[OBSERVATIONS OPENER] Picked "%s" for Observation Opener.', openers[openerChoice])
            opener = openers[openerChoice].replace('TIME', currentTimeFormat)
            observations = f'{opener} {observations}'
        for phoneme in phonemeDict:
            log.debug('[OBSERVATIONS PHONEMES] Replacing %s with %s', phoneme, phonemeDict[phoneme])
            observations = str(observations).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
        for word in replaceDict:
            log.debug('[OBSERVATIONS PHONEMES] Replacing %s with %s', word, replaceDict[word])
            if '*PAUSE' in replaceDict[word]:
                pauseTime = replaceDict[word].split('*')[1].split('-')[1]
                word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
                observations = str(observations).replace(word, replaceDict[word])
            else:
                observations = str(observations).replace(word, replaceDict[word])
        observations = f'<vtml_pause time="500"/> <vtml_speed value="{speed}"> ' + observations + f'<vtml_pause time="{pause}"/> </vtml_speed>'

        observations = observations.replace('\n', ' ').replace('\r', ' ')

        log.debug('[OBSERVATIONS] Final Text: %s', observations)
        produce_wav_file(observations, 'Observations.wav')
    except requests.exceptions.Timeout:
        log.error("[OBSERVATIONS] An HTTP Request timed out.")
    except Exception:
        log.error('[OBSERVATIONS] %s', traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[OBSERVATIONS] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
