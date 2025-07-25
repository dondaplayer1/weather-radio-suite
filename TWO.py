import requests, json
from os import system as controller
twolink = 'https://tgftp.nws.noaa.gov/data/hurricane_products/atlantic/weather/outlook.txt'
config = json.load(open('config.json'))
speed = config['ttsSpeed']
pause = config['endPause']
phonemeDict = json.load(open('phonemeDB.json'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']

data = requests.get(twolink).text
data = data.split('\n')
data = data[8:]
data = ' '.join(data)
data = data.split('&&')
data = data[0]
data = data.split('$$')
data = data[0]
data = data.replace('...', ', ').replace('.', '. \n').replace(':', '. ').replace('*', '') #punctuation fix
for phoneme in phonemeDict:
    print(f'[PHONEMES] Replacing {phoneme} with {phonemeDict[phoneme]}')
    data = str(data).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
for word in replaceDict:
    print(f'[PHONEMES] Replacing {word} with {replaceDict[word]}')
    if '*PAUSE' in replaceDict[word]:
        pauseTime = replaceDict[word].split('*')[1].split('-')[1]
        word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
        data = str(data).replace(word, replaceDict[word])
    else:
        data = str(data).replace(word, replaceDict[word])
data = f'<vtml_speed value="{speed}"> <vtml_volume value="200"> The tropical weather outlook. {data} <vtml_pause time="1300"/> </vtml_volume> </vtml_speed>'
print(f'[MAIN] TWO Final:\n{data}')
with open('input.txt', 'w+') as f:
    print(f'[MAIN] Written to input.txt')
    f.write(data)
controller('TWOTTS.bat')
