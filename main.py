import webbrowser
from os import path
from browser_login import LoginError, get_session_cookies
from calendar_exporter import export_calendar
from scraper import CalendarRequestError, request_calendar, clean_received_sessions
from utils import ask_date, ask_path, ask_yes_no, print_progress_bar, print_separator
from datetime import datetime, timedelta
from typing import Tuple

URL_IMPORT_CALENDAR = "https://calendar.google.com/calendar/r/settings/export"


def launch_google_calendar():
    webbrowser.open(URL_IMPORT_CALENDAR, new=2)  # 2 requires new tab


def academic_year(date: datetime) -> int:
    return date.year if date.month >= 8 else date.year - 1  # 2026 for 2026/2027


def guide_user_start() -> Tuple[datetime, datetime, str, bool, bool]:
    print("steps")
    print_progress_bar(0, 4)

    year = academic_year(datetime.now())
    print("customise parameters")
    first_date = ask_date("first date to import", default=datetime(year, 9, 1))
    last_date = ask_date("last date to import (included)", default=datetime(year + 1, 7, 31),
                         greater_than=int(first_date.timestamp()))
    if academic_year(first_date) != academic_year(last_date):
        print("note: only subjects of the {}/{} academic year will be exported".format(
            academic_year(first_date), academic_year(first_date) + 1))
    print_progress_bar(1, 4)

    print("select directory")
    saving_path = path.join(ask_path(), "calendar_export")
    print_progress_bar(2, 4)

    print("additional options")
    separate = ask_yes_no("export subjects in separate files? ")
    keep_holidays = ask_yes_no("include holidays and non-teaching days? ")
    print_progress_bar(3, 4)

    return first_date, last_date, saving_path, separate, keep_holidays


def login(first_date: datetime) -> dict:
    print("a browser window will open: log in to Secretaria Virtual with your DNI and password")
    print("that's all, the timetable is opened automatically (do not close the window)")
    input("press enter to open the browser...")

    cookies = get_session_cookies(academic_year(first_date))
    print("...logged in, the browser can be closed")
    print_progress_bar(4, 4)

    return cookies


def process(cookies: dict, first_date: datetime, last_date: datetime, saving_path: str, separate: bool,
            keep_holidays: bool) -> bool:
    print_progress_bar(0, 3)

    print("requesting calendar...")
    end = last_date + timedelta(days=1)  # the last date is included
    data = request_calendar(cookies, str(int(first_date.timestamp())), str(int(end.timestamp())))
    print("...request finished")
    print_progress_bar(1, 3)

    print("cleaning received info...")
    clean_received_sessions(data, keep_holidays)
    print("...cleaning finished, {} events".format(len(data)))
    if not data:
        print("no events found in that range, check the dates")
    print_progress_bar(2, 3)

    print("exporting Google Calendar file...")
    status = export_calendar(data, saving_path, separate)
    print("...exported to {}_all.csv".format(saving_path))
    print_progress_bar(3, 3)

    return status


def guide_user_end() -> None:
    print("you can now import the file to Google Calendar")
    print("additional info:")
    print("https://support.google.com/calendar/answer/37118?co=GENIE.Platform%3DDesktop&hl=en")
    print("suggestion: create a new calendar and import it there, so that you can batch-delete/color change")
    input("press enter to import into Google Calendar manually")
    launch_google_calendar()


def show_troubleshooting_steps() -> None:
    print("- verify that Google Chrome or Microsoft Edge is installed")
    print("- log in to Secretaria Virtual in the window opened by this app, not in your usual browser")
    print("- do not close that window until the app says you are logged in")
    print("- if 'Horaris de classe' is not in your Secretaria Virtual menu, the calendar is not available for you")


def main():
    print("""

    a project by @miquelvir
    ***********************

    """)
    print("this script will help you export your UPF Calendar to Google Calendar (or similar)")
    print_separator()

    first_date, last_date, saving_path, separate, keep_holidays = guide_user_start()
    print_separator()

    try:
        cookies = login(first_date)
        print_separator()
        status = process(cookies, first_date, last_date, saving_path, separate, keep_holidays)
    except (LoginError, CalendarRequestError) as e:
        print("error: {}".format(e))
        status = False
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
