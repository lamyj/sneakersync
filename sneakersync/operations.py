import datetime
import logging
import pathlib
import socket
import sys

import yaml

sneakersync = sys.modules["sneakersync"]

from .state import State

def send(destination, progress, backend):
    """Send modules on the sneakernet."""
    
    state = State.load(destination / "sneakersync.dat")
    if state.previous_direction == "send":
        confirmed = confirm(
            "WARNING: "
            "do you want to re-send the current files "
            "(sent from {} on {})?".format(
                state.previous_host, state.previous_date.strftime("%c")))
        if not confirmed:
            return 0
    
    configuration = read_configuration(destination / "sneakersync.cfg")
    
    for module in configuration["modules"]:
        if sneakersync.logger.getEffectiveLevel() <= logging.WARNING:
            print("Sending {}".format(sneakersync.get_module_root(module)))
        
        backend.send(destination, configuration, module, state, progress)
    
    state.previous_direction = "send"
    state.previous_date = datetime.datetime.now()
    state.previous_host = socket.gethostname()
    state.save()

def receive(source, progress, backend):
    """Receive modules from the sneakernet."""
    
    state = State.load(source / "sneakersync.dat")
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
    
    configuration = read_configuration(source / "sneakersync.cfg")
    
    for module in configuration["modules"]:
        if sneakersync.logger.getEffectiveLevel() <= logging.WARNING:
            print("Receiving {}".format(sneakersync.get_module_root(module)))
        
        backend.receive(source, configuration, module, state, progress)
    
    state.previous_direction = "receive"
    state.save()

def read_configuration(path):
    configuration = {
        "modules": [],
        "filters": []
    }
    
    if path.is_file():
        with open(path) as fd:
            data = yaml.load(fd, Loader=yaml.BaseLoader)
            if data:
                configuration.update(data)
    
    for module in configuration["modules"]:
        if isinstance(module["root"], str):
            module["root"] = {socket.gethostname(): module["root"]}
        for host, path in module["root"].items():
            path = pathlib.Path(path)
            if not path.is_absolute():
                raise Exception(
                    "Module path \"{}\" is not absolute".format(module["root"]))
            module["root"][host] = path
        module["root"] = {h: pathlib.Path(p) for h, p in module["root"].items()}
        
        module.setdefault("filters", [])
    
    return configuration

def confirm(message):
    user_input = ""
    while user_input.lower() not in ["y", "n"]: 
        user_input = input("{} [yn] ".format(message))
    return (user_input == "y")
