#!/usr/bin/env python

import argparse
import datetime
import os
import socket
import subprocess
import sys

import yaml

def main():
    parser = argparse.ArgumentParser(
        description="Send and receive files through the sneakernet")
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

def send(destination):
    sync_data = read_sync_data(os.path.join(destination, "sneakersync.dat"))
    if sync_data["previous_direction"] == "send":
        confirmed = confirm(
            "WARNING: "
            "do you want to re-send the current files "
            "(sent from {} on {})?".format(
                sync_data["previous_host"], 
                sync_data["previous_date"].strftime("%c")))
        if not confirmed:
            return 0
    
    configuration = read_configuration(
        os.path.join(destination, "sneakersync.cfg"))
    
    for module in configuration["modules"]:
        # WARNING: make sure there is no "/" at the end of the module
        module["root"] = module["root"].rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", "--relative",
            "--progress", "--stats"
        ]
        command += get_filters(configuration["filters"])
        command += get_filters(module["filters"])
        command += [
            os.path.join("/." + module["root"], ""), 
            os.path.join(destination, "")
        ]
        subprocess.check_call(command)
    
    sync_data["previous_direction"] = "send"
    sync_data["previous_date"] = datetime.datetime.now()
    sync_data["previous_host"] = socket.gethostname()
    write_sync_data(sync_data, os.path.join(destination, "sneakersync.dat"))

def receive(source):
    sync_data = read_sync_data(os.path.join(source, "sneakersync.dat"))
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
    
    configuration = read_configuration(os.path.join(source, "sneakersync.cfg"))
    
    for module in configuration["modules"]:
        # WARNING: make sure there is no "/" at the end of the module
        module["root"] = module["root"].rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", 
            "--progress", "--stats"
        ]
        command += get_filters(configuration["filters"])
        command += get_filters(module["filters"])
        command += [
            os.path.join(source, module["root"].lstrip("/"), ""),
            os.path.join(module["root"], "")
        ]
        subprocess.check_call(command)
        
    sync_data["previous_direction"] = "receive"
    write_sync_data(sync_data, os.path.join(source, "sneakersync.dat"))

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

def get_filters(filters):
    arguments = []
    for filter_ in filters:
        if len(filter_) > 1:
            raise Exception(
                "Filter must contain only one entry: {}".format(filter_))
        if "exclude" in filter_:
            arguments += ["--exclude", filter_["exclude"]]
        elif "include" in filter_:
            arguments += ["--include", filter_["include"]]
        else:
            raise Exception(
                "Filter must contain include or exclude: {}".format(filter_))
    return arguments

def write_sync_data(sync_data, path):
    with open(path, "w") as fd:
        yaml.dump(sync_data, fd)    

if __name__ == "__main__":
    sys.exit(main())
