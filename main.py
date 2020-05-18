import webbrowser
from calendar_exporter import export_calendar
from scraper import request_calendar, clean_received_sessions
from utils import *
from datetime import datetime
from typing import Tuple
from legal_notice import *

URL_CAMPUS_GLOBAL = "https://campusglobal.upf.edu/"
URL_IMPORT_CALENDAR = "https://calendar.google.com/calendar/r/settings/export"


def launch_campus_global():
    webbrowser.open(URL_CAMPUS_GLOBAL, new=2)  # 2 requires new tab


def launch_google_calendar():
    webbrowser.open(URL_IMPORT_CALENDAR, new=2)  # 2 requires new tab


def guide_user_start() -> Tuple[str, datetime, datetime, str]:
    print("steps")
    print_progress_bar(0, 6)

    print("log in to Campus Global")
    input("press enter to continue and launch Campus Global...")
    launch_campus_global()
    print_progress_bar(1, 6)

    input("enter 'Els meus horaris'")
    print_progress_bar(2, 6)

    input("click 'Veure Calendari'")
    print_progress_bar(3, 6)

    print("right click, inspect (using Chrome), Application, Cookies, copy JSESSIONID")
    jsessionid = input("JSESSIONID: ")
    print_progress_bar(4, 6)

    print("customise parameters")
    first_date = ask_date("first date to import")
    last_date = ask_date("last date to import:", greater_than=int(first_date.timestamp()))
    print_progress_bar(5, 6)

    print("select directory")
    saving_path = ask_path() + "\\calendar_export.csv"
    print_progress_bar(6, 6)

    return jsessionid, first_date, last_date, saving_path


def process(jsessionid: str, first_date: datetime, last_date: datetime, saving_path: str) -> bool:
    print_progress_bar(0, 3)

    print("posting ajax request...")
    data = request_calendar(jsessionid, str(int(first_date.timestamp())), str(int(last_date.timestamp())))
    print("...ajax request finished")
    print_progress_bar(1, 3)

    print("cleaning received info...")
    clean_received_sessions(data)
    print("...cleaning finished")
    print_progress_bar(2, 3)

    print("exporting Google Calendar file...")
    status = export_calendar(data, saving_path)
    print("...exported")
    print_progress_bar(3, 3)

    return status


def guide_user_end() -> None:
    print("you can now import the file to Google Calendar")
    print("additional info:")
    print("https://support.google.com/calendar/answer/37118?co=GENIE.Platform%3DDesktop&hl=en")
    input("press enter to import into Google Calendar manually")
    launch_google_calendar()


def show_troubleshooting_steps() -> None:
    print("- verify that you have followed the steps correctly in general")
    print("- verify that you have not added any space when entering the JSESSIONID")
    print("- verify that you have clicked 'Veure calendari' before copying the JSESSIONID and trying to request the "
          "calendar")


def main():
    legal_notice()

    print("this script will help you export your UPF Calendar to Google Calendar (or similar)")
    print_separator()

    jsessionid, first_date, last_date, saving_path = guide_user_start()
    print_separator()

    status = process(jsessionid, first_date, last_date, saving_path)
    print_separator()

    if status:
        guide_user_end()
    else:
        print("error during the process, troubleshooting steps below")
        show_troubleshooting_steps()
    print_separator()

    input("enter to exit...")


if __name__ == "__main__":
    main()
