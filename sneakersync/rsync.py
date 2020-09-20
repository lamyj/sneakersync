import logging
import socket
import subprocess
import sys

sneakersync = sys.modules["sneakersync"]

def send(destination, configuration, module, state, progress=False):
    source = sneakersync.get_module_root(module)
    if not source.is_dir():
        raise Exception("No such directory: {}".format(source))
        
    command = [
        "rsync",
        "--archive", "--acls", "--hard-links", "--xattrs",
        "--delete", "--relative"
    ]
    if sys.platform == "darwin":
        command.extend(["--crtimes", "--fileflags"])
    command.extend(get_verbosity_options(progress))
    
    command += get_filters(configuration["filters"])
    command += get_filters(module["filters"])
    command += ["/.{}/".format(source), "{}/".format(destination)]
    
    call_subprocess(command, "send", module)

def receive(source, configuration, module, state, progress=False):
    command = [
        "rsync",
        "--archive", "--acls", "--hard-links", "--xattrs",
        "--delete"
    ]
    if sys.platform == "darwin":
        command.extend(["--crtimes", "--fileflags"])
    command.extend(get_verbosity_options(progress))
    
    command += get_filters(configuration["filters"])
    command += get_filters(module["filters"])
    command += [
        "{}{}/".format(
            source, sneakersync.get_module_root(module, state.previous_host)), 
        "{}/".format(sneakersync.get_module_root(module))]
    
    call_subprocess(command, "receive", module)

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
        options.append("--info=name")
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
