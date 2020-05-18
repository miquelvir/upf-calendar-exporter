import html
from requests import Session, get
from bs4 import BeautifulSoup
import json

from common import TEACHERS
from session import is_valid_session
from utils import replace_entities
from typing import List

AJAX_REQUEST_URL = 'https://gestioacademica.upf.edu/pds/control/[Ajax]selecionarRangoHorarios?rnd=4236.0&start={' \
                   '}&end={}'


def request_calendar(jsessionid: str, start: str, end: str) -> List[dict]:
    """

    posts ajax request to get calendar info and returns it as a list of dicts

    :param jsessionid: JSESSIONID parameter for ajax post headers
    :param start: epoch start time of events to import
    :param end: epoch end time of events to import
    :return: list of dicts, each dict representing an event
    """
    session = Session()

    response = session.post(
        url=AJAX_REQUEST_URL.format(start, end),
        headers={
            "Cookie": "JSESSIONID={};".format(jsessionid),
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Content-Type": "application/json; charset=uft-8",
            "Host": "gestioacademica.upf.edu",
            "Referer": "https://gestioacademica.upf.edu/pds/control/PubliHoraAlumCalendario?rnd=176.0",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-Requested-With": "XMLHttpRequest"
        }
    )

    return json.loads(response.text)


def clean_received_sessions(data: List[dict]) -> None:
    """
    cleans received data (I/O): removes events without minimum info and replaces html entities (otherwise encoding
    is not correct when exporting)

    :param data: list of dict representing sessions
    """

    for i, session in enumerate(data):
        if not is_valid_session(session):
            data.pop(i)  # remove dictionary, it does not have enough info to display event
        else:
            # is valid event, should clean html entities
            for key in session.keys():
                if type(session[key]) is str:  # only strings can have html entities
                    session[key] = replace_entities(session[key])
                elif key == TEACHERS and len(session[TEACHERS]) > 0:  # replace entities for each teacher name
                    map(replace_entities, session[TEACHERS])

