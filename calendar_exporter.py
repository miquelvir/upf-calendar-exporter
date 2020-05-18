from csv_utils.csv_exporter import export_csv
from utils import *
from common import *
from typing import List

CALENDAR_HEADERS = ["Subject", "Start Date", "Start Time", "End Date", "End Time", "All Day Event", "Description",
                    "Location", "Private"]


def dict_to_valid_rows(data: List[dict]) -> List[list]:
    """
    transforms imported data to the Google Calendar format

    refer here (format specs): https://support.google.com/calendar/answer/37118?co=GENIE.Platform%3DDesktop&hl=en&oco=0

    :param data: list of dict representing valid sessions (with title, start time and end time at least)
    :return:  list of lists (matrix) for the csv file rows and columns
    """

    row_list = [CALENDAR_HEADERS]  # first row must be the headers

    for session in data:
        # get basic arguments
        start = datetime.strptime(session[START], "%Y-%m-%d %H:%M:%S")
        end = datetime.strptime(session[END], "%Y-%m-%d %H:%M:%S")
        full_title = session[TITLE]

        # search if there are any additional parameters and add them
        description = ""
        session_keys = session.keys()

        if TYPE in session_keys and session[TYPE] is not "":
            full_title += ' [{}]'.format(session[TYPE])

        description += full_title + NEWLINE + NEWLINE

        if GROUP in session_keys and str(session[GROUP]) is not "":
            description += str(session[GROUP]) + NEWLINE

        if TEACHERS in session_keys and len(session[TEACHERS]) > 0:
            description += str(session[TEACHERS]) + NEWLINE

        if NOTES1 in session_keys and session[NOTES1] is not "":
            description += session[NOTES1] + NEWLINE

        if NOTES2 in session_keys and session[NOTES2] is not "":
            description += session[NOTES2] + NEWLINE

        if CODE in session_keys and str(session[CODE]) is not "":
            description += str(session[CODE]) + NEWLINE

        new_row = [full_title,  # title (with session type if available)
                   get_date(start),  # start date
                   get_time(start),  # start time
                   get_date(end),  # end date
                   get_time(end),  # end time
                   False,  # not full day - we can't know from provided info
                   description,  # description - additional info
                   session[ROOM] if ROOM in session_keys else "unknown",   # room - include only if it is known
                   True]  # private (by default)

        row_list.append(new_row)

    return row_list


def export_calendar(data: List[dict], file_path: str) -> bool:
    """

    :param data: list of dict representing valid sessions (with title, start time and end time at least)
    :param file_path: a valid verified path
    :return: true if successful, false otherwise
    """

    return export_csv(dict_to_valid_rows(data), file_path)  # returns true if successful
