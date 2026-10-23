from requests import Session
from requests.exceptions import RequestException
import json

from common import TEACHERS
from session import is_valid_session, is_holiday
from utils import replace_entities
from typing import Dict, List

AJAX_REQUEST_URL = 'https://secretariavirtual.upf.edu/pds/control/[Ajax]selecionarRangoHorarios?rnd=4236.0&start={' \
                   '}&end={}'
REFERER_URL = 'https://secretariavirtual.upf.edu/pds/control/PubliHoraAlumCalendario?rnd=5732.0'


class CalendarRequestError(Exception):
    pass


def request_calendar(cookies: Dict[str, str], start: str, end: str) -> List[dict]:
    """

    requests calendar info with the ajax endpoint used by the calendar page and returns it as a list of dicts

    :param cookies: session cookies; JSESSIONID alone is not enough, the load balancer ROUTEID cookie is needed to
                    reach the server holding the session
    :param start: epoch start time of events to import
    :param end: epoch end time of events to import
    :return: list of dicts, each dict representing an event
    """
    session = Session()
    session.cookies.update(cookies)

    try:
        response = session.get(
            url=AJAX_REQUEST_URL.format(start, end),
            headers={
                "Accept": "*/*",
                "Content-Type": "application/json; charset=utf-8",
                "Referer": REFERER_URL,
                "X-Requested-With": "XMLHttpRequest"
            },
            timeout=60
        )
    except RequestException as e:
        raise CalendarRequestError("could not reach secretariavirtual.upf.edu: {}".format(e)) from e

    try:
        data = json.loads(response.text)
    except ValueError:  # an html page, 'Sesión expirada'
        raise CalendarRequestError("the session is not valid (secretariavirtual answered 'session expired')") from None

    if isinstance(data, dict) and "error" in data:  # the calendar was not opened before requesting it
        raise CalendarRequestError("secretariavirtual answered: {}".format(data["error"]))

    return data


def clean_received_sessions(data: List[dict], keep_holidays: bool = False) -> None:
    """
    cleans received data (I/O): removes events without minimum info, optionally removes holidays and non-teaching
    days, and replaces html entities (otherwise encoding is not correct when exporting)

    :param data: list of dict representing sessions
    :param keep_holidays: true to keep holidays and non-teaching days, false to remove them
    """

    cleaned = []

    for session in data:
        if not is_valid_session(session):
            continue  # skip dictionary, it does not have enough info to display event

        if not keep_holidays and is_holiday(session):
            continue  # skip holiday/non-teaching day, it is not a real session

        # is valid event, should clean html entities
        for key in session.keys():
            if type(session[key]) is str:  # only strings can have html entities
                session[key] = replace_entities(session[key])
            elif key == TEACHERS and len(session[TEACHERS]) > 0:  # replace entities for each teacher name
                session[TEACHERS] = [replace_entities(str(teacher)) for teacher in session[TEACHERS]]

        cleaned.append(session)

    data[:] = cleaned  # replace contents in place, callers keep their reference
