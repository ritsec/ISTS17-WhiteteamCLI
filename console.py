import requests
import fire
import shlex
import platform
import os
import sys
import subprocess
import threading

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

# Slack Information
NAME = "Unnamed User"
USE_SLACK = True
URI="https://hooks.slack.com/services/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"
CHANNEL = "#white-team-tool"
USERNAME = "White Team"
ICON_EMOJI = ":robot_face:"

# OUR NUMEROUS API'S
CENTRAL_API_URL = "http://10.0.20.21:7000"
BANK_API_URL = "http://10.0.20.21:5000"
SHIP_API_URL = "http://10.0.20.21:6000"
AUTH_API_URL = "http://10.0.20.21:9000"

#WHITE TEAM ACCOUNT FOR AUTH SERVER
AUTH_USERNAME = "theblindmice"
AUTH_PASSWORD = "basedgodboyuan1016"

# API ENDPOINTS

AUTH_ENDPOINTS = ['validate-session', 'login', 'update-password',
                  'expire-session', 'update-session', 'pub-key']

BANK_ENDPOINTS = ['get-balance', 'buy', 'transfer', 'transactions', 'items',
                  'dosh-get-balance', 'dosh-add-credits', 'dosh-set-credits',
                  'dosh-remove-credits']

CENTRAL_ENDPOINTS = ['status/koth', 'status/alerts', 'clear/alert', 'create/alert']

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
    ____________________    ________
   /  _/ ___/_  __/ ___/    / / ___/
   / / \__ \ / /  \__ \    / / __ \ 
 _/ / ___/ // /  ___/ /   / / /_/ / 
/___//____//_/  /____/   /_/\____/  
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


def api_request(endpoint, data=None, method='POST', token=None):
    """
    Makes a request to our api and returns the response

    :param endpoint: the api endpoint to hit
    :param data: the data to send in dictionary format

    :returns resp: the api response
    """
    if endpoint in AUTH_ENDPOINTS:
        url = "{}/{}".format(AUTH_API_URL, endpoint)
    elif endpoint in BANK_ENDPOINTS:
        url = "{}/{}".format(BANK_API_URL, endpoint)
    elif endpoint in CENTRAL_ENDPOINTS:
        url = "{}/{}".format(CENTRAL_API_URL, endpoint)
    else:
        url = "{}/{}".format(SHIP_API_URL, endpoint)
    print url

    cookies = {'token': token}
    if method == 'POST':
        print data
        print url
        resp = requests.post(url, json=data, cookies=cookies)
    else:
        resp = requests.get(url, cookies=cookies)

    if resp.status_code == 400:
        print resp.json()
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
        fire.Fire(Console, '{}'.format(self._cmd))

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


