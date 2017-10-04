#!/usr/bin/env python

import argparse
import datetime
import os
import socket
import subprocess
import sys

here = os.path.abspath(os.path.dirname(sys.argv[0]))
if sys.version_info.major == 2:
    sys.path.insert(0, "lib")
elif sys.version_info.major == 3:
    sys.path.insert(0, "lib3")
else:
    raise NotImplementedError("Unknown Python version: {}".format(sys.version))

import yaml

remote = "/Volumes/Sneakernet"

def main():
    parser = argparse.ArgumentParser(
        description="Send and receive files through the sneakernet")
    parser.add_argument(
        "--configuration_path",default=os.path.join(here, "sneakernet.cfg"))
    parser.add_argument(
        "--sync-data-path",default=os.path.join(here, "sneakernet.dat"))
    subparsers = parser.add_subparsers(help="Sub-commands help")
    
    send_parser = subparsers.add_parser(
        "send", help="Send data on the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    send_parser.add_argument("destination")
    send_parser.set_defaults(function=send)
    
    receive_parser = subparsers.add_parser(
        "receive", help="Receive data from the sneakernet",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    receive_parser.add_argument("source")
    receive_parser.set_defaults(function=receive)
    
    arguments = vars(parser.parse_args())
    function = arguments.pop("function")
    function(**arguments)
    
    return 0

def send(destination, configuration_path, sync_data_path):
    sync_data = read_sync_data(sync_data_path)
    if sync_data["previous_direction"] == "send":
        confirmed = confirm(
            "WARNING: "
            "do you want to re-send the current files "
            "(sent from {} on {})?".format(
                sync_data["previous_host"], 
                sync_data["previous_date"].strftime("%c")))
        if not confirmed:
            return 0
        
    configuration = read_configuration(configuration_path)
    
    for module in configuration["modules"]:
        # WARNING: make sure there is no "/" at the end of the module
        module = module.rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", "--progress", "--stats",
            os.path.join(module, ""), 
            os.path.join(destination, module.lstrip("/"), "")
        ]
        print " ".join(command)
    
    sync_data["previous_direction"] = "send"
    sync_data["previous_date"] = datetime.datetime.now()
    sync_data["previous_host"] = socket.gethostname()
    write_sync_data(sync_data, sync_data_path)

def receive(source, configuration_path, sync_data_path):
    sync_data = read_sync_data(sync_data_path)
    if sync_data["previous_direction"] == "receive":
        confirmed = confirm(
            "WARNING: "
            "do you want to receive the current files again "
            "(sent from {} on {})?".format(
                sync_data["previous_host"], 
                sync_data["previous_date"].strftime("%c")))
        if not confirmed:
            return 0
        confirmed = confirm(
            "This will overwrite your data. Are you really sure?")
        if not confirmed:
            return 0
    
    configuration = read_configuration(configuration_path)
    
    for module in configuration["modules"]:
        # WARNING: make sure there is no "/" at the end of the module
        module = module.rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", "--progress", "--stats",
            os.path.join(source, module.lstrip("/"), ""),
            os.path.join(module, "")
        ]
        print " ".join(command)
        
    sync_data["previous_direction"] = "receive"
    write_sync_data(sync_data, sync_data_path)

def read_configuration(path):
    configuration = {
        "modules": []
    }
    
    if os.path.isfile(path):
        with open(path) as fd:
            data = yaml.load(fd)
            if data:
                configuration.update(data)
    
    for module in configuration["modules"]:
        if not module.startswith("/"):
            raise Exception("Module path \"{}\" is not absolute".format(module))
    
    return configuration

def read_sync_data(path):
    sync_data = {
        "previous_direction": None,
        "previous_date": None,
        "previous_host": None,
    }
    
    if os.path.isfile(path):
        with open(path) as fd:
            data = yaml.load(fd)
            if data:
                sync_data.update(data)
    
    return sync_data

def confirm(message):
    user_input = ""
    while user_input.lower() not in ["y", "n"]: 
        user_input = raw_input("{} [yn] ".format(message))
    return (user_input == "y")

def write_sync_data(sync_data, path):
    with open(path, "w") as fd:
        yaml.dump(sync_data, fd)    

if __name__ == "__main__":
    sys.exit(main())
