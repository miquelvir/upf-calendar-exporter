from csv_utils.csv_exporter import export_csv
from utils import *
from common import *
from typing import List

CALENDAR_HEADERS = ["Subject", "Start Date", "Start Time", "End Date", "End Time", "All Day Event", "Description",
                    "Location", "Private"]
ROW_TITLE_INDEX = -1  # index


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
                   True,  # private (by default)
                   session[TITLE]]  # for internal use, title without type

        row_list.append(new_row)

    return row_list


def get_separated_rows(rows: List[list]) -> dict:
    """
    returns a dictionary with name: rows for each class

    :param rows: list of lists (matrix) for the csv file rows and columns
    :return: dict of list of lists (matrix) for the csv file of each class
    """

    result = {}

    for session in rows:
        if session[ROW_TITLE_INDEX] not in result:  # first session of the class, create key in dict and start list
            result[session[ROW_TITLE_INDEX]] = [session]
        else:  # elements of same class already in list, append element
            result[session[ROW_TITLE_INDEX]].append(session)

    return result


def export_calendar(data: List[dict], file_path: str, separate: bool) -> bool:
    """

    :param data: list of dict representing valid sessions (with title, start time and end time at least)
    :param file_path: a valid verified path without .csv
    :param separate: true if additionally a csv for each course must be created, false otherwise
    :return: true if successful, false otherwise
    """

    rows = dict_to_valid_rows(data)

    if separate:
        separated_rows = get_separated_rows(rows)
        for i, classe in enumerate(separated_rows.values()):
            if len(classe) > 1:  # only the header takes 1 space; aka if it is not empty
                export_csv(classe, "{}_{}.csv".format(file_path, str(i)))

    return export_csv(rows, "{}_all.csv".format(file_path))  # returns true if successful