class Console(object):
    def help(self, functionName=None):
        """
        Display function docstrings.

        Args:
            functionName: The name of the function you wish to know more about.
        """
        if functionName is None:
            print("\nAvailable Functions:\n")
            print('\n'.join(sorted(filter(lambda x: not x.startswith('_'), dir(Console)))))
            return

        try:
            print(self.__getattribute__(functionName).__doc__)
        except AttributeError:
            print("Invalid function")
    
    def GetCredits(self, team):
        """
        Gets the current credits for a given team #.
        
        i.e. GetCredits 7
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['team_id'] = team
        print post_data
        resp = api_request('dosh-get-balance', data=post_data)
        balance = resp['balance']
        print balance

    def AddCredits(self, team, amount, reason):
        """
        Adds credits to the given team # account. Please also specify a reason.

        i.e. AddCredits 7 50000 "Completed Challenge"
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['team_id'] = team
        post_data['amount'] = amount
        resp = api_request('dosh-add-credits', data=post_data)
        message = resp['success']
        print message
        slackUpdate("Added {} credits to team {} because: {}".format(amount, team, reason))
    
    def RemoveCredits(self, team, amount, reason):
        """
        Removes credits from the given team # account. Please also specify a reason.

        i.e. RemoveCredits 7 50000 "Purchased item at service desk"
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['team_id'] = team
        post_data['amount'] = amount
        resp = api_request('dosh-remove-credits', data=post_data)
        message = resp['success']
        print message
        slackUpdate("Removed {} credits from team {} because: {}".format(amount, team, reason))

    def SetCredits(self, team, amount, reason):
        """
        Set the credits for the given team # account. Please also specify a reason.

        i.e. SetCredits 7 50000 "Setting up the competition"
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['team_id'] = team
        post_data['amount'] = amount
        resp = api_request('dosh-set-credits', data=post_data)
        message = resp['success']
        print message
        slackUpdate("Set team {} credits to {} because: {}".format(team, amount, reason))

    def CreateTeam(self, team, name):
        """
        Add a new team

        """
        token = get_token()
        post_data = dict()
        post_data['teamNum'] = team
        post_data['name'] = name
        resp = api_request('createteam', data=post_data, token=token)
        message = resp['message']
        print message

    def GetAllShips(self):
        """
        Gets the ships for a given team
        """
        token = get_token()
        resp = api_request("teams", method='GET', token=token)
        for team, x in enumerate(resp['teams']):
            print "Team {}: Guardians {} Bombers {} Striker {}".format(team, x['guardian'], x['bomber'], x['striker'])

    def GetAllStats(self):
        """
        Gets the ships for a given team
        """
        token = get_token()
        resp = api_request("teams", method='GET', token=token)
        for team, x in enumerate(resp['teams']):
            print "Team {}: Health {} Damage {} Speed {}".format(team, x['health'], x['damage'], x['speed'])


    def GetShips(self, team):
        """
        Gets the ships for a given team
        """
        token = get_token()
        resp = api_request("teams/{}".format(team), method='GET', token=token)
        print "Guardian: {} Bomber: {} Striker: {}".format(resp['guardian'],
                                                           resp['bomber'], resp['striker'])


    def AddShips(self, team, shipType, amount, reason):
        """
        Adds ships of the given type to a team.

        i.e. AddShips 5 striker 1 "Completed Challenge"
        """
        token = get_token()
        post_data = dict()
        post_data['value'] = amount
        resp = api_request('teams/{}/{}'.format(team, shipType), data=post_data, token=token)
        message = resp['message']
        print message
        slackUpdate("Added {} {} ships to team {} because: {}".format(amount, shipType, team, reason))

    def RemoveShips(self, team, shipType, amount, reason):
        """
        Removes ships of the given type from a team.

        i.e. RemoveShips 5 striker 4 "Stop"
        """
        token = get_token()
        post_data = dict()
        post_data['value'] = -amount
        resp = api_request('teams/{}/{}'.format(team, shipType), data=post_data, token=token)
        message = resp['message']
        print message
        slackUpdate("Removed {} {} ships to team {} because: {}".format(amount, shipType, team, reason))

    def ClearShips(self, team, reason):
        """
        Clear a teams ships. This will set all ship types to 0.

        i.e. ClearShips 5 "Sabotage"
        """
        token = get_token()
        resp = api_request('teams/{}/reset'.format(team), token=token)
        message = resp['message']
        print message
        slackUpdate("Cleared ships from team {} because: {}".format(team, reason))

    def ClearAllShips(self, reason):
        """
        Removes all ships of all types from all teams.

        i.e. ClearAllShips
        """
        valid = input("Are you sure you want to do this?(y/n)")
        if valid.lower().startswith("y"):
            token = get_token()
            for team in range(1, 12):
                resp = api_request('teams/{}/reset'.format(team), token=token)
                message = resp['message']
                print message

            slackUpdate("Cleared ships for all teams because: {}".format(reason))

    def GetKOTH(self):
        """
        Fetches current king of the hill status information.

        i.e. GetKOTH
        """
        resp = api_request('status/koth', method='GET')
        message = resp['planets']
        print message

    def GetAlerts(self):
        """
        This fetches all currently active alerts.

        i.e. GetAlerts
        """
        resp = api_request('status/alerts', method='GET')
        message = resp['alerts']
        print message

    def CreateAlert(self, name, alert):
        """
        Issues an alert from Whiteteam. This will be displayed on Blue Team command center interfaces.

        name: Name of the alert. This is used for tracking so that when the alert is over it may be deactivated.

        i.e. CreateAlert WhiteTeamStore "White Team store offline for the next 15 minutes"
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['name'] = name
        post_data['message'] = alert
        resp = api_request('create/alert', data=post_data)
        message = resp['success']
        print message
        slackUpdate("@channel ALERT ({}): {}".format(name, alert))

    def ClearAlert(self, name):
        """
        Clears an alert from Whiteteam. This will no longer be displayed on Blue Team command center interfaces.
        
        name: Name of the alert.

        i.e. ClearAlert WhiteTeamStore
        """
        token = get_token()
        post_data = dict()
        post_data['token'] = token
        post_data['name'] = name
        resp = api_request('clear/alert', data=post_data)
        message = resp['success']
        print message
        slackUpdate("@channel Cleared alert: {}".format(name))




def main():
    # Configure readline
    if HAS_READLINE:
        if os.path.exists(HIST_FILE):
            readline.read_history_file(HIST_FILE)
        readline.parse_and_bind('tab: complete')
        readline.parse_and_bind('set editing-mode vi')

        # Build Auto Complete
        autocomplete = list(filter(lambda x: not x.startswith('_'), dir(Console)))
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
