import datetime
import logging
import os
import socket
import sys

import six
import yaml

from .exception import SneakersyncException
import sys
sys.modules["sneakersync"].Exception = SneakersyncException

logger = logging.getLogger(__name__)

import rsync

def read_configuration(path):
    configuration = {
        "modules": [],
        "filters": []
    }
    
    if os.path.isfile(path):
        with open(path) as fd:
            data = yaml.load(fd)
            if data:
                configuration.update(data)
    
    for module in configuration["modules"]:
        if not module["root"].startswith("/"):
            raise Exception(
                "Module path \"{}\" is not absolute".format(module["root"]))
        module.setdefault("filters", [])
    
    return configuration

def confirm(message):
    user_input = ""
    while user_input.lower() not in ["y", "n"]: 
        user_input = six.moves.input("{} [yn] ".format(message))
    return (user_input == "y")
