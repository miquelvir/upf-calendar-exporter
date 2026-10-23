import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Dict, List, Optional

import requests
import websocket

URL_SECRETARIA = "https://secretariavirtual.upf.edu/"
URL_PDS = "https://secretariavirtual.upf.edu/pds/"

POLL_SECONDS = 1.0
ACTION_RETRY_SECONDS = 15.0  # if an action did not change the page after this time, try it again

# reports which step of the secretariavirtual flow the page is at
DETECT_STATE_JS = """(() => {
    if (location.hostname !== 'secretariavirtual.upf.edu') return {state: 'other'};
    if (document.readyState !== 'complete') return {state: 'loading'};
    if (location.pathname.includes('PubliHoraAlumCalendario')) return {state: 'calendar'};
    const form = document.forms.formu_Edi;
    if (form && typeof buscar === 'function') {
        const plan = form.planDocente;
        return {state: 'form', year: plan ? plan.value : null,
                years: plan ? [...plan.options].map(o => o.value) : []};
    }
    const menu = [...document.querySelectorAll('a[href]')]
        .some(a => /idAplicacion=PUBLI\\b/.test(a.getAttribute('href')));
    return {state: menu ? 'menu' : 'login'};
})()"""

# 'Horaris de classe' in the menu: hands the login over to the timetable app (/pds) with a token
OPEN_TIMETABLE_JS = """(() => {
    const link = [...document.querySelectorAll('a[href]')]
        .find(a => /idAplicacion=PUBLI\\b/.test(a.getAttribute('href')));
    const match = link.getAttribute('href').match(/lanzarUrlNaus\\('([^']+)'\\)/);
    location.href = match ? new URL(match[1], location.href).href : link.href;
})()"""

# reloads the form with the subjects of another academic year
CHANGE_YEAR_JS = """(year => {
    document.forms.formu_Edi.planDocente.value = year;
    refrescarAsignaturas();
})({year})"""

# 'Veure Calendari' with every subject selected: stores the selection server side, the ajax request depends on it
SHOW_CALENDAR_JS = """(() => {
    try { jQuery('#asignaturas').multiselect('checkAll'); } catch (e) {}
    buscar();
})()"""


class LoginError(Exception):
    pass


