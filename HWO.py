import requests
import json
from os import system

config = json.load(open('config.json'))
office = config['HWO']['office']
speed = config['ttsSpeed']
pause = config['endPause']
phonemeDict = json.load(open('phonemeDB.json'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']

def getHWO():
    print('[LOG] Grabbing HWO')
    apiCall = requests.get(f'https://api.weather.gov/products/types/HWO/locations/{office}').text
    apiCall = json.loads(apiCall)
    thing = apiCall['@graph']
    hwo = thing[0]
    hwo = hwo['@id']
    hwo = requests.get(f'{hwo}').text
    hwo = json.loads(hwo)
    hwo = hwo['productText']
    hwo = hwo.split('\n')
    index = [idx for idx, s in enumerate(hwo) if 'this hazardous weather outlook is for' in s.lower()][0]
    hwo = hwo[int(index):-2]
    hwo = '\n'.join(hwo)
    for phoneme in phonemeDict:
        print(f'[PHONEMES] Replacing {phoneme} with {phonemeDict[phoneme]}')
        hwo = str(hwo).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
    for word in replaceDict:
        print(f'[PHONEMES] Replacing {word} with {replaceDict[word]}')
        if '*PAUSE' in replaceDict[word]:
            pauseTime = replaceDict[word].split('*')[1].split('-')[1]
            word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
            hwo = str(hwo).replace(word, replaceDict[word])
        else:
            hwo = str(hwo).replace(word, replaceDict[word])
    print(f'[LOG] Final Text: {hwo}')
    print(f'[LOG] Outputting to input.txt')
    with open('input.txt', 'w+') as f:
        f.write(f'<vtml_speed value="{speed}"> {hwo} </vtml_speed> <vtml_pause time="{pause}"/>')
    print(f'[LOG] Running HWOTTS.bat')
    system('HWOTTS.bat')

getHWO()