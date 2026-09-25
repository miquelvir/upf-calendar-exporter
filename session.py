from common import HOLIDAY


def is_valid_session(session: dict) -> bool:
    """
    checks if passed dict has enough info to display event

    :param session: dict representing a session
    :return: True if it has enough info (title, start time, end time), False otherwise
    """

    try:
        session_keys = session.keys()
    except AttributeError:
        print("probable error in ajax request...")
        return False  # not a dict

    for expected in 'title', 'start', 'end':  # minimal requirements
        if expected not in session_keys:
            return False

    return True  # at this level, all required keys were found


def is_holiday(session: dict) -> bool:
    """
    checks if passed dict is a holiday or non-teaching day rather than a real session

    UPF returns these with placeholder 11:00-19:00 times, so they clutter the calendar if exported

    :param session: dict representing a session
    :return: True if it is a holiday or non-teaching day, False otherwise
    """

    return session.get(HOLIDAY) is True
