import json
import os
import shutil
import subprocess
import sys

sneakersync = sys.modules["sneakersync"]

def send(destination, configuration, module, progress):
    repository = os.path.join(destination, "repository")
    
    has_sneakersync = True
    initialize = False
    if not os.path.isdir(destination):
        has_sneakersync = False
        initialize = True
    elif not os.path.isdir(repository):
        has_sneakersync = True
        initialize = True
    
    if initialize:
        subprocess.check_call(["borg", "init", "-e", "none", repository])
    
    try:
        info = json.loads(
            subprocess.check_output(["borg", "list", "--json", repository]))
    except subprocess.CalledProcessError as e:
        raise sneakersync.Exception(
            "Could not get repository information: {}".format(e))
    
    has_sneakersync = "sneakersync" in [x["name"] for x in info["archives"]]
    
    if has_sneakersync:
        subprocess.call([
            "borg", "rename", "{}::sneakersync".format(repository), 
            "sneakersync.old"])
    
    subprocess.call(
        ["borg", "create", "--verbose", "--filter", "AME", "--list", "--stats", "--show-rc", "-x", "-C", "none"]
        + get_filters(module["filters"])
        + ["{}::sneakersync".format(repository), module["root"]])
    
    if has_sneakersync:
        subprocess.call([
            "borg", "delete", "{}::sneakersync.old".format(repository)])

def get_filters(filters):
    options = [
        "--pattern={}{}".format(
            "+" if list(f.keys())[0] == "include" else "-", list(f.values())[0])
        for f in filters
    ]
    
    return options
