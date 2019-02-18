import requests
import config as _conf

# We dont register these endpoints because we use our own _request function
_endpoints = []

_server = _conf.get("VOTE_API")

_creds = _conf.get("VOTE_API_CREDS")

def _request(endpoint, data=None, method='GET'):
    url = "{}/{}".format(_server, endpoint)
    auth = (_creds['username'], _creds['password'])
    if method == 'GET':
        resp = requests.get(url, auth=auth)
    elif method == 'POST':
        resp = requests.post(url, json=data, auth=auth)
    else:
        raise Exception("Unknown method '{}'".format(method))

    if not resp or resp.status_code != 200:
        raise Exception("API returned {} for /{}".format(resp.status_code, endpoint))
    
    return resp.json()

def GetVotingTally():
    """
    Gets the current tally of votes for all the teams
    
    i.e. GetTally
    """
    resp = _request('tally')
    for team, tally in resp.get("message", {}).items():
        print("\t{}: {}".format(team, tally))


def EndVotingRound(confirm):
    """
    Ends the voting round for all the teams
    
    i.e. EndVotingRound True
    """
    if not confirm:
        print("You must confirm to end the round")
        return
    resp = _request('admin/end_round')
    print("Ended the voting round. Here are the tallies")
    for team, tally in resp.get("message", {}).items():
        print("\t{}: {}".format(team, tally))


def GetVotingTokens(team):
    """
    Gets the voting tokens for a team

    i.e. GetVoteTokens 0
    """
    resp = _request('admin/get_tokens', method="POST", data={"team": "team{}".format(team)})
    for server, token in resp.get("message", {}).items():
        print("\t{}: {}".format(server, token))

def SetVotingTokens(team, stalin=None, castro=None):
    """
    Sets the voting tokens for a team

    i.e. SetVoteTokens 0
    """
    if not stalin and not castro:
        print("Must specify atleast one voting token")
        return
    data={"team": "team{}".format(team), "tokens": {}}
    if castro:
        data['tokens']['castro'] = castro
    if stalin:
        data['tokens']['stalin'] = stalin

    resp = _request('admin/set_token', method="POST", data=data)
    print(resp.get("message", "Error"))


def SetVotingTally(team, tally):
    """
    Sets the voting tally for a team

    i.e. SetVotingTally 3 500
    """
    data={"team": "team{}".format(team), "tally": tally}
    resp = _request('admin/set_tally', method="POST", data=data)
    print(resp.get("message", "Error"))

