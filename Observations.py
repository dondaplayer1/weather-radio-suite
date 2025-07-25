import json, requests, time
from datetime import datetime
import random
from os import system
now = datetime.now()

config = json.load(open('config.json'))
localObsCode = config['Observations']['mainObsCode']
currentTimeFormat = now.strftime('%I %p')
regionalObsCodes = config['Observations']['regionalObsCodes']
formatFile = 'obsFormat.txt'
speed = config['ttsSpeed']
pause = config['endPause']
openerlist = config['Observations']['openerList']
openers = config['Observations']['openers']
cityNameDef = config['Observations']['cityNameDef']
dividers = config['Observations']['dividers']
phonemeDict = json.load(open('phonemeDB.json'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']

#If you touch stuff below, it might break. Be nice to it, it's fragile. Like me. I'm kidding. Why are you still reading this?
observations = []

def getMain(airportCode):
    global recap
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/latest').text
    apiCall = json.loads(apiCall)
    cityName = cityNameDef[airportCode]
    try:
        print(f'[MAIN] Grabbing main report for {airportCode}.')
        skyCondition = str(apiCall['properties']['textDescription']).replace('fog', 'foggy')
        tempInF = str(toCelcius(apiCall['properties']['temperature']['value']))
        dewpointInF = str(toCelcius(apiCall['properties']['dewpoint']['value']))
        relativeHumidity = str(round(apiCall['properties']['relativeHumidity']['value'], 0)).replace('.0', '')
        windSpeed = str(toMPH(apiCall['properties']['windSpeed']['value']))
        try:
            windGust = str(toMPH(apiCall['properties']['windGust']['value']))
        except:
            windGust = 'null'
        windDirection = str(degToCompass(round(apiCall['properties']['windDirection']['value'], 0)))
        Pressure = str(toinHG(apiCall['properties']['barometricPressure']['value']))
        PressureDirection = getPressureDirection(airportCode)
        if windGust == 'null':
            fullObservation = f'At {cityName}, it was {skyCondition}. The temperature was {tempInF}, the dewpoint {dewpointInF}, the relative humidity was {relativeHumidity} percent. the wind was {windDirection}, at {windSpeed} miles an hour. the pressure was {Pressure} inches, and {PressureDirection}.'
        else:
            fullObservation = f'At {cityName}, it was {skyCondition}. The temperature was {tempInF}, the dewpoint {dewpointInF}, the relative humidity was {relativeHumidity} percent. the wind was {windDirection}, at {windSpeed} miles an hour,  gusting to {windGust}. the pressure was {Pressure} inches, and {PressureDirection}.'
        recap = f'Once again at {cityName}, {tempInF}. '
    except:
        print(f'[MAIN] [ERROR] No report for {airportCode}.')
        fullObservation = f'The report from {cityName} was not available. '
        recap = f''
    observations.append(str(fullObservation))

def getRegional(airportCode):
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/latest').text
    apiCall = json.loads(apiCall)
    cityName = cityNameDef[airportCode]
    try:
        print(f'[REGIONAL] Grabbing report for {airportCode}.')
        skyCondition = apiCall['properties']['textDescription']
        tempInF = str(toCelcius(apiCall['properties']['temperature']['value']))[0:3].replace('.', '')
        relativeHumidity = str(round(apiCall['properties']['relativeHumidity']['value'], 0)).replace('.0', '')
        windSpeed = str(toMPH(apiCall['properties']['windSpeed']['value']))
        try:
            windGust = str(toMPH(apiCall['properties']['windGust']['value']))
        except:
            windGust = 'null'
        windDirection = str(degToCompass(round(apiCall['properties']['windDirection']['value'], 0)))
        if airportCode in dividers:
            if windGust == 'null':
                fullObservation = f'{dividers[airportCode]} {cityName}, {skyCondition}, {tempInF}. <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> {windDirection} at {windSpeed} miles an hour.'
            else:
                fullObservation = f'{dividers[airportCode]} {cityName}, {skyCondition}, {tempInF}. <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> {windDirection} at {windSpeed} miles an hour, gusting to {windGust}.'
        else:
            if windGust == 'null':
                fullObservation = f'{cityName}, {skyCondition}, {tempInF}. <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> {windDirection} at {windSpeed} miles an hour.'
            else:
                fullObservation = f'{cityName}, {skyCondition}, {tempInF}. <vtml_phoneme alphabet="x-CMU" ph="W IH1 N D"></vtml_phoneme> {windDirection} at {windSpeed} miles an hour, gusting to {windGust}.'
    except:
        print(f'[REGIONAL] [ERROR] No report for {airportCode}.')
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
    apiCall = requests.get(f'https://api.weather.gov/stations/{airportCode}/observations/').text
    apiCall = json.loads(apiCall)
    currentPressure = toinHG(apiCall['features'][0]['properties']['barometricPressure']['value'])
    lastPressure = toinHG(apiCall['features'][1]['properties']['barometricPressure']['value'])
    if currentPressure > lastPressure:
        return 'Rising'
    elif currentPressure < lastPressure:
        return 'Falling'
    elif currentPressure == lastPressure:
        return 'Steady'

getMain(localObsCode)
for location in regionalObsCodes:
    getRegional(location)
observations.append(recap)
observations = '\n'.join(observations)
openerChoice = str(random.choice(openerlist))
print(f'[OPENER] Picked "{openers[openerChoice]}" for Observation Opener.')
opener = openers[openerChoice].replace('TIME', currentTimeFormat)
observations = f'{opener} {observations}'
for phoneme in phonemeDict:
    print(f'[PHONEMES] Replacing {phoneme} with {phonemeDict[phoneme]}')
    observations = str(observations).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
for word in replaceDict:
    print(f'[PHONEMES] Replacing {word} with {replaceDict[word]}')
    if '*PAUSE' in replaceDict[word]:
        pauseTime = replaceDict[word].split('*')[1].split('-')[1]
        word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
        observations = str(observations).replace(word, replaceDict[word])
    else:
        observations = str(observations).replace(word, replaceDict[word])
print(f'Final Obserevations:\n{observations}')
observations = f'<vtml_pause time="500"/> <vtml_speed value="{speed}"> ' + observations + f'<vtml_pause time="{pause}"/> </vtml_speed>'
print('[OUTPUT] Saving to input.txt')
with open('input.txt', 'w+') as f:
    f.write(observations)
system('ObsTTS.bat')
