import logging
import os
import subprocess
import sys

sneakersync = sys.modules["sneakersync"]

from .state import State

def send(destination, progress):
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
        
        if not os.path.isdir(module["root"]):
            logger.warn("No such file or directory: {}".format(module["root"]))
            continue
            
        # WARNING: make sure there is no "/" at the end of the module
        module["root"] = module["root"].rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", "--relative", "--fake-super"
        ]
        command.extend(get_verbosity_options(progress))
        
        command += get_filters(configuration["filters"])
        command += get_filters(module["filters"])
        command += [
            os.path.join("/." + module["root"], ""), 
            os.path.join(destination, "")
        ]
        
        call_subprocess(command, "send", module)
    
    state.previous_direction = "send"
    state.previous_date = datetime.datetime.now()
    state.previous_host = socket.gethostname()
    state.save()

def receive(source, progress):
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
        
        # WARNING: make sure there is no "/" at the end of the module
        module["root"] = module["root"].rstrip("/")
        
        command = [
            "rsync",
            "--archive", "--xattrs", "--delete", "--fake-super"
        ]
        command.extend(get_verbosity_options(progress))
        
        command += get_filters(configuration["filters"])
        command += get_filters(module["filters"])
        command += [
            os.path.join(source, module["root"].lstrip("/"), ""),
            os.path.join(module["root"], "")
        ]
        
        call_subprocess(command, "receive", module)
        
    state.previous_direction = "receive"
    state.save()

def get_filters(filters):
    """Return the rsync options for the given filters."""
    
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

def get_verbosity_options(progress):
    options = []
    if progress:
        options.append("--progress")
    if sneakersync.logger.getEffectiveLevel() <= logging.INFO:
        options.append("--stats")
    if sneakersync.logger.getEffectiveLevel() <= logging.DEBUG:
        options.extend(["--verbose", "--verbose"])
    return options

def call_subprocess(command, action, module):
    """Call a command, redirect output given current logging level."""
    
    output = []
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in iter(process.stdout.readline, b""):
        output.append(line)
        encoding = (
            getattr(sys.stdout, "encoding", None)
            or getattr(sys.stdin, "encoding", None)
            or "utf-8"
        )
        sys.stdout.write(line.decode(encoding))
    
    process.wait()
    process.stdout.close()
    if process.returncode != 0:
        raise sneakersync.Exception(action, module, b"".join(output))
