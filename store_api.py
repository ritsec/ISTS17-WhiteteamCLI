from console import _api_request, _get_token
import config as _conf

_endpoints = ["get-balance", "buy", "transfer", "transactions", "items",
             "admin-get-balance", "admin-add-credits", "admin-set-credits",
             "admin-remove-credits"]

_server = _conf.get("STORE_API")

def GetMoney(team):
    """
    Gets the current money for a given team #.
    
    i.e. GetMoney 7
    """
    token = _get_token()
    post_data = dict()
    post_data['token'] = token
    post_data['team_id'] = team
    resp = _api_request('admin-get-balance', data=post_data)
    balance = resp['balance']
    print(balance)

def AddMoney(team, amount, reason):
    """
    Adds money to the given team # account. Please also specify a reason.

    i.e. AddMoney 7 50000 "Completed Challenge"
    """
    token = _get_token()
    post_data = dict()
    post_data['token'] = token
    post_data['team_id'] = team
    post_data['amount'] = amount
    resp = _api_request('admin-add-credits', data=post_data)
    message = resp['success']
    print(message)
    #slackUpdate("Added {} credits to team {} because: {}".format(amount, team, reason))

def RemoveMoney(team, amount, reason):
    """
    Removes money from the given team # account. Please also specify a reason.

    i.e. RemoveMoney 7 50000 "Purchased item at service desk"
    """
    token = _get_token()
    post_data = dict()
    post_data['token'] = token
    post_data['team_id'] = team
    post_data['amount'] = amount
    resp = _api_request('admin-remove-credits', data=post_data)
    message = resp['success']
    print(message)
    #slackUpdate("Removed {} credits from team {} because: {}".format(amount, team, reason))

def SetMoney(team, amount, reason):
    """
    Set the credits for the given team # account. Please also specify a reason.

    i.e. SetMoney 7 50000 "Setting up the competition"
    """
    token = _get_token()
    post_data = dict()
    post_data['token'] = token
    post_data['team_id'] = team
    post_data['amount'] = amount
    resp = _api_request('admin-set-credits', data=post_data)
    message = resp['success']
    print(message)
    #slackUpdate("Set team {} credits to {} because: {}".format(team, amount, reason))

def GetAllMoney():
    """
    Gets the money for all teams
    """
    team = 1
    token = _get_token()
    credz = dict()
    while team != 12:
        post_data = dict()
        post_data['token'] = token
        post_data['team_id'] = team
        resp = _api_request('admin-get-balance', data=post_data)
        balance = resp['balance']
        credz[team] = balance
        team += 1
    post_data = dict()
    post_data['token'] = token
    post_data['team_id'] = 99
    resp = _api_request('admin-get-balance', data=post_data)
    balance = resp['balance']
    credz[team] = balance

    team = 1
    for team in sorted(credz.keys()):
        if team == 12:
            print('team: ' + str(99) + ', balance: ' + str(credz[team]))
        else:
            print('team: ' + str(team) + ', balance: ' + str(credz[team]))

def __CreateTeam(team, name):
    """
    Add a new team
    TODO: Dont know where this came from

    """
    token = _get_token()
    post_data = dict()
    post_data['teamNum'] = team
    post_data['name'] = name
    resp = _api_request('createteam', data=post_data, token=token)
    message = resp['message']
    print(message)
