#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
BMH Emulation Main Script

This script emulates the behavior of the NWS Broadcast Message Handler (BMH) system
by periodically generating various weather-related audio products and combining
them into a final audio output. The script runs in an infinite loop, updating
the audio files every minute (for time-only updates), with a full refresh cycle
every 10 minutes.
"""

# System-level imports
import os
import sys
import json
import time
import shutil
import logging
import argparse
import traceback
import subprocess

class ColorFormatter(logging.Formatter):
    grey = "\x1b[90m"
    green = "\x1b[92m"
    yellow = "\x1b[93m"
    red = "\x1b[91m"
    reset = "\x1b[0m"

    format_str = "%(asctime)s | %(levelname)-8s | %(message)s"

    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: red + format_str + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logging(verbose, config=None):
    try:
        if config is not None:
            loglevel = config.upper()
        else:
            loglevel = 'DEBUG' if verbose else 'INFO'
        log = logging.getLogger("BMH")
        log.setLevel(loglevel)

        ch = logging.StreamHandler()
        ch.setLevel(loglevel)
        ch.setFormatter(ColorFormatter())
        log.addHandler(ch)
        return log
    except Exception:
        print(f"Error setting up logging: {traceback.format_exc()}")
        sys.exit(1)

try:
    parser = argparse.ArgumentParser(description='BMH Emulation')
    parser.add_argument('--config', default='config.json', help='Path to the config file')
    parser.add_argument('--generate-config', action='store_true', help='Generate a default config file and exit')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging output')
    parser.add_argument('--interactively-configure', action='store_true', help='Run interactive configuration setup')
    args = parser.parse_args()

    config = json.load(open('config.json', encoding='utf-8'))

    # Various products
    from forecast import getForecast
    from alert_summary import getAlertSummary
    from hazardous_weather_outlook import getHazardousWeatherOutlook
    from tropical_weather_outlook import getTropicalWeatherOutlook
    from current_time import getCurrentTime
    from area_observations import getObservations
except FileNotFoundError:
    log = setup_logging(args.verbose, None)
    if args.generate_config:
        from utils import generate_default_config
        generate_default_config(log)
        sys.exit(0)
    elif args.interactively_configure:
        from utils import interactive_config_setup
        interactive_config_setup(log)
        sys.exit(0)
    else:
        log.critical("Error: config.json file not found. Please ensure it exists in the current directory.")
        sys.exit(1)
except json.JSONDecodeError as e:
    log = setup_logging(args.verbose, None)
    if args.generate_config:
        from utils import generate_default_config
        generate_default_config(log)
        sys.exit(0)
    else:
        log.critical(f"Error parsing config.json: {e.msg} at line {e.lineno} column {e.colno}\nMaybe run --generate-config to create a new, safe default?")
        sys.exit(1)
except Exception as e:
    log = setup_logging(args.verbose, None)
    log.critical(f"Error loading config.json: {traceback.format_exc()}")
    sys.exit(1)

path_separator = '\\' if os.name == 'nt' else '/'

PRODUCT_GENERATORS = (
    getForecast,
    getAlertSummary,
    getHazardousWeatherOutlook,
    getTropicalWeatherOutlook,
    getCurrentTime,
    getObservations,
)

def refresh_products():
    for generator in PRODUCT_GENERATORS:
        generator()

def combine_audio(output_name, AUDIO_SEQUENCE):
    sox_location = shutil.which(f'binary{path_separator}sox.exe') if os.name == 'nt' else shutil.which('sox')
    sox = subprocess.Popen((sox_location, '-q', *AUDIO_SEQUENCE, output_name))
    sox.wait()

def run_time_updates(minutes, AUDIO_SEQUENCE):
    for remaining in range(minutes, 0, -1):
        plural = 's' if remaining != 1 else ''
        log.info('[BMH] Time update completed. Continuing time updates for the next %d minute%s...', remaining, plural)
        getCurrentTime()
        combine_audio('FINAL_CYCLE.wav', AUDIO_SEQUENCE)
        time.sleep(60)

def main(log):
    try:
        log.info('[BMH] Setting up BMH Emulation environment...')
        os.makedirs(f'..{path_separator}bmh_wav', exist_ok=True)
        os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmh_wav"))
        for file in os.listdir():
            if file.endswith('.wav'):
                os.remove(file)
        os.chdir('..')
        _ = os.remove('FINAL_CYCLE.wav') if os.path.exists('FINAL_CYCLE.wav') else None
        _ = os.remove('NoAlerts.txt') if os.path.exists('NoAlerts.txt') else None
        log.info('[BMH] Starting BMH Emulation. Hit Ctrl+C to stop at any time...')
        while True:
            refresh_products()
            no_alerts_file = os.path.join(os.getcwd(), 'NoAlerts.txt')

            if os.path.exists(no_alerts_file):
                if config['Forecast']['enableTropicalForecast'] is False:
                    AUDIO_SEQUENCE = (
                        f'bmh_wav{path_separator}Forecast.wav',
                        f'bmh_wav{path_separator}Observations.wav',
                        f'bmh_wav{path_separator}HWO.wav',
                        f'bmh_wav{path_separator}CurrentTime.wav',
                    )
                else:
                    AUDIO_SEQUENCE = (
                        f'bmh_wav{path_separator}Forecast.wav',
                        f'bmh_wav{path_separator}Observations.wav',
                        f'bmh_wav{path_separator}HWO.wav',
                        f'bmh_wav{path_separator}CurrentTime.wav',
                    )

            else:
                if config['Forecast']['enableTropicalForecast'] is False:
                    AUDIO_SEQUENCE = (
                        f'bmh_wav{path_separator}AlertSummary.wav',
                        f'bmh_wav{path_separator}Forecast.wav',
                        f'bmh_wav{path_separator}Observations.wav',
                        f'bmh_wav{path_separator}HWO.wav',
                        f'bmh_wav{path_separator}CurrentTime.wav',
                    )
                else:
                    AUDIO_SEQUENCE = (
                        f'bmh_wav{path_separator}AlertSummary.wav',
                        f'bmh_wav{path_separator}Forecast.wav',
                        f'bmh_wav{path_separator}Observations.wav',
                        f'bmh_wav{path_separator}HWO.wav',
                        f'bmh_wav{path_separator}TWO.wav',
                        f'bmh_wav{path_separator}CurrentTime.wav',
                    )

            log.info('[BMH] Combining all audio files into FINAL_CYCLE.wav...')
            combine_audio('FINAL_CYCLE.wav', AUDIO_SEQUENCE)
            log.info('[BMH] All tasks completed successfully. Re-running in approx. 1 minute (time-only)...')
            time.sleep(60)
            run_time_updates(9, AUDIO_SEQUENCE)
            log.info('[BMH] Time update completed. 10 minutes has passed. Restarting full cycle now...')
            os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bmh_wav"))
            for file in os.listdir():
                if file.endswith('.wav'):
                    os.remove(file)
            os.chdir('..')
    except KeyboardInterrupt:
        log.info('[BMH] Stopping BMH Emulation as requested by user. Goodbye!')
        sys.exit(0)
    except Exception:
        log.error("[BMH] Error: %s", traceback.format_exc())
        sys.exit(1)

if __name__ == '__main__':
    if args.generate_config:
        log = setup_logging(args.verbose, config["logLevel"] if "logLevel" in config else None)
        from utils import generate_default_config
        generate_default_config(log)
        sys.exit(0)
    if args.interactively_configure:
        log = setup_logging(args.verbose, config["logLevel"] if "logLevel" in config else None)
        from utils import interactive_config_setup
        interactive_config_setup(log)
        sys.exit(0)
    else:
        log = setup_logging(args.verbose, config["logLevel"] if "logLevel" in config else None)
        main(log)
