from datetime import datetime
import subprocess
import json
global date

config = json.load(open('config.json'))
speed = config['ttsSpeed']
pause = config['endPause']
script = config['currentTime']['timeScript']
script = f'<vtml_pause time="500"/> {script} <vtml_pause time="0"/> ' #Played before the hour, minute, AM/PM, and timezone.
timezone = config['currentTime']['timeZone']
date = config['currentTime']['dateEnable']
dateScript = config['currentTime']['dateScript']

if date:
    dateStatus = 'ENABLED'
else:
    dateStatus = 'DISABLED'
timeZone = timezone.replace('EDT', 'Eastern Daylight Time.').replace('EST', 'Eastern Standard Time.').replace('CDT', 'Central Daylight Time').replace('CST', 'Central Standard Time')
print(f'[LOG] Running AutoTime - V2.0.0A\n[LOG] Format: {script}\n[LOG] Speed: {speed}\n[LOG] Timezone: {timeZone}\n[WARN] Date is {dateStatus}')

def getTime():
    print('[LOG] Fetching Current Time..')
    dateSelect = str(date)
    now = datetime.now()
    timeFormat = now.strftime(f'%I. <vtml_pause time="0"/> %M. <vtml_pause time="0"/> %p. <vtml_pause time="0"/> {timeZone}')
    if now.strftime('%I')[0:1] == "0":
        hour = now.strftime('%I')
        if str(hour) == '00':
            hour = '12'
        else:
            hour = str(hour).replace('0', '')
        timeFormat = now.strftime(f'{hour}. <vtml_pause time="0"/> %M. <vtml_pause time="0"/> %p. <vtml_pause time="0"/> {timeZone}')
        print(f'[LOG] {timeFormat}')
    else:
        print(f"[WARN] That probably wasn't supposed to happen.")
        pass
    if dateSelect == 'True':
        print('[WARN] Date is active.')
        dateFormat = now.strftime('<vtml_pause time="0"/> %B %d, %Y. ')
        dateFormat = dateScript + dateFormat
        print(f'[LOG] {dateFormat}')
    else:
        dateFormat = ''
    timeFormat = '<vtml_pause time="500"/> <vtml_speed value="' + speed + '"> ' + dateFormat + script + timeFormat + '<vtml_pause time="1300"/> </vtml_speed>'
    print(f'[LOG] Final Text: {timeFormat}')
    print(timeFormat)
    with open('input.txt', 'w') as f:
        print('[LOG] Writing to input.txt')
        f.write(timeFormat)
    print('[LOG] Running othertts.bat')
    subprocess.call(['TimeTTS.bat'])
    print('[LOG] Done!')

getTime()
