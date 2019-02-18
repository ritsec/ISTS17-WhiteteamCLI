import yaml

# open the config file
with open("config.yml") as fil:
    _conf = yaml.load(fil)


get = _conf.get

__getitem__ = _conf.__getitem__
