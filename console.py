import requests
import fire
import shlex
import platform
import os
import sys
import subprocess
import threading
import yaml

# Import all the API functions
from bank_api import *


FUNCTIONS = {}
FUNCTIONS.update(bank_api_functions)

# Shell Information
PROMPT = "White Team >> "
HIST_FILE=".whiteteam_history"

HAS_READLINE = True
try:
    import readline
except ImportError:
    print("Warning: readline not installed. Limited shell capability.")
    HAS_READLINE = False

# Remap input, for python 2/3 compatibility
try:
    input = raw_input
except NameError:
    pass


# open the config file
with open("config.yml") as fil:
    config = yaml.load(fil)


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

def _banner():
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


def _api_request(endpoint, data=None, method='POST', token=None):
    """
    Makes a request to our api and returns the response

    :param endpoint: the api endpoint to hit
    :param data: the data to send in dictionary format

    :returns resp: the api response
    """
    url = ""
    # Search through all the endpoints for the one we are given
    # Build a URL once its found
    for ep in config.get("endpoints", []):
        print(ep)
        if ep.get("endpoints", []) and endpoint in ep.get("endpoints", []):
            url = "{}/{}".format(ep.get("url"), endpoint)
    '''
    if endpoint in AUTH_ENDPOINTS:
        url = "{}/{}".format(AUTH_API_URL, endpoint)
    elif endpoint in BANK_ENDPOINTS:
        url = "{}/{}".format(BANK_API_URL, endpoint)
    elif endpoint in CENTRAL_ENDPOINTS:
        url = "{}/{}".format(CENTRAL_API_URL, endpoint)
    else:
        url = "{}/{}".format(SHIP_API_URL, endpoint)
    '''
    # If the endpoint is not registered, error
    if not url:
        raise Exception("Endpoint not found")
    
    cookies = {'token': token}
    if method == 'POST':
        print(data)
        print(url)
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


def get_token():
    """
    Gets an auth token for our white team account from the auth api

    :returns token: the auth token for white team account
    """
    data = dict()
    data['username'] = AUTH_USERNAME
    data['password'] = AUTH_PASSWORD
    endpoint = 'login'
    resp = api_request(endpoint, data=data)
    if 'token' not in resp:
        raise Exception('No token in AUTH_API response')

    return resp['token']

class FireThread(threading.Thread):
    """
    Run Fire in separate thread to prevent exiting.
    """
    def __init__(self, cmd):
        self._cmd = cmd
        threading.Thread.__init__(self)

    def run(self):
        fire.Fire(FUNCTIONS)

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
    # Configure readline
    if HAS_READLINE:
        if os.path.exists(HIST_FILE):
            readline.read_history_file(HIST_FILE)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')

        # Build Auto Complete
        #autocomplete = list(filter(lambda x: not x.startswith('_'), dir(Console)))
        #completer = SimpleCompleter(autocomplete)
        #readline.set_completer(completer.complete)

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
    _api_request(NAME)
    #main()
