import datetime
import os
import socket
import sys

import six
import yaml

sneakersync = sys.modules["sneakersync"]

from .state import State

def send(destination, progress, backend):
    """Send modules on the sneakernet."""
    
    state = State.load(os.path.join(destination, "sneakersync.dat"))
    if state.previous_direction == "send":
        confirmed = confirm(
            "WARNING: "
            "do you want to re-send the current files "
            "(sent from {} on {})?".format(
                state.previous_host, state.previous_date.strftime("%c")))
        if not confirmed:
            return 0
    
    configuration = read_configuration(
        os.path.join(destination, "sneakersync.cfg"))
    
    for module in configuration["modules"]:
        if sneakersync.logger.getEffectiveLevel() <= logging.WARNING:
            print("Sending {}".format(module["root"]))
        
        backend.send(destination, configuration, module, progress)
    
    state.previous_direction = "send"
    state.previous_date = datetime.datetime.now()
    state.previous_host = socket.gethostname()
    state.save()

def receive(source, progress, backend):
    """Receive modules from the sneakernet."""
    
    state = State.load(os.path.join(source, "sneakersync.dat"))
    if state.previous_direction == "receive":
        confirmed = confirm(
            "WARNING: "
            "do you want to receive the current files again "
            "(sent from {} on {})?".format(
                state.previous_host, state.previous_date.strftime("%c")))
        if not confirmed:
            return 0
        confirmed = confirm(
            "This will overwrite your data. Are you really sure?")
        if not confirmed:
            return 0
    
    configuration = read_configuration(os.path.join(source, "sneakersync.cfg"))
    
    for module in configuration["modules"]:
        if sneakersync.logger.getEffectiveLevel() <= logging.WARNING:
            print("Receiving {}".format(module["root"]))
        
        backend.send(destination, configuration, module, progress)
    
    state.previous_direction = "receive"
    state.save()

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
