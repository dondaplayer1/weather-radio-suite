import json, requests
from datetime import datetime
from os import system as controller

config = json.load(open('config.json'))
forecastDays = config['Forecast']['forecastDays']
forecastZone = config['Forecast']['forecastZone']
forecastPre = config['Forecast']['forecastPre']
forecastPost = config['Forecast']['forecastPost']
phonemeDict = json.load(open('phonemeDB.json'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']
speed = config['ttsSpeed']
pause = config['endPause']
apiCall = requests.get(f'https://api.weather.gov/zones/forecast/{forecastZone}/forecast').text
apiCall = json.loads(apiCall)
forecast = []

for period in apiCall['properties']['periods']:
    name = str(period['name']).capitalize()
    detailedForecast = str(period['detailedForecast'])
    #print(f'{name}, {detailedForecast}')
    forecast.append(f'{name}, {detailedForecast}')
finalForecast = forecast
finalForecast = ' '.join(finalForecast)
for phoneme in phonemeDict:
    print(f'[PHONEMES] Replacing {phoneme} with {phonemeDict[phoneme]}')
    finalForecast = str(finalForecast).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
for word in replaceDict:
    print(f'[PHONEMES] Replacing {word} with {replaceDict[word]}')
    if '*PAUSE' in replaceDict[word]:
        pauseTime = replaceDict[word].split('*')[1].split('-')[1]
        word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
        finalForecast = str(finalForecast).replace(word, replaceDict[word])
    else:
        finalForecast = str(finalForecast).replace(word, replaceDict[word])

finalForecast = f'{forecastPre}\n{finalForecast}\n{forecastPost}'

print(finalForecast)
finalForecast = f'<vtml_volume value="200"> <vtml_speed value="{speed}"> ' + finalForecast + f'<vtml_pause time="{pause}"/> </vtml_volume> </vtml_speed>'
with open('input.txt', 'w+') as f:
    f.write(finalForecast)
controller('ForecastTTS.bat')