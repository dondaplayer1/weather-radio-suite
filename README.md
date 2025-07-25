
# WeatherRadioSuite
A faithful recreation of NOAA's National Weather Service - NOAA Weather Radio "Broadcast Message Handler" system, in Python.
## What can it do?

> - Generate NWR-like audio files utilizing the VoiceText Paul voice
> - Poll weather information for any US location utilizing the NWS API
> - Supports Zone Forecast, Local Observations, Hazardous Weather Outlook, Tropical Weather Outlook, Current Time, Local Alert Summary
> - Fully customizable product headers
> - Customizable phoneme/replacement table
> - Randomized observation intro (Like NWS Midland, TX)

## Requirements

- Windows 10/11 (7 may work; untested and unsupported!)
- Python 3.8+ with requests and datetime installed

# Initial setup

## WeatherRadioSuite-LIB

Download the supporting libraries and the TTS engine from a secure download server, located here: https://cdn.dondaplayer.com/WeatherRadioSuite-LIB.zip

Once you've cloned the repo, extract the contents of WeatherRadioSuite-LIB.zip to the root of the project.

Ideally, your topography should look something like this:

WeatherRadioSuite:
 - binary/
 - data-common/
 - data-paul/
 - include/
 - the rest of the files (.py, .bat, etc)

You can now continue with setup.
## Observations

Go through config.json and configure it to your liking. I recommend spacing out your observation locations evenly. If you're unsure if a location has observations, try placing the location code in https://api.weather.gov/stations/{airportCode}/observations/latest. For example, if I wanted the Kalamazoo/Battle Creek International Airport, I would put "KAZO" in {airportCode} in that link. 

Populate "mainObsCode" with your main observation. Then, for regionalObsCodes, place as many codes as you would like for the rest of your observations. Your  opener list can include as many as you would like, you just have to make sure you have each number in openerList for each opener in openers. If you only want one, remove everything except #1 in both places.

cityNameDef is where you can define each location. That way you're not locked in to what the API has the location as. dividers is where you can add a 'divider' before a specific location. For example, after my main observation plays, I have it say "Around our local area, Battle Creek..."
## Forecast
Here you can define how many forecast days you want in your forecast. Default is 14, this is odd because it's days and nights. Technically this can be as high as 15, however 14 is the safest as it's not always 15 segments.
The zone is what you want the forecast to be. MIZ072 is Kalamazoo Co., MI.
Pre/Post are what come before and after your forecast. If you don't want one, the other, or both, just make them blank.
## HWO
Set your office's code here.
## Alert Summary
Here, you need to set the callsign of your station. The Alert Summary has a fixed format, as I never got to the point of making it customizable.
You also need to set the zones you want alerts for. I have it set as MIC077, which is Kalamazoo Co., MI. You *can* set multiple, however it's not recommended and may result in duplicate alerts.
timezoneLong could be automated, however it's not. Set it as you see fit.
## Misc. configuration
At the top, you'll see the "ttsSpeed", "endPause", and "currentTime". TTS Speed should be whatever VoiceText speed you want- there's a discord server that has this information [here](https://discord.gg/JSJXd8pMt2). "endPause" is how long the pause at the end of every file should be, to keep it uniform. 

As for currentTime, you set your time script. Don't change this if you don't care. Also, keep date off unless you *really* want it. You'll need to change the timezone as well, it is not automatic yet. 

If you don't want your station ID to be it's own static file, you can also just put it before or after the current time script within the file. This is a bit of an advanced option though, and will slow down generation, as it will synthesize your ID every single time it re-pulls the time. So, although this is an option, I do NOT recommend it.
## Phonemes/replacements
In "phonemeDB.json", you'll find a common list of replacements that I have pre-curated. If you're not a fan of some of them, you can remove them, and also add to them as you see fit. There's information for these in the discord server I listed above. **That server is NOT related to this project and is purely just a resource for the VoiceText Paul voice.**
# Usage
Once you've done the initial setup, run "Automation_Controller.bat". This will run all of your scripts at initial setup, and then count down 10 minutes after the last one until the script restarts and pulls everything again. The current time is ran every 10 seconds. This is also where you enable/disable scripts if you don't want to use them- instructions are in the file.

I cannot and **will not** help you set this software up. I have explained a little on how to use it, and eventually I'd like to make proper documentation on every way you can utilize the software. However for now it's not possible.

I recommend using a free software called "ZaraRadio" as your playout/playlist management program. It's quite robust for this purpose and offers some relatively powerful automation in a simple package. You can set up hourly scheduled events if you'd like your station ID played at a certain interval. 

If a file was not mentioned in this "README", ***Do Not Touch It***. It is likely crucial to the function of the program.
# Other things

If you encounter an issue with the software, feel free to create an issue. I can't guarantee I will be able to fix everything, which is why this is open source. If it's something you can fix, feel free to create a pull request and it will be reviewed in a timely manner.