def find_browser() -> Optional[str]:
    """
    finds an installed Chromium-based browser (Chrome, Edge, Chromium)

    :return: path to the browser executable, None if none is found
    """
    candidates = []

    if sys.platform == "win32":
        for root in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"),
                     os.environ.get("LOCALAPPDATA")):
            if root:
                candidates.append(os.path.join(root, "Google", "Chrome", "Application", "chrome.exe"))
                candidates.append(os.path.join(root, "Microsoft", "Edge", "Application", "msedge.exe"))
    elif sys.platform == "darwin":
        candidates += ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                       "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
                       "/Applications/Chromium.app/Contents/MacOS/Chromium"]

    for name in ("chrome", "msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 "microsoft-edge"):
        found = shutil.which(name)
        if found:
            candidates.append(found)

    return next((c for c in candidates if os.path.isfile(c)), None)


class CdpPage:
    """
    minimal Chrome DevTools Protocol client attached to one page (tab)
    """

    def __init__(self, ws_url: str):
        # Chrome refuses DevTools websockets that send an Origin header it does not allow
        self._ws = websocket.create_connection(ws_url, timeout=30, suppress_origin=True)
        self._last_id = 0

    def call(self, method: str, **params) -> dict:
        self._last_id += 1
        self._ws.send(json.dumps({"id": self._last_id, "method": method, "params": params}))

        while True:
            message = json.loads(self._ws.recv())
            if message.get("id") != self._last_id:
                continue  # an event, not the answer we are waiting for
            if "error" in message:
                raise LoginError(message["error"].get("message", "devtools error"))
            return message["result"]

    def evaluate(self, expression: str):
        result = self.call("Runtime.evaluate", expression=expression, returnByValue=True)
        if "exceptionDetails" in result:
            raise LoginError(result["exceptionDetails"].get("text", "javascript error"))
        return result["result"].get("value")

    def close(self) -> None:
        self._ws.close()


def launch_browser(executable: str, profile_dir: str) -> subprocess.Popen:
    """
    launches the browser on a throwaway profile with the DevTools port enabled

    :param executable: browser executable path
    :param profile_dir: empty directory for the temporary profile
    :return: the browser process
    """
    return subprocess.Popen([executable,
                             "--remote-debugging-port=0",  # any free port, written to DevToolsActivePort
                             "--user-data-dir={}".format(profile_dir),
                             "--no-first-run",
                             "--no-default-browser-check",
                             URL_SECRETARIA],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def wait_devtools_port(profile_dir: str, process: subprocess.Popen, timeout: float = 30) -> int:
    """
    waits until the browser publishes its DevTools port

    :return: DevTools http port
    """
    port_file = os.path.join(profile_dir, "DevToolsActivePort")
    deadline = time.time() + timeout

    while time.time() < deadline:
        if process.poll() is not None:
            raise LoginError("the browser closed before it was ready")
        try:
            with open(port_file) as file:
                return int(file.readline().strip())
        except (OSError, ValueError):
            time.sleep(0.2)  # not written yet

    raise LoginError("the browser did not open its DevTools port")


def list_pages(port: int) -> List[dict]:
    targets = requests.get("http://127.0.0.1:{}/json/list".format(port), timeout=5).json()
    return [t for t in targets if t.get("type") == "page" and "webSocketDebuggerUrl" in t]


def drive_to_calendar(port: int, process: subprocess.Popen, academic_year: Optional[int],
                      timeout: float) -> Dict[str, str]:
    """
    waits for the user to log in, then opens the timetable calendar like a user would and returns the cookies

    :param port: DevTools http port
    :param process: browser process, to detect the user closing it
    :param academic_year: academic year to select (2026 for 2026/2027), None to keep the default one
    :param timeout: seconds to wait for the whole flow
    :return: cookies of the timetable app (JSESSIONID and the load balancer ROUTEID among others)
    """
    pages: Dict[str, CdpPage] = {}
    last_action, last_action_time = None, 0.0
    year_changed = False
    deadline = time.time() + timeout

    try:
        while time.time() < deadline:
            if process.poll() is not None:
                raise LoginError("the browser was closed before the calendar was loaded")

            try:
                targets = list_pages(port)
            except requests.RequestException:
                time.sleep(POLL_SECONDS)
                continue

            for target in targets:
                if "secretariavirtual.upf.edu" not in target.get("url", ""):
                    continue

                try:
                    page = pages.get(target["id"]) or pages.setdefault(target["id"],
                                                                        CdpPage(target["webSocketDebuggerUrl"]))
                    info = page.evaluate(DETECT_STATE_JS) or {}
                except (LoginError, OSError, websocket.WebSocketException):
                    pages.pop(target["id"], None)  # page navigating or closed, check again on next poll
                    continue

                state = info.get("state")
                if state == "calendar":
                    cookies = page.call("Network.getCookies", urls=[URL_PDS])["cookies"]
                    return {c["name"]: c["value"] for c in cookies}

                if state not in ("menu", "form"):
                    continue  # still logging in or loading

                year = str(academic_year) if academic_year is not None else None
                if state == "form" and year and not year_changed and info.get("year") != year \
                        and year in info.get("years", []):
                    action, script = "year", CHANGE_YEAR_JS.replace("{year}", json.dumps(year))
                    year_changed = True
                elif state == "form":
                    action, script = "calendar", SHOW_CALENDAR_JS
                else:
                    action, script = "menu", OPEN_TIMETABLE_JS

                if action == last_action and time.time() - last_action_time < ACTION_RETRY_SECONDS:
                    continue  # already done, waiting for the page to change

                if action == "menu":
                    print("login detected, opening your timetable...")
                try:
                    page.evaluate(script)
                except (LoginError, OSError, websocket.WebSocketException):
                    pass  # navigation started while evaluating, expected
                last_action, last_action_time = action, time.time()

            time.sleep(POLL_SECONDS)
    finally:
        for page in pages.values():
            try:
                page.close()
            except (OSError, websocket.WebSocketException):
                pass

    raise LoginError("timed out waiting for the login")


def get_session_cookies(academic_year: Optional[int] = None, timeout: float = 15 * 60) -> Dict[str, str]:
    """
    opens a browser window for the user to log in to secretariavirtual and returns the session cookies

    :param academic_year: academic year to select (2026 for 2026/2027), None to keep the default one
    :param timeout: seconds to wait for the user to log in
    :return: cookies to use for the ajax request
    """
    executable = find_browser()
    if executable is None:
        raise LoginError("Google Chrome or Microsoft Edge is required, none was found")

    profile_dir = tempfile.mkdtemp(prefix="upf-calendar-exporter-")
    process = launch_browser(executable, profile_dir)

    try:
        port = wait_devtools_port(profile_dir, process)
        return drive_to_calendar(port, process, academic_year, timeout)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
        shutil.rmtree(profile_dir, ignore_errors=True)
