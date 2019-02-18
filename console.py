import requests
import fire
import shlex
import platform
import os
import sys
import subprocess
import threading
import yaml
import config
import __main__

# Load new API modules here
APIS = ["store_api", "auth_api", "votes_api"]

ENDPOINT_MAP = {}
FUNCTION_MAP = {}

# Shell Information
PROMPT = "White Team >> "
HIST_FILE=".whiteteam_history"

HAS_READLINE = True

try:
    import readline
except ImportError:
    print("Warning: readline not installed. Limited shell capability.")
    HAS_READLINE = False


def _api_request(endpoint, data=None, method='POST', token=None):
    """
    Makes a request to our api and returns the response
    :param endpoint: the api endpoint to hit
    :param data: the data to send in dictionary format
    :returns resp: the api response
    """
    ENDPOINT_MAP = __main__.ENDPOINT_MAP
    url = "{}/{}".format(ENDPOINT_MAP[endpoint], endpoint)
    #print(url)

    cookies = {'token': token}
    if method == 'POST':
        resp = requests.post(url, json=data, cookies=cookies)
    else:
        resp = requests.get(url, cookies=cookies)

    if resp.status_code == 400:
        print(resp.json())
        raise Exception("Bad request sent to API")

    if resp.status_code == 403:
        raise Exception(resp.json()['error'])

    elif resp.status_code != 200:
        raise Exception("API returned {} for /{}".format(resp.status_code, endpoint))

    resp_data = resp.json()
    return resp_data


def _get_token():
    """
    Gets an auth token for our white team account from the auth api
    :returns token: the auth token for white team account
    """
    data = dict()
    data.update(config.get("creds", {}))
    #data['username'] = config.get("creds", {}).get("username"
    #data['password'] = AUTH_PASSWORD
    endpoint = 'login'
    resp = _api_request(endpoint, data=data)
    if 'token' not in resp:
        raise Exception('No token in AUTH_API response')

    return resp['token']


def slackUpdate(msg):
    """
    This function is used to log messages to slack.
    """
    if not USE_SLACK:
        return
    requests.post(
        URI,
        json= {
            "text": "{}:\t{}".format(NAME, msg),
            "channel": CHANNEL,
            "link_names": 1,
            "username": USERNAME,
            "icon_emoji": ICON_EMOJI
        }
    )

def banner():
    """
    This function prints out the banner.
    """
    print(
    """

 ██╗███████╗████████╗███████╗     ██╗███████╗
 ██║██╔════╝╚══██╔══╝██╔════╝    ███║╚════██║
 ██║███████╗   ██║   ███████╗    ╚██║    ██╔╝
 ██║╚════██║   ██║   ╚════██║     ██║   ██╔╝
 ██║███████║   ██║   ███████║     ██║   ██║
 ╚═╝╚══════╝   ╚═╝   ╚══════╝     ╚═╝   ╚═╝

""")

def exit():
    """
    This function will be called when the console window is closed.
    """
    sys.exit(0)
    

def clear():
    """
    This function is used to clear the console window.
    """
    p = subprocess.Popen( "cls" if platform.system() == "Windows" else "echo -e \\\\033c", shell=True)
    p.wait()

class FireThread(threading.Thread):
    """
    Run Fire in separate thread to prevent exiting.
    """
    def __init__(self, cmd):
        self._cmd = cmd
        threading.Thread.__init__(self)

    def run(self):
        fire.Fire(FUNCTION_MAP, "{}".format(self._cmd))


# Tab completion for our console
class SimpleCompleter(object):

    def __init__(self, options):
        self.options = sorted(options)
        return

    def complete(self, text, state):
        response = None
        if state == 0:
            # This is the first time for this text, so build a match list.
            if text:
                self.matches = [s
                                for s in self.options
                                if s and s.startswith(text)]
            else:
                self.matches = self.options[:]

        # Return the state'th item from the match list,
        # if we have that many.
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        return response


def main():
    """
    Main Method
    """
    # Build a map of all the endpoints and all the functions
    global ENDPOINT_MAP
    ENDPOINT_MAP = {}
    global FUNCTION_MAP
    FUNCTION_MAP = {}
    
    for API in APIS:
        api_module = __import__(API)
        # Load all the endpoints and map them to the server
        for endpoint in api_module._endpoints:
            ENDPOINT_MAP[endpoint] = api_module._server

        # Find all the callable functions for Fire
        for func in dir(api_module):
            if not func.startswith("_"):
                FUNCTION_MAP[func] = getattr(api_module, func)
    # Configure readline
    if HAS_READLINE:
        if os.path.exists(HIST_FILE):
            readline.read_history_file(HIST_FILE)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')

        # Build Auto Complete
        autocomplete = list(FUNCTION_MAP.keys())
        completer = SimpleCompleter(autocomplete)
        readline.set_completer(completer.complete)

    # Loop for input
    cleared = False

    # Display the banner
    banner()

    while True:
        if cleared:
            cleared = False
            continue

        try:
            cmd = input(PROMPT)
            args = shlex.split(cmd)
            if cmd.lower() == 'exit' or cmd.lower() == 'quit':
                exit()
            elif cmd.lower() == 'clear' or cmd.lower() == 'cls':
                clear()
                cleared = True
            else:
                t1 = FireThread(cmd)
                t1.start()
                t1.join()
                if HAS_READLINE:
                    readline.write_history_file(HIST_FILE)
        except EOFError as e:
            exit()
        except Exception as e:
            print(e)


if __name__ == '__main__':
    NAME = input("Please enter your name: ")
    main()

