#from cli import api_request, get_token
import config as _conf

_endpoints = [
              "validate-session",
              "login",
              "update-password",
              "expire-session",
              "update-session"
             ]

_server = _conf.get("AUTH_API")

