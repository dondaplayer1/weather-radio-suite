import os
import re
import sys
import json
import logging
import traceback
from datetime import datetime
from collections import defaultdict
import requests
from utils import produce_wav_file


config = json.load(open('config.json', encoding='utf-8'))
speed = config['ttsSpeed']
pause = config['endPause']
globalTimeout = int(config.get('globalHTTPTimeout', 15))
stationID = config['AlertSummary']['stationID']
alertZones = config['AlertSummary']['alertZones']
timezoneLong = config['AlertSummary']['timezoneLong']
phonemeDict = json.load(open('phonemeDB.json', encoding='utf-8'))
replaceDict = phonemeDict['replace']
phonemeDict = phonemeDict['phonemes']
#useless (not really)
us_state_to_abbrev = {
    "Alabama": "AL",
    "Alaska": "AK",
    "Arizona": "AZ",
    "Arkansas": "AR",
    "California": "CA",
    "Colorado": "CO",
    "Connecticut": "CT",
    "Delaware": "DE",
    "Florida": "FL",
    "Georgia": "GA",
    "Hawaii": "HI",
    "Idaho": "ID",
    "Illinois": "IL",
    "Indiana": "IN",
    "Iowa": "IA",
    "Kansas": "KS",
    "Kentucky": "KY",
    "Louisiana": "LA",
    "Maine": "ME",
    "Maryland": "MD",
    "Massachusetts": "MA",
    "Michigan": "MI",
    "Minnesota": "MN",
    "Mississippi": "MS",
    "Missouri": "MO",
    "Montana": "MT",
    "Nebraska": "NE",
    "Nevada": "NV",
    "New Hampshire": "NH",
    "New Jersey": "NJ",
    "New Mexico": "NM",
    "New York": "NY",
    "North Carolina": "NC",
    "North Dakota": "ND",
    "Ohio": "OH",
    "Oklahoma": "OK",
    "Oregon": "OR",
    "Pennsylvania": "PA",
    "Rhode Island": "RI",
    "South Carolina": "SC",
    "South Dakota": "SD",
    "Tennessee": "TN",
    "Texas": "TX",
    "Utah": "UT",
    "Vermont": "VT",
    "Virginia": "VA",
    "Washington": "WA",
    "West Virginia": "WV",
    "Wisconsin": "WI",
    "Wyoming": "WY",
    "District of Columbia": "DC",
    "American Samoa": "AS",
    "Guam": "GU",
    "Northern Mariana Islands": "MP",
    "Puerto Rico": "PR",
    "United States Minor Outlying Islands": "UM",
    "U.S. Virgin Islands": "VI",
}

log = logging.getLogger("BMH")

# invert the dictionary
abbrev_to_us_state = dict(map(reversed, us_state_to_abbrev.items()))

alertList = []
alertIDList = []
alertReadout = []
counties = []

ibwalerts = ['TOR', 'SVR', 'FFW', 'SQW']

def add_colon_to_time(string):
    pattern = r'(\d{1,2})(\d{2})\s*(AM|PM)'
    replaced_string = re.sub(pattern, r'\1:\2 \3', string)
    return replaced_string

