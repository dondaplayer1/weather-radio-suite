import sys
import json
import logging
import traceback
from datetime import datetime
from utils import produce_wav_file

log = logging.getLogger("BMH")

config = json.load(open('config.json', encoding='utf-8'))
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

timeZone = timezone.replace('EDT', 'Eastern Daylight Time.').replace('EST', 'Eastern Standard Time.').replace('CDT', 'Central Daylight Time').replace('CST', 'Central Standard Time').replace('MDT', 'Mountain Daylight Time').replace('MST', 'Mountain Standard Time').replace('PDT', 'Pacific Daylight Time').replace('PST', 'Pacific Standard Time')

log.debug('[TIME] Running AutoTime - V2.0.0A\n[TIME] Format: %s\n[TIME] Speed: %s\n[TIME] Timezone: %s\n[TIME] Date is %s', script, speed, timeZone, dateStatus)

def getCurrentTime():
    try:
        log.debug('[TIME] Fetching Current Time...')
        dateSelect = str(date)
        now = datetime.now()
        timeFormat = now.strftime(f'%I. <vtml_pause time="0"/> %M. <vtml_pause time="0"/> %p. <vtml_pause time="0"/> {timeZone}')
        if now.strftime('%I')[0:1] == "0":
            try:
                hour = now.strftime('%I')
                if str(hour) == '00':
                    hour = '12'
                else:
                    hour = str(hour).replace('0', '')
                timeFormat = now.strftime(f'{hour}. <vtml_pause time="0"/> %M. <vtml_pause time="0"/> %p. <vtml_pause time="0"/> {timeZone}')
            except Exception:
                log.warning('[TIME WARN] That probably wasn\'t supposed to happen.')
                log.error('[TIME WARN] %s', traceback.format_exc())
        if now.strftime('%M')[0:1] == "0":
            minute = now.strftime('%M')
            if str(minute) == '00':
                hour_no_leading_0 = now.strftime('%I').lstrip('0')
                timeFormat = now.strftime(f'{hour_no_leading_0}. <vtml_pause time="0"/> %p. <vtml_pause time="0"/> {timeZone}')
        if dateSelect == 'True':
            log.debug('[DATE] Date is active.')
            dateFormat = now.strftime('<vtml_pause time="0"/> %B %d, %Y. ')
            dateFormat = dateScript + dateFormat
            log.debug('[DATE] %s', dateFormat)
        else:
            dateFormat = ''
        timeFormat = '<vtml_pause time="500"/> <vtml_speed value="' + speed + '"> ' + dateFormat + script + timeFormat + '<vtml_pause time="1300"/> </vtml_speed>'

        timeFormat = timeFormat.replace('\n', ' ').replace('\r', ' ')

        log.debug('[TIME] Final Text: %s', timeFormat)
        produce_wav_file(timeFormat, 'CurrentTime.wav')
    except Exception:
        log.error('[TIME] %s', traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[TIME] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
