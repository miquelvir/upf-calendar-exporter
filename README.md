# upf-calendar-exporter

exports UPF University calendar to Google Calendar (and similar services)

this works for any student of UPF which accesses its calendar using https://campusglobal.upf.edu/

***
HOW TO EXECUTE

requirements: Google Chrome or Microsoft Edge (Edge comes with Windows)

**Windows (exe, nothing to install)**

1. download upf-calendar-exporter.exe from the [releases](https://github.com/miquelvir/upf-calendar-exporter/releases)
   and move it to the folder where you want the calendar files
2. double-click it. The exe is not signed, so Windows may show "Windows protected your PC": click "More info" and
   then "Run anyway"
3. answer the questions (press enter to accept the defaults) and log in when the browser window opens

**macOS and Linux (from source, with [uv](https://docs.astral.sh/uv/))**

1. install uv (it also installs Python if needed), then open a new terminal:

       curl -LsSf https://astral.sh/uv/install.sh | sh

   or, with Homebrew: `brew install uv`

2. download the project and enter its folder:

       git clone https://github.com/miquelvir/upf-calendar-exporter.git
       cd upf-calendar-exporter

   (without git: "Code" > "Download ZIP" on GitHub, unzip it and `cd` into the folder)

3. install the dependencies and run the app:

       uv sync
       uv run main.py

on Linux, use Google Chrome or Chromium installed from a .deb/.rpm package: Chromium installed as a snap (Ubuntu's
default) is not supported, its sandbox hides the temporary profile from the app

**what the app does**

it asks for the dates and options (press enter to accept the defaults: the current academic year, and the directory
the app runs from), then opens a browser window: log in to Secretaria Virtual with your DNI and password and that's
all. The app opens the timetable by itself, reads the session cookies through the Chrome DevTools Protocol and closes
the window. The browser uses a temporary profile, deleted when the app finishes.

the result is calendar_export_all.csv (plus one csv per subject if you asked for separate files) in the chosen
directory, ready to import into Google Calendar

***
BUILDING THE EXE

    ./build.ps1

creates dist/upf-calendar-exporter.exe with Python and all dependencies bundled. Pushing a tag like v2.0.0 builds it on
GitHub Actions and attaches it to a release.

***
BROWSER VERSION

there is also a userscript version of this exporter: https://github.com/bdim404/upf-calendar-userscript

it runs on the timetable page itself, so the browser's existing session authenticates the request. it exports the same Google Calendar csv, plus an .ics file for Apple Calendar, with a date range, subject exclusion and a holiday filter

***

this is not a project endorsed by UPF; changes in UPF's end might break the current solution


report bugs through comments if possible - be nice, it is a one day built :)


***

FURTHER IMPROVEMENTS


if someone has time and knowledge, it would be nice to branch and integrate with google calendar api + .py that can be scheduled with TaskScheduler to get new updates


*******************************************************************************
 # legal
 

Copyright 2020 Miquel Vázquez (@miquelvir)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

***

baseline_today_white_48dp.ico is available from https://material.io/resources/icons/?style=baseline under the Apache License, Version 2.0
