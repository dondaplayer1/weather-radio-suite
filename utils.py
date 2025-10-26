
import os
import datetime
import traceback
import subprocess
import shutil
import logging
import tzlocal
import pytz

log = logging.getLogger("BMH")

def produce_wav_file(text, output_module_name):
    try:
        path_separator = '\\' if os.name == 'nt' else '/'

        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "binary"))

        with open('input1.txt', 'w', encoding='utf-8') as f:
            f.write(text)

        # Generate initial WAV file using voice synthesis
        wait = subprocess.Popen(['voicetext_paul.exe'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait.wait()

        # Convert to proper WAV format using SoX
        sox_location = shutil.which('sox.exe') if os.name == 'nt' else shutil.which('sox')
        wait2 = subprocess.Popen([str(sox_location), '-q', 'output.wav', '-r', '44100', '-b', '16', '-c', '1', f"..{path_separator}bmh_wav{path_separator}{output_module_name}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait2.wait()

        # Clean up temporary files
        os.remove('output.wav')
        os.remove('input1.txt')
        os.chdir('..')

        log.info("[UTILS] Successfully produced WAV file for %s", output_module_name)

    except Exception:
        log.error("[UTILS] Error producing WAV file: %s", traceback.format_exc())

def generate_default_config():
    log.info("[UTILS] Generating default config.json file...")

    local_tz = tzlocal.get_localzone()
    timeZone = pytz.timezone(str(local_tz)).localize(pytz.datetime.datetime.now()).tzname()
    timeZoneFull = datetime.datetime.now().astimezone().tzname()

    log.info("[UTILS] Detected timezone as %s (%s).", timeZone, timeZoneFull)

    default_config = {
        "ttsSpeed": "110",
        "endPause": "1300",
        "logLevel": "INFO",
        "globalHTTPTimeout": "15",
        "currentTime": {
            "timeScript": "The current time is.",
            "timeZone": "EDT",
            "dateEnable": False,
            "dateScript": "Today's date is. "
        },
        "Observations": {
            "mainObsCode": "KAZO",
            "regionalObsCodes": ["KBTL", "KHAI", "KLWA", "KGRR", "KLAN", "KDET", "KFNT", "KLDM", "KY31", "KTVC", "KAPN", "KANJ", "KSAW", "KMKE", "KLOT", "KFWA"],
            "openerList": [1, 2 , 3, 4],
            "openers": {
                "1": "Got weather? The michigan mezonet does and here are your TIME observations. ",
                "2": "From the mountains in the north to the rolling farm lands in the south, here are your TIME michigan weather observations. ",
                "3": "In a hurry? Don't worry, because here are your TIME weather observations.",
                "4": "At the top of the hour, "
            },
            "cityNameDef": {
                "KAZO": "Kalamazoo",
                "KBTL": "Battle Creek",
                "KHAI": "Three Rivers",
                "KLWA": "South Haven",
                "KGRR": "The National Weather Service forecast office in Grand Rapids",
                "KLAN": "Lansing",
                "KDET": "Detroit",
                "KFNT": "Flint",
                "KLDM": "Ludington",
                "KY31": "West Branch",
                "KTVC": "Traverse City",
                "KAPN": "Alpena",
                "KANJ": "Sault Ste. Marie",
                "KSAW": "Marquette",
                "KMKE": "Milwaukee",
                "KLOT": "Chicago",
                "KFWA": "Fort Wayne"
            },
            "dividers": {
                "KBTL": "Around our local area, ",
                "KGRR": "At ",
                "KLAN": "Around the rest of the state, to our east, ",
                "KLDM": "Looking north, ",
                "KANJ": "In the upper peninsula, ",
                "KSAW": "And, ",
                "KMKE": "In neighboring states, "
            }
        },
        "Forecast": {
            "forecastDays": "14",
            "forecastZone": "MIZ072",
            "forecastPre": "Here is your official national weather service forecast for the Kalamazoo listening area.",
            "forecastPost": "For additional weather and climate information, please visit weather, dot g o v, forward slash, g, r, r.",
            "enableTropicalForecast": False
        },
        "HWO": {
            "office": "GRR"
        },
        "AlertSummary": {
            "stationID": "WNG773",
            "alertZones": ["MIC077"],
            "timezoneLong": "Eastern Daylight Time"
        }
    }

    with open('config.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(default_config, f, indent=4)

    log.info("[UTILS] Generated default config.json file with timezone awareness.")

def interactive_config_setup():
    log.info("[UTILS] Welcome to the interactive configuration setup! This will guide you through setting up your config.json file step-by-step.")
    input("Press Enter to continue with setup...")
    ttsSpeed = input("Enter TTS Speed (default 110): ") or "110"
    endPause = input("Enter End Pause in milliseconds (default 1300): ") or "1300"
    logLevel = input("Enter Log Level (DEBUG, INFO, WARNING, ERROR) (default INFO): ") or "INFO"
    logLevel = logLevel.upper()
    globalHTTPTimeout = input("Enter Global HTTP Timeout in seconds (default 15): ") or "15"
    currentTimeScript = input("Enter Current Time Script (default 'The current time is.'): ") or "The current time is."

    dateEnableInput = input("Enable Date Announcement? (yes/no) (default no): ") or "no"
    dateEnable = True if dateEnableInput.lower() in ['yes', 'y'] else False
    if dateEnable:
        dateScript = input("Enter Date Script (default 'Today's date is. '): ") or "Today's date is. "
    else:
        dateScript = "Today's date is. "

    mainObsCode = input("Enter Main Observation Station Code (default KAZO): ") or "KAZO"

    regionalObsCodesInput = input("Enter Regional Observation Station Codes separated by commas (default is in config.example.json if you want to see what it looks like): ") or ""
    regionalObsCodes = [code.strip() for code in regionalObsCodesInput.split(",")] if regionalObsCodesInput else []

    shouldAddOpeners = input("Enable Openers? (yes/no) (default no): ") or "no"
    if shouldAddOpeners.lower() in ['yes', 'y']:
        keep_adding = True
        openers = {}
        idx = 0
        while keep_adding:
            idx += 1
            value = input(f"Enter Opener Value for #{idx}, or enter \"done\" to finish adding openers: ")
            if value.lower() == 'done':
                keep_adding = False
                break
            openers[idx] = value
        openerList = list(openers.keys())
    else:
        openers = {}
        openerList = []

    if len(regionalObsCodes) > 0:
        cityNameDef = {}
        for cityname in regionalObsCodes:
            cityNameDef[cityname] = input(f"Enter City Name for {cityname}: ")
        cityNameDef = {key: value for key, value in cityNameDef.items()}
    else:
        cityNameDef = {}
        cityNameDef[mainObsCode] = input(f"Enter City Name for {mainObsCode}: ")
        cityNameDef = {key: value for key, value in cityNameDef.items()}

    shouldAddDividers = input("Enable Dividers? (yes/no) (default no): ") or "no"
    if shouldAddDividers.lower() in ['yes', 'y']:
        dividers = {}
        for citycode in regionalObsCodes:
            dividerText = input(f"Enter Divider Text for {citycode} (or leave blank to skip): ")
            if dividerText.strip() != "":
                dividers[citycode] = dividerText
    else:
        dividers = {}
    dividersDict = {key: value for key, value in dividers.items()}

    forecastDays = input("Enter Forecast Days (default 14): ") or "14"
    forecastZone = input("Enter Forecast Zone (default MIZ072): ") or "MIZ072"
    forecastPre = input("Enter Forecast Pre-Script (default nothing): ") or ""
    forecastPost = input("Enter Forecast Post-Script (default nothing): ") or ""

    enableTropicalForecastInput = input("Enable Tropical Forecast? (yes/no) (default no): ") or "no"
    enableTropicalForecast = True if enableTropicalForecastInput.lower() in ['yes', 'y'] else False

    hwoOffice = input("Enter HWO Office Code (default GRR): ") or "GRR"

    alertStationID = input("Enter NWS Station ID (default WNG773): ") or "WNG773"
    alertZonesInput = input("Enter Alert Zones separated by commas (default MIC077): ") or "MIC077"
    alertZones = [zone.strip() for zone in alertZonesInput.split(",")] if alertZonesInput else []

    log.info("[UTILS] Configuration setup complete! Generating your custom config.json now...")

    local_tz = tzlocal.get_localzone()
    timeZone = pytz.timezone(str(local_tz)).localize(pytz.datetime.datetime.now()).tzname()
    timeZoneFull = datetime.datetime.now().astimezone().tzname()

    log.info("[UTILS] Detected timezone as %s (%s).", timeZone, timeZoneFull)

    default_config = {
        "ttsSpeed": ttsSpeed,
        "endPause": endPause,
        "logLevel": logLevel,
        "globalHTTPTimeout": globalHTTPTimeout,
        "currentTime": {
            "timeScript": currentTimeScript,
            "timeZone": timeZone,
            "dateEnable": dateEnable,
            "dateScript": dateScript
        },
        "Observations": {
            "mainObsCode": mainObsCode,
            "regionalObsCodes": regionalObsCodes,
            "openerList": openerList,
            "openers": openers,
            "cityNameDef": cityNameDef,
            "dividers": dividersDict
        },
        "Forecast": {
            "forecastDays": forecastDays,
            "forecastZone": forecastZone,
            "forecastPre": forecastPre,
            "forecastPost": forecastPost,
            "enableTropicalForecast": enableTropicalForecast
        },
        "HWO": {
            "office": hwoOffice
        },
        "AlertSummary": {
            "stationID": alertStationID,
            "alertZones": alertZones,
            "timezoneLong": timeZoneFull
        }
    }

    with open('config.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(default_config, f, indent=4)

    log.info("[UTILS] Generated new, custom config.json file with timezone awareness.")


if __name__ == '__main__':
    print("[UTILS] This is one of the BMH modules, not a standalone program. Please run main.py to execute the full BMH program.")
