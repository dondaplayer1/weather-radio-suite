
import os
import datetime
import traceback
import subprocess
import shutil
import logging
import time
import tzlocal
import pytz
from dataclasses import dataclass
from typing import Generator, Optional

global_prompt = ""
clicked_yes = False
clicked_no = False

def produce_wav_file(text, output_module_name):
    try:
        log = logging.getLogger("BMH")

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

def generate_default_config(log):
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
            "timeZone": timeZone,
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
            "timezoneLong": timeZoneFull
        }
    }

    with open('config.json', 'w', encoding='utf-8') as f:
        import json
        json.dump(default_config, f, indent=4)

    log.info("[UTILS] Generated default config.json file with timezone awareness.")

def interactive_config_setup(log):
    log.info("[UTILS] Starting interactive configuration setup...")

    try:
        from textual import events
        from textual.app import App, ComposeResult
        from textual.containers import Vertical
        from textual.message import Message
        from textual.widgets import Footer, Header, Static, TextArea
        from textual.widgets import Button as ButtonWidget
    except ImportError as exc:
        log.error("[UTILS] Textual is required for the interactive setup. Install it with 'pip install textual'. (%s)", exc)
        raise

    @dataclass
    class Step:
        prompt: str
        default: str = ""
        placeholder: str = ""

    class ConfigWizard(App):
        CSS = """
        * {
            align: center middle;
        }

        TextArea {
            border: round $accent;
            height: 30%;
        }

        Button {
            width: 10;
            margin: 1 2;
            align: center middle;
        }

        #form {
            width: 100vw;
            max-width: 100vw;
            padding: 1 2;
            align: center middle;
        }

        #yes_button {
            background: green;
            width: 10;
            height: 3;
        }

        #yes_button:hover {
            background: darkgreen;
        }

        #no_button {
            background: red;
            width: 10;
            height: 3;
        }

        #no_button:hover {
            background: darkred;
        }

        .hidden {
            display: none;
        }
        """

        BINDINGS = [("ctrl+c", "quit", "Quit"), ("escape", "quit", "Quit")]

        class ResponseTextArea(TextArea):
            class Submitted(Message):
                def __init__(self, text_area: "ConfigWizard.ResponseTextArea", value: str) -> None:
                    super().__init__()
                    self.text_area = text_area
                    self.value = value

                @property
                def control(self) -> "ConfigWizard.ResponseTextArea":
                    return self.text_area

            async def _on_key(self, event: events.Key) -> None:
                self._restart_blink()
                if self.read_only:
                    return

                key = event.key

                if key in ("enter", "ctrl+m"):
                    event.stop()
                    event.prevent_default()
                    self.post_message(self.Submitted(self, self.text))
                    return

                insert_values: dict[str, str] = {}
                if key in ("ctrl+shift+insert"):
                    insert_values[key] = "\n"

        class Button(ButtonWidget):
            class Pressed(Message):
                def __init__(self, button: "ConfigWizard.Button") -> None:
                    super().__init__()
                    self.button = button

                @property
                def control(self) -> "ConfigWizard.Button":
                    return self.button

            def yes_handler(self, event: Pressed) -> None:
                global clicked_yes
                global clicked_no
                clicked_yes = True
                clicked_no = False
                return

            def no_handler(self, event: Pressed) -> None:
                global clicked_yes
                global clicked_no
                clicked_no = True
                clicked_yes = False
                return

        def __init__(self) -> None:
            super().__init__()
            self.answers: dict[str, object] = {}
            self._steps_iter: Optional[Generator[Step, str, None]] = None
            self._current_step: Optional[Step] = None
            self._awaiting_confirmation: bool = False

        def compose(self) -> ComposeResult:
            yield Header()
            with Vertical(id="form"):
                yield Static("", id="prompt")
                if "using the default" not in global_prompt:
                    yield self.ResponseTextArea(
                        placeholder="",
                        id="response",
                        soft_wrap=True,
                        show_line_numbers=False,
                        highlight_cursor_line=False,
                    )
                yield ButtonWidget("Yes", id="yes_button", classes="hidden")
                yield ButtonWidget("No", id="no_button", classes="hidden")
                yield Static("Press Enter to accept the default value that comes in the example config. Press Ctrl+C or Escape to cancel without saving your changes.", id="hint")
            yield Footer()

        def on_mount(self) -> None:
            self._steps_iter = self._steps()
            self._advance("")

        def action_quit(self) -> None:
            self.exit(None)

        def on_response_text_area_submitted(
            self, event: "ConfigWizard.ResponseTextArea.Submitted"
        ) -> None:
            self._submit_response(event.value)

        def _submit_response(self, value: Optional[str] = None) -> None:
            response = self.query_one("#response", self.ResponseTextArea)
            if value is None:
                value = response.text
            if self._current_step is not None and not value:
                value = self._current_step.default
            self._advance(value)

        def _advance(self, user_input: str) -> None:
            prompt_widget = self.query_one("#prompt", Static)
            input_widget = self.query_one("#response", self.ResponseTextArea)

            try:
                if self._current_step is None:
                    assert self._steps_iter is not None
                    step = next(self._steps_iter)
                else:
                    assert self._steps_iter is not None
                    step = self._steps_iter.send(user_input)
            except StopIteration:
                self.exit(self.answers)
                return

            self._current_step = step

            global global_prompt

            global_prompt = step.prompt
            input_widget.placeholder = step.placeholder or step.default
            input_widget.text = ""

            if "using the default" not in global_prompt:
                prompt_widget.update(global_prompt)

            else:
                input_widget.classes = "hidden"
                input_widget.visible = False
                yes_button = self.query_one("#yes_button", ButtonWidget)
                no_button = self.query_one("#no_button", ButtonWidget)
                yes_button.classes = ""
                no_button.classes = ""
                prompt_widget.update(f"[bold red]{global_prompt}[/bold red]\n\n{step.placeholder}")
                global clicked_yes
                global clicked_no
                clicked_yes = False
                clicked_no = False
                self._awaiting_confirmation = True
                self.call_after_refresh(no_button.focus)
                return

            self.call_after_refresh(input_widget.focus)

        def on_button_pressed(self, event: ButtonWidget.Pressed) -> None:
            if not self._awaiting_confirmation:
                return

            button_id = event.button.id
            if button_id not in {"yes_button", "no_button"}:
                return

            event.stop()

            input_widget = self.query_one("#response", self.ResponseTextArea)
            yes_button = self.query_one("#yes_button", ButtonWidget)
            no_button = self.query_one("#no_button", ButtonWidget)
            yes_button.classes = "hidden"
            no_button.classes = "hidden"
            input_widget.visible = True
            input_widget.classes = ""
            input_widget.text = ""

            choice = "yes" if button_id == "yes_button" else "no"

            global clicked_yes
            global clicked_no
            clicked_yes = choice == "yes"
            clicked_no = choice == "no"

            self._awaiting_confirmation = False

            self.call_after_refresh(lambda selection=choice: self._advance(selection))

        def _steps(self) -> Generator[Step, str, None]:
            tts_speed = (yield Step("Enter TTS Speed (default 110): ", "110", "This is how fast the TTS will speak.")).strip()
            self.answers["ttsSpeed"] = tts_speed or "110"

            end_pause = (yield Step("Enter End Pause in milliseconds (default 1300): ", "1300", "This is the pause duration in milliseconds after the TTS ends each sentence.")).strip()
            self.answers["endPause"] = end_pause or "1300"

            log_level = (yield Step("Enter Log Level (DEBUG, INFO, WARNING, ERROR) (default INFO): ", "INFO", "How much logging do you want?")).strip()
            self.answers["logLevel"] = (log_level or "INFO").upper()

            http_timeout = (yield Step("Enter Global HTTP Timeout in seconds (default 15): ", "15", "How long should each page try and load before giving up?")).strip()
            self.answers["globalHTTPTimeout"] = http_timeout or "15"

            current_time_script = (yield Step("Enter Current Time Script (default 'The current time is.'): ", "The current time is.", "ex. Entering \"The current time is.\" would mean that sentence and then the time would be read out, you can add the station ID tagline here if you wish.")).strip()
            self.answers["currentTimeScript"] = current_time_script or "The current time is."

            date_enable_input = (yield Step("Enable Date Announcement? (yes/no) (default no): ", "no", "Usually not recommended.")).strip().lower()
            date_enable = date_enable_input in ("yes", "y")
            self.answers["dateEnable"] = date_enable

            if date_enable:
                date_script = (yield Step("Enter Date Script (default 'Today's date is. '): ", "Today's date is. ", "ex. Entering \"Today's date is.\" would mean that sentence would be read, then the date would be read out.")).strip()
                self.answers["dateScript"] = date_script or "Today's date is. "
            else:
                self.answers["dateScript"] = "Today's date is. "

            main_obs_code = (yield Step("Enter Main Observation Station Code (default KAZO): ", "KAZO", "You can find this at https://www.weather.gov/nwr/wfo_nwr under \"Call Sign\", just remember to add a \"K\" before the code.")).strip()
            self.answers["mainObsCode"] = main_obs_code or "KAZO"
            keep_going = True if main_obs_code == "KAZO" else False
            while self.answers["mainObsCode"] == "" or keep_going is True:
                keep_going = True
                confirm = (yield Step("You are using the default KAZO observation code. Are you sure? (yes/no) (default no): ", "yes", "KAZO is for Kalamazoo, MI. If you are not in that area, please enter your local observation station code.")).strip().lower()
                if confirm not in ("yes", "y"):
                    main_obs_code = (yield Step("Enter Main Observation Station Code: ", "", "You can find this at https://www.weather.gov/nwr/wfo_nwr under \"Call Sign\", just remember to add a \"K\" before the code.")).strip()
                    self.answers["mainObsCode"] = main_obs_code
                    if self.answers["mainObsCode"] != "":
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

            regional_codes_input = (yield Step("Enter Regional Observation Airport Codes separated by commas (leave blank for none): ", "", "ex. \"KBTL,KHAI,KLWA,KGRR...\" would mean 4 regional codes and observations from those airports would be reported.")).strip()
            if regional_codes_input:
                regional_codes = [code.strip() for code in regional_codes_input.split(",") if code.strip()]
            else:
                regional_codes = []
            self.answers["regionalObsCodes"] = regional_codes
            if regional_codes == []:
                confirm_no_regional = (yield Step("You are using the default of having NO regional observation stations. Are you sure? (yes/no) (default no): ", "yes", "It's usually recommended to have at least a few regional observations for a broader view of the weather. If you don't know your regional observation locations, listen to your local weather radio broadcast for a few minutes and see if you can identify them!")).strip().lower()
                if confirm_no_regional not in ("yes", "y"):
                    regional_codes_input = (yield Step("Enter Regional Observation Airport Codes separated by commas (leave blank for none): ", "", "ex. \"KBTL,KHAI,KLWA,KGRR...\" would mean 4 regional codes and observations from those airports would be reported.")).strip()
                    if regional_codes_input:
                        regional_codes = [code.strip() for code in regional_codes_input.split(",") if code.strip()]
                    else:
                        regional_codes = []
                    self.answers["regionalObsCodes"] = regional_codes

            openers_enabled = (yield Step("Enable Openers? (yes/no) (default no): ", "no", "Some stations, like Midland, TX, have little \"openers\" before the forecast. You can enable this here by saying yes.")).strip().lower() in ("yes", "y")
            openers: dict[int, str] = {}
            if openers_enabled:
                idx = 1
                while True:
                    opener_value = (yield Step(f"Enter Opener Value for #{idx} (type 'done' to finish): ", "done", "ex. \"Got weather? The michigan mezonet does and here are your observations.\"")).strip()
                    if not opener_value or opener_value.lower() == "done":
                        break
                    openers[idx] = opener_value
                    idx += 1
            self.answers["openers"] = openers
            self.answers["openerList"] = list(openers.keys())

            city_name_def: dict[str, str] = {}
            if regional_codes:
                city_label = f"Enter the city name for airport code {self.answers['mainObsCode']}: "
                city_name = (yield Step(city_label, "Kalamazoo", "ex. Kalamazoo")).strip()
                city_name_def[self.answers["mainObsCode"]] = city_name or "Kalamazoo"
                keep_going = True if city_name == "Kalamazoo" else False
                while keep_going is True:
                    keep_going = True
                    confirm_city = (yield Step("You are using the default city name of Kalamazoo. Are you sure? (yes/no) (default no): ", "yes", "Kalamazoo is for KAZO and vice versa. If you are not in that local area, please enter your local city name.")).strip().lower()
                    if confirm_city not in ("yes", "y"):
                        city_name = (yield Step(f"Enter the city name for airport code {self.answers['mainObsCode']}: ", "", "ex. Kalamazoo")).strip()
                        city_name_def[self.answers["mainObsCode"]] = city_name
                        if city_name_def[self.answers["mainObsCode"]] != "":
                            keep_going = False
                        else:
                            keep_going = True
                    else:
                        keep_going = False
                for city_code in regional_codes:
                    city_label = f"Enter the city name for airport code {city_code}: "
                    city_name = (yield Step(city_label, "", "ex. Kalamazoo")).strip()
                    keep_going = True if city_name == "" else False
                    while keep_going is True:
                        keep_going = True
                        confirm_city = (yield Step(f"You are using the default, blank city name for airport code {city_code}. Are you sure? (yes/no) (default no): ", "yes", "You cannot leave any city names blank.")).strip().lower()
                        if confirm_city not in ("yes", "y"):
                            city_name = (yield Step(f"Enter the city name for airport code {city_code}: ", "", "ex. Kalamazoo")).strip()
                            if city_name != "":
                                keep_going = False
                            else:
                                keep_going = True
                        else:
                            keep_going = False
                    city_name_def[city_code] = city_name
            else:
                single_code = self.answers["mainObsCode"]
                city_name = (yield Step(f"Enter the city name for airport code {single_code}: ", "Kalamazoo", "ex. Kalamazoo")).strip()
                city_name_def[single_code] = city_name or "Kalamazoo"
            self.answers["cityNameDef"] = city_name_def
            keep_going = True if city_name == "Kalamazoo" else False
            while keep_going is True:
                keep_going = True
                confirm_city = (yield Step("You are using the default city name of Kalamazoo. Are you sure? (yes/no) (default no): ", "yes", "Kalamazoo is for KAZO and vice versa. If you are not in that local area, please enter your local city name.")).strip().lower()
                if confirm_city not in ("yes", "y"):
                    city_name = (yield Step(f"Enter the city name for airport code {single_code}: ", "", "ex. Kalamazoo")).strip()
                    city_name_def[single_code] = city_name
                    self.answers["cityNameDef"] = city_name_def
                    if city_name_def[single_code] != "":
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

            dividers_enabled = (yield Step("Enable Observation dividers? (yes/no) (default no): ", "no", "These are custom strings used to divvy up the observations by region. This lets you enter custom text before each city's observations are read out.")).strip().lower() in ("yes", "y")
            dividers: dict[str, str] = {}
            if dividers_enabled and regional_codes:
                for city_code in regional_codes:
                    divider_prompt = f"Enter Divider Text for Airport Code {city_code} ({city_name_def.get(city_code, '')}) (leave blank to skip): "
                    divider_text = (yield Step(divider_prompt, "", "ex. \"Here are some observations from across the region. In\" would be added before the city below if you set this to that sentence.")).strip()
                    if divider_text:
                        dividers[city_code] = divider_text
            self.answers["dividers"] = dividers

            forecast_days = (yield Step("Enter Forecast Days (default 14): ", "14", "The number of days to include in the forecast. Typically, this is 14 days (2 weeks).")).strip()
            self.answers["forecastDays"] = forecast_days or "14"

            forecast_zone = (yield Step("Enter Forecast Zone (default MIZ072): ", "MIZ072", "You can find this by visiting https://www.arcgis.com/apps/mapviewer/index.html?url=https://mapservices.weather.noaa.gov/static/rest/services/nws_reference_maps/nws_reference_map/MapServer&source=sd and enabling the \"Public Weather Zone Forecasts\" layer. Click the link, wait for ArcGIS to load, then click the arrow next to \"Nws reference map\", then \"Weather Zone Forecasts\", then finally click the eye icon next to \"Public Weather Zone Forecasts\". Zoom in to your county and the zone will be a string like \"MI072\" on the map itself. Just add a letter Z (for Zone) between the state abbreviation and the zone ID.")).strip()
            self.answers["forecastZone"] = forecast_zone or "MIZ072"
            keep_going = False if forecast_zone != "MIZ072" else True
            while keep_going is True:
                keep_going = True
                confirm_zone = (yield Step("You are using the default MIZ072 forecast zone. Are you sure? (yes/no) (default no): ", "yes", "MIZ072 is for Kalamazoo, MI. If you are not in that area, please enter your local forecast zone.")).strip().lower()
                if confirm_zone not in ("yes", "y"):
                    forecast_zone = (yield Step("Enter Forecast Zone: ", "", "You can find this by visiting https://www.arcgis.com/apps/mapviewer/index.html?url=https://mapservices.weather.noaa.gov/static/rest/services/nws_reference_maps/nws_reference_map/MapServer&source=sd and enabling the \"Public Weather Zone Forecasts\" layer. Click the link, wait for ArcGIS to load, then click the arrow next to \"Nws reference map\", then \"Weather Zone Forecasts\", then finally click the eye icon next to \"Public Weather Zone Forecasts\". Zoom in to your county and the zone will be a string like \"MI072\" on the map itself. Just add a letter Z (for Zone) between the state abbreviation and the zone ID.")).strip()
                    self.answers["forecastZone"] = forecast_zone
                    if self.answers["forecastZone"] != "":
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

            forecast_pre = (yield Step("Enter Forecast Pre-Script (default \"Here is your official national weather service forecast for the Kalamazoo listening area.\"): ", "Here is your official national weather service forecast for the Kalamazoo listening area.", "ex. \"This is the pre-script.\" would be said before the forecast is announced.")).strip()
            self.answers["forecastPre"] = forecast_pre

            forecast_post = (yield Step("Enter Forecast Post-Script (default \"For additional weather and climate information, please visit weather, dot g o v, forward slash, g, r, r.\"): ", "For additional weather and climate information, please visit weather, dot g o v, forward slash, g, r, r.", "ex. \"This is the post-script.\" would be said after the forecast is announced.")).strip()
            self.answers["forecastPost"] = forecast_post

            tropical_input = (yield Step("Enable Tropical Forecast? (yes/no) (default no): ", "no", "Enable or disable tropical forecast. Useful if you live near coastal waters.")).strip().lower()
            self.answers["enableTropicalForecast"] = tropical_input in ("yes", "y")

            hwo_office = (yield Step("Enter HWO Office Code (default GRR): ", "GRR", "You can find this at https://www.weather.gov/nwr/wfo_nwr under \"Call Sign\".")).strip()
            self.answers["hwoOffice"] = hwo_office or "GRR"
            keep_going = False if hwo_office != "GRR" else True
            while keep_going is True:
                keep_going = True
                confirm_hwo = (yield Step("You are using the default GRR HWO office code. Are you sure? (yes/no) (default no): ", "yes", "GRR is for Grand Rapids, MI. If you are not served by that HWO, please enter your local HWO office code.")).strip().lower()
                if confirm_hwo not in ("yes", "y"):
                    hwo_office = (yield Step("Enter HWO Office Code: ", "", "You can find this at https://www.weather.gov/nwr/wfo_nwr under \"Call Sign\".")).strip()
                    self.answers["hwoOffice"] = hwo_office
                    if self.answers["hwoOffice"] != "":
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

            alert_station_id = (yield Step("Enter NWS Station ID (default WNG773): ", "WNG773", "You can find this at https://www.weather.gov/nwr/wfo_nwr under your local WFO, under \"Station ID\".")).strip()
            self.answers["alertStationID"] = alert_station_id or "WNG773"
            keep_going = False if alert_station_id != "WNG773" else True
            while keep_going is True:
                keep_going = True
                confirm_alert_station = (yield Step("You are using the default WNG773 station ID. Are you sure? (yes/no) (default no): ", "yes", "WNG773 is for Kalamazoo, MI. If you are not in that area, please enter your local station ID.")).strip().lower()
                if confirm_alert_station not in ("yes", "y"):
                    alert_station_id = (yield Step("Enter NWS Station ID: ", "", "You can find this at https://www.weather.gov/nwr/wfo_nwr under your local WFO, under \"Station ID\".")).strip()
                    self.answers["alertStationID"] = alert_station_id
                    if self.answers["alertStationID"] != "":
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

            alert_zones_input = (yield Step("Enter Alert Zones separated by commas (default MIC077): ", "MIC077", "You can find this at https://www.weather.gov/nwr/counties under your state and county, replace the first 2 letters with your state abbreviation.")).strip()
            if alert_zones_input:
                alert_zones = [zone.strip() for zone in alert_zones_input.split(",") if zone.strip()]
            else:
                alert_zones = []
            self.answers["alertZones"] = alert_zones or ["MIC077"]
            keep_going = False if alert_zones != ["MIC077"] else True
            while keep_going is True:
                keep_going = True
                if alert_zones == ["MIC077"]:
                    confirm_alert_zones = (yield Step("You are using the default MIC077 alert zone. Are you sure? (yes/no) (default no): ", "yes", "MIC077 is for Kalamazoo County, MI. If you are not in that area, please enter your local alert zones.")).strip().lower()
                    if confirm_alert_zones not in ("yes", "y"):
                        alert_zones_input = (yield Step("Enter Alert Zones separated by commas: ", "", "You can find this at https://www.weather.gov/nwr/counties under your state and county, replace the first 2 letters with your state abbreviation.")).strip()
                        if alert_zones_input:
                            alert_zones = [zone.strip() for zone in alert_zones_input.split(",") if zone.strip()]
                    else:
                        alert_zones = []
                    self.answers["alertZones"] = alert_zones
                    if self.answers["alertZones"] != []:
                        keep_going = False
                    else:
                        keep_going = True
                else:
                    keep_going = False

    wizard = ConfigWizard()
    answers = wizard.run()

    if answers is None:
        log.warning("[UTILS] Interactive configuration aborted by user.")
        return

    ttsSpeed = answers["ttsSpeed"]
    endPause = answers["endPause"]
    logLevel = answers["logLevel"]
    globalHTTPTimeout = answers["globalHTTPTimeout"]
    currentTimeScript = answers["currentTimeScript"]
    dateEnable = answers["dateEnable"]
    dateScript = answers["dateScript"]
    mainObsCode = answers["mainObsCode"]
    regionalObsCodes = answers["regionalObsCodes"]
    openers = answers["openers"]
    openerList = answers["openerList"]
    cityNameDef = answers["cityNameDef"]
    dividers = answers["dividers"]
    forecastDays = answers["forecastDays"]
    forecastZone = answers["forecastZone"]
    forecastPre = answers["forecastPre"]
    forecastPost = answers["forecastPost"]
    enableTropicalForecast = answers["enableTropicalForecast"]
    hwoOffice = answers["hwoOffice"]
    alertStationID = answers["alertStationID"]
    alertZones = answers["alertZones"]
    dividersDict = {key: value for key, value in dividers.items()}

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