def getAlertSummary():
    global alertList
    global alertReadout
    global globalTimeout
    global stationID

    try:
        for county in alertZones:
            apiCall = requests.get(f'https://api.weather.gov/alerts/active/zone/{county}', timeout=globalTimeout).text
            apiCall = json.loads(apiCall)
            #try:
            for feature in apiCall['features']:
                alertid = feature['id']
                eventcode = ''.join(feature['properties']['parameters']['AWIPSidentifier'])[0:3]
                log.debug("[ALERTSUMMARY] Event code: %s", eventcode)
                global counties
                if alertid not in alertIDList:
                    if eventcode in ibwalerts:
                        alertIDList.append(alertid)
                        readoutstring = '\n' + str(feature['properties']['description']).replace('\n', ' ').replace('...', ', ') + ' \n ' + str(feature['properties']['instruction']).replace('\n', ' ').replace('...', ', ') + '<vtml_pause time="1300"/>'
                        readoutstring = add_colon_to_time(readoutstring)
                        alertReadout.append(readoutstring)
                        event = feature['properties']['event']
                        expireTime = feature['properties']['expires']
                        #2023-02-06T03:00:00-06:00
                        expireTime = datetime.strptime(expireTime[0:-6], '%Y-%m-%dT%H:%M:%S')
                        expireTimeHR = expireTime.strftime('%I')
                        expireTimeMIN = expireTime.strftime('%M')
                        expireTimeTS = expireTime.strftime('%p')
                        if expireTimeMIN == '00':
                            if expireTimeHR[0:1] == '0':
                                expireTimeStamp = expireTimeHR[1:] + ' ' + expireTimeTS
                            else:
                                expireTimeStamp = expireTimeHR + ' ' + expireTimeTS
                        else:
                            if expireTimeHR[0:1] == '0':
                                expireTimeStamp = expireTimeHR[1:] + ':' + expireTimeMIN + ' ' + expireTimeTS
                            else:
                                expireTimeStamp = expireTimeHR + ':' + expireTimeMIN + ' ' + expireTimeTS
                        affectedZones = {}
                        states = []
                        for zone in feature['properties']['affectedZones']:
                            zoneCall = requests.get(zone, timeout=globalTimeout).text
                            zoneCall = json.loads(zoneCall)
                            state = zoneCall['properties']['state']
                            county = zoneCall['properties']['name']
                            affectedZones[county]=state
                            states.append(state)
                        res = defaultdict(list)
                        for key, val in sorted(affectedZones.items()):
                            res[val].append(key)
                        locationString = []
                        completedStates = []
                        for state in states:
                            stateName = abbrev_to_us_state[state]
                            counties = res[state]
                            useCountiesOrParishes = 'counties' if state not in ['LA', 'AK'] else 'parishes'
                            useCountyOrParish = 'county' if state not in ['LA', 'AK'] else 'parish'
                            if len(counties) > 1 and state not in completedStates:
                                completedStates.append(state)
                                insertInt = len(counties) - 1
                                counties.insert(insertInt, 'and')
                                counties = ', '.join(counties)
                                counties = counties.replace('and, ', 'and ')
                                string = f'the following {useCountiesOrParishes}, in {stateName}, {counties}'
                                locationString.append(string)
                            elif state not in completedStates:
                                counties = ''.join(counties)
                                string = f'the following {useCountyOrParish}, {county}, {stateName}'
                                locationString.append(string)
                            else:
                                pass
                        finalLocString = []
                        if len(locationString) > 1:
                            for loc in locationString:
                                finalLocString.append(loc)
                            finalLocString = ', and '.join(finalLocString)
                            finalLocString = 'for ' + finalLocString + '. '
                            alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                        else:
                            finalLocString = ''.join(locationString)
                            finalLocString = 'for ' + finalLocString + '. '
                            alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                    elif eventcode == 'WCN':
                        if feature['properties']['event'] == 'Tornado Watch':
                            alertIDList.append(alertid)
                            event = feature['properties']['event']
                            expireTime = feature['properties']['expires']
                            #2023-02-06T03:00:00-06:00
                            expireTime = datetime.strptime(expireTime[0:-6], '%Y-%m-%dT%H:%M:%S')
                            expireTimeHR = expireTime.strftime('%I')
                            expireTimeMIN = expireTime.strftime('%M')
                            expireTimeTS = expireTime.strftime('%p')
                            if expireTimeMIN == '00':
                                if expireTimeHR[0:1] == '0':
                                    expireTimeStamp = expireTimeHR[1:] + ' ' + expireTimeTS
                                else:
                                    expireTimeStamp = expireTimeHR + ' ' + expireTimeTS
                            else:
                                if expireTimeHR[0:1] == '0':
                                    expireTimeStamp = expireTimeHR[1:] + ':' + expireTimeMIN + ' ' + expireTimeTS
                                else:
                                    expireTimeStamp = expireTimeHR + ':' + expireTimeMIN + ' ' + expireTimeTS
                            affectedZones = {}
                            states = []
                            for zone in feature['properties']['affectedZones']:
                                zoneCall = requests.get(zone, timeout=globalTimeout).text
                                zoneCall = json.loads(zoneCall)
                                state = zoneCall['properties']['state']
                                county = zoneCall['properties']['name']
                                affectedZones[county]=state
                                states.append(state)
                            res = defaultdict(list)
                            for key, val in sorted(affectedZones.items()):
                                res[val].append(key)
                            locationString = []
                            completedStates = []
                            watchNo = ''.join(feature['properties']['parameters']['VTEC']).split('.')[5]
                            inefficient = watchNo[0:1]
                            if inefficient == '0':
                                watchNo = watchNo[1:]
                            inefficient = watchNo[1:2]
                            if inefficient == '0':
                                watchNo = watchNo[2:]
                            for state in states:
                                stateName = abbrev_to_us_state[state]
                                counties = res[state]
                                useCountiesOrParishes = 'counties' if state not in ['LA', 'AK'] else 'parishes'
                                useCountyOrParish = 'county' if state not in ['LA', 'AK'] else 'parish'
                                if len(counties) > 1 and state not in completedStates:
                                    completedStates.append(state)
                                    insertInt = len(counties) - 1
                                    counties.insert(insertInt, 'and')
                                    counties = ', '.join(counties)
                                    counties = counties.replace('and, ', 'and ')
                                    string = f'the following {useCountiesOrParishes}, in {stateName}, {counties}'
                                    locationString.append(string)
                                elif state not in completedStates:
                                    counties = ''.join(counties)
                                    string = f'the following {useCountyOrParish}, {county}, {stateName}'
                                    locationString.append(string)
                                else:
                                    pass
                            finalLocString = []
                            if len(locationString) > 1:
                                for loc in locationString:
                                    finalLocString.append(loc)
                                finalLocString = ', and '.join(finalLocString)
                                finalLocString = ' ' + finalLocString + '. '
                                readoutstring = '\n' + f'\nThe National Weather Service has issued Tornado Watch number {watchNo}, effective until {expireTimeStamp} {timezoneLong}. This watch includes {finalLocString}. Remember, a Tornado Watch means that conditions are favorable for the development of severe weather, including tornadoes, large hail and damaging winds, in, and close to the watch area. While severe weather may not be imminent, persons should remain alert for rapidly changing weather conditions, and listen for later statements and possible warnings. Stay tuned to NOAA Weather Radio, commercial radio and television outlets, or internet sources for the latest severe weather information. ' + '<vtml_pause time="1300"/>'
                                readoutstring = add_colon_to_time(readoutstring)
                                alertReadout.append(readoutstring)
                                alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                            else:
                                finalLocString = ''.join(locationString)
                                finalLocString = ' ' + finalLocString + '. '
                                readoutstring = '\n' + f'\nThe National Weather Service has issued Tornado Watch number {watchNo}, effective until {expireTimeStamp} {timezoneLong}. This watch includes {finalLocString}. Remember, a Tornado Watch means that conditions are favorable for the development of severe weather, including tornadoes, large hail and damaging winds, in, and close to the watch area. While severe weather may not be imminent, persons should remain alert for rapidly changing weather conditions, and listen for later statements and possible warnings. Stay tuned to NOAA Weather Radio, commercial radio and television outlets, or internet sources for the latest severe weather information. ' + '<vtml_pause time="1300"/>'
                                readoutstring = add_colon_to_time(readoutstring)
                                alertReadout.append(readoutstring)
                                alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                        elif feature['properties']['event'] == 'Severe Thunderstorm Watch':
                            alertIDList.append(alertid)
                            event = feature['properties']['event']
                            expireTime = feature['properties']['expires']
                            #2023-02-06T03:00:00-06:00
                            expireTime = datetime.strptime(expireTime[0:-6], '%Y-%m-%dT%H:%M:%S')
                            expireTimeHR = expireTime.strftime('%I')
                            expireTimeMIN = expireTime.strftime('%M')
                            expireTimeTS = expireTime.strftime('%p')
                            if expireTimeMIN == '00':
                                if expireTimeHR[0:1] == '0':
                                    expireTimeStamp = expireTimeHR[1:] + ' ' + expireTimeTS
                                else:
                                    expireTimeStamp = expireTimeHR + ' ' + expireTimeTS
                            else:
                                if expireTimeHR[0:1] == '0':
                                    expireTimeStamp = expireTimeHR[1:] + ':' + expireTimeMIN + ' ' + expireTimeTS
                                else:
                                    expireTimeStamp = expireTimeHR + ':' + expireTimeMIN + ' ' + expireTimeTS
                            affectedZones = {}
                            states = []
                            for zone in feature['properties']['affectedZones']:
                                zoneCall = requests.get(zone, timeout=globalTimeout).text
                                zoneCall = json.loads(zoneCall)
                                state = zoneCall['properties']['state']
                                county = zoneCall['properties']['name']
                                affectedZones[county]=state
                                states.append(state)
                            res = defaultdict(list)
                            for key, val in sorted(affectedZones.items()):
                                res[val].append(key)
                            locationString = []
                            completedStates = []
                            watchNo = feature['properties']['parameters']['VTEC'].split('.')[5]
                            inefficient = watchNo[0:1]
                            if inefficient == '0':
                                watchNo = watchNo[1:]
                            inefficient = watchNo[1:2]
                            if inefficient == '0':
                                watchNo = watchNo[2:]
                            for state in states:
                                stateName = abbrev_to_us_state[state]
                                counties = res[state]
                                useCountiesOrParishes = 'counties' if state not in ['LA', 'AK'] else 'parishes'
                                useCountyOrParish = 'county' if state not in ['LA', 'AK'] else 'parish'
                                if len(counties) > 1 and state not in completedStates:
                                    completedStates.append(state)
                                    insertInt = len(counties) - 1
                                    counties.insert(insertInt, 'and')
                                    counties = ', '.join(counties)
                                    counties = counties.replace('and, ', 'and ')
                                    string = f'the following {useCountiesOrParishes}, in {stateName}, {counties}'
                                    locationString.append(string)
                                elif state not in completedStates:
                                    counties = ''.join(counties)
                                    string = f'the following {useCountyOrParish}, {county}, {stateName}'
                                    locationString.append(string)
                                else:
                                    pass
                            finalLocString = []
                            if len(locationString) > 1:
                                for loc in locationString:
                                    finalLocString.append(loc)
                                finalLocString = ', and '.join(finalLocString)
                                finalLocString = ' ' + finalLocString + '. '
                                readoutstring = '\n' + f'\nThe National Weather Service has issued Severe Thunderstorm Watch number {watchNo}, effective until {expireTimeStamp} {timezoneLong}. This watch includes {finalLocString}. Remember, a Severe Thunderstorm Watch, means that conditions are favorable for the development of severe weather, including large hail and damaging winds, in, and close to the watch area. While severe weather may not be imminent, persons should remain alert for rapidly changing weather conditions, and listen for later statements and possible warnings. Stay tuned to NOAA Weather Radio, commercial radio and television outlets, or internet sources for the latest severe weather information. ' + '<vtml_pause time="1300"/>'
                                readoutstring = add_colon_to_time(readoutstring)
                                alertReadout.append(readoutstring)
                                alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                            else:
                                finalLocString = ''.join(locationString)
                                finalLocString = ' ' + finalLocString + '. '
                                readoutstring = '\n' + f'\nThe National Weather Service has issued Severe Thunderstorm Watch number {watchNo}, effective until {expireTimeStamp} {timezoneLong}. This watch includes {finalLocString}. Remember, a Severe Thunderstorm Watch, means that conditions are favorable for the development of severe weather, including large hail and damaging winds, in, and close to the watch area. While severe weather may not be imminent, persons should remain alert for rapidly changing weather conditions, and listen for later statements and possible warnings. Stay tuned to NOAA Weather Radio, commercial radio and television outlets, or internet sources for the latest severe weather information. ' + '<vtml_pause time="1300"/>'
                                readoutstring = add_colon_to_time(readoutstring)
                                alertReadout.append(readoutstring)
                                alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                    else:
                        alertIDList.append(alertid)
                        readoutstring = 'The following information concerns a ' + feature['properties']['event'] + '.\n' + str(feature['properties']['parameters']['NWSheadline']) + '. \n' + str(feature['properties']['description']).replace('\n', ' ').replace('...', ', ') + '<vtml_pause time="1300"/>'
                        readoutstring = add_colon_to_time(readoutstring)
                        alertReadout.append(readoutstring)
                        event = feature['properties']['event']
                        expireTime = feature['properties']['expires']
                        #2023-02-06T03:00:00-06:00
                        expireTime = datetime.strptime(expireTime[0:-6], '%Y-%m-%dT%H:%M:%S')
                        expireTimeHR = expireTime.strftime('%I')
                        expireTimeMIN = expireTime.strftime('%M')
                        expireTimeTS = expireTime.strftime('%p')
                        if expireTimeMIN == '00':
                            if expireTimeHR[0:1] == '0':
                                expireTimeStamp = expireTimeHR[1:] + ' ' + expireTimeTS
                            else:
                                expireTimeStamp = expireTimeHR + ' ' + expireTimeTS
                        else:
                            if expireTimeHR[0:1] == '0':
                                expireTimeStamp = expireTimeHR[1:] + ':' + expireTimeMIN + ' ' + expireTimeTS
                            else:
                                expireTimeStamp = expireTimeHR + ':' + expireTimeMIN + ' ' + expireTimeTS
                        affectedZones = {}
                        states = []
                        for zone in feature['properties']['affectedZones']:
                            zoneCall = requests.get(zone, timeout=globalTimeout).text
                            zoneCall = json.loads(zoneCall)
                            state = zoneCall['properties']['state']
                            county = zoneCall['properties']['name']
                            affectedZones[county]=state
                            states.append(state)
                        res = defaultdict(list)
                        for key, val in sorted(affectedZones.items()):
                            res[val].append(key)
                        locationString = []
                        completedStates = []
                        for state in states:
                            stateName = abbrev_to_us_state[state]
                            counties = res[state]
                            useCountiesOrParishes = 'counties' if state not in ['LA', 'AK'] else 'parishes'
                            useCountyOrParish = 'county' if state not in ['LA', 'AK'] else 'parish'
                            if len(counties) > 1 and state not in completedStates:
                                completedStates.append(state)
                                insertInt = len(counties) - 1
                                counties.insert(insertInt, 'and')
                                counties = ', '.join(counties)
                                counties = counties.replace('and, ', 'and ')
                                string = f'the following {useCountiesOrParishes}, in {stateName}, {counties}'
                                locationString.append(string)
                            elif state not in completedStates:
                                counties = ''.join(counties)
                                string = f'the following {useCountyOrParish}, {county}, {stateName}'
                                locationString.append(string)
                            else:
                                pass
                        finalLocString = []
                        if len(locationString) > 1:
                            for loc in locationString:
                                finalLocString.append(loc)
                            finalLocString = ', and '.join(finalLocString)
                            finalLocString = 'for ' + finalLocString + '. '
                            alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                        else:
                            finalLocString = ''.join(locationString)
                            finalLocString = 'for ' + finalLocString + '. '
                            alertList.append(f'a {event} has been issued until {expireTimeStamp} {timezoneLong} {finalLocString}')
                else:
                    log.debug('[ALERTSUMMARY] Alert already processed!')
            #except:
            #    pass
        if len(alertList) == 0:
            alertList.append('At this time, no alerts are in effect.')
        alertList = ''.join(alertList)
        #print(f'The following is a summary of watches, warnings, and advisories in effect, for the {stationID} listening area. {alertList}')
        alertReadout = '\n'.join(alertReadout)
        stationID = re.sub(r'(\D)', r'\1 ', stationID, flags=re.DOTALL)
        summary = '<vtml_volume value="200"> <vtml_speed value="110"> ' + f'The following is a summary of watches, warnings, and advisories in effect for the {stationID} listening area. {alertList} <vtml_pause time="1300"/> {alertReadout}' + '<vtml_pause time="1300"/>'

        for phoneme in phonemeDict:
            log.debug('[ALERTSUMMARY PHONEMES] Replacing %s with %s', phoneme, phonemeDict[phoneme])
            summary = str(summary).replace(phoneme, f'<vtml_phoneme alphabet="x-cmu" ph="{phonemeDict[phoneme]}"></vtml_phoneme>')
        for word in replaceDict:
            log.debug('[ALERTSUMMARY PHONEMES] Replacing %s with %s', word, replaceDict[word])
            if '*PAUSE' in replaceDict[word]:
                pauseTime = replaceDict[word].split('*')[1].split('-')[1]
                word = word.replace(f'*PAUSE-{pauseTime}*', f'<vtml_pause time="{pauseTime}"/>')
                summary = str(summary).replace(word, replaceDict[word])
            else:
                summary = str(summary).replace(word, replaceDict[word])

        summary = summary.replace('\n', ' ').replace('\r', ' ')

        log.debug('[ALERTSUMMARY] Final Text: %s', summary)
        path_separator = '\\' if os.name == 'nt' else '/'
        produce_wav_file(summary, 'AlertSummary.wav')

        if "no alerts are in effect" in alertList:
            log.info('[ALERTSUMMARY] No alerts in effect.')
            with open(os.path.join(os.getcwd(), 'NoAlerts.txt'), 'w', encoding='utf-8') as f:
                f.write(f'{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        else:
            if os.path.exists(os.path.join(os.getcwd(), 'NoAlerts.txt')):
                os.remove(os.path.join(os.getcwd(), 'NoAlerts.txt'))
    except requests.exceptions.Timeout:
        log.error("[ALERTSUMMARY] An HTTP Request timed out.")
    except Exception:
        log.error("[ALERTSUMMARY] %s", traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    print('[ALERTSUMMARY] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.')
